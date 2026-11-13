import json
import time
import uuid
from collections.abc import AsyncIterable, Iterable
from logging import getLogger

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.sse import EventSourceResponse
from redis_fastapi import CacheBackendDep
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_, or_

from database import get_db
from middlewares import auth_middleware, chat_usage_middleware, subscription_middleware
from models import ChatRoleType, Chats, Messages, Users
from models.service import Subscription
from services.chat_service import chat_agent
from tasks.chat_embbeding import store_chat_embeddings
from tasks.usage_track import track_feature_usage, track_llm_usage
from utils.datetime_utc import datetime_from_unix, datetime_to_unix
from utils.errors import BadRequestException
from utils.success import PaginatedSchema, SuccessSchema

from .pydantic_schema import (
    ChatMessageResponseSchema,
    ChatStreamingResponseSchema,
    UserChatsResponseSchema,
)

chats = APIRouter(prefix="/chat")

logger = getLogger(__name__)


@chats.get(
    "",
    response_model=SuccessSchema[PaginatedSchema[list[UserChatsResponseSchema]]],
    status_code=200,
)
async def user_chats(
    after_uid: uuid.UUID | None = Query(None, description="Last chat UID"),
    after_date: float | None = Query(None, description="Last created_at"),
    limit: int = Query(20, ge=1, le=50),
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    List all chats

    Args:
        - after_uid (uuid | None): Last chat uid to start from
        - after_date (flaot | None): Last chat created_at to start from
        - limit (int, def=20 1><50): Number of chats to fetch
    Returns:
        - SuccessSchema[PaginatedSchema[list[UserChatsResponseSchema]]]: List of chats
    """

    query = (
        db.query(Chats)
        .filter_by(owner_id=user.id)
        .order_by(Chats.updated_at.desc(), Chats.uid.desc())
    )
    # Apply keyset filter
    if after_uid is not None and after_date is not None:
        query = query.filter(
            or_(
                Chats.updated_at < datetime_from_unix(after_date),
                and_(
                    Chats.updated_at == datetime_from_unix(after_date),
                    Chats.uid < after_uid,
                ),
            )
        )
    items = query.limit(limit + 1).all()

    has_more = len(items) > limit

    if has_more:
        items = items[:limit]

    chats = [UserChatsResponseSchema.model_validate(chat) for chat in items]

    response = PaginatedSchema(items=chats, has_more=has_more)

    if items:
        last_item = items[-1]
        response.after_uid = last_item.uid
        response.after_date = datetime_to_unix(last_item.updated_at)

    return SuccessSchema(data=response)


@chats.post("")
async def create_chat_session(
    message_data: UserChatsResponseSchema,
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Create new chat session, generate chat uid

    Args:
        - message_data (UserChatsResponseSchema):
    Returns:
        - Redirect to /api/chat/{uid}/message:
    """
    title = message_data.content.strip()
    if title == "":
        raise BadRequestException("Message cannot be empty")
    title = title if len(title) < 70 else title[:70]
    new_chat = Chats(
        title=title,
        owner_id=user.id,
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return RedirectResponse(f"/api/chat/{new_chat.uid}/message")


@chats.delete("/{uid}")
async def delete_chat_session(
    uid: uuid.UUID,
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Delete user's chats along with messages

    Args:
        - uid (uuid): Chat uid
    Returns:
        - SuccessSchema: Deletion status
    Raises:
        - BadRequestException: If chat not found
    """
    chat = (
        db.query(Chats)
        .where(
            and_(
                Chats.uid == uid,
                Chats.owner_id == user.id,
            )
        )
        .first()
    )
    if not chat:
        raise BadRequestException("Chat not found")
    db.delete(chat)
    db.commit()
    return SuccessSchema("Chat deleted successfully")


@chats.get("/{uid}/message")
async def get_chat_message(
    uid: uuid.UUID,
    after_id: int | None = Query(None, description="Last chat ID"),
    after_date: float | None = Query(None, description="Last created_at"),
    limit: int = Query(10, ge=1, le=50),
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Get all chats message from the end using
    """
    query = (
        db.query(Messages)
        .filter_by(chat_uid=uid)
        .order_by(Messages.created_at.desc(), Messages.id.desc())
    )

    # Aply the keyset filter
    if after_id is not None and after_date is not None:
        query = query.filter(
            or_(
                Messages.created_at < datetime_from_unix(after_date),
                and_(
                    Messages.created_at == datetime_from_unix(after_date),
                    Messages.id < after_id,
                ),
            )
        )

    items = query.limit(limit + 1).all()

    has_more = len(items) > limit

    if has_more:
        items = items[:limit]

    chats = [ChatMessageResponseSchema.model_validate(chat) for chat in items]
    response = PaginatedSchema(items=chats, has_more=has_more)

    if items:
        last_item = items[-1]
        response.after_uid = last_item.id
        response.after_date = datetime_to_unix(last_item.created_at)
    return response


@chats.post(
    "/{uid}/message",
    response_class=EventSourceResponse,
    response_model=None,
)
async def chat(
    uid: uuid.UUID,
    message_data: UserChatsResponseSchema,  # Expect body contain entire history of chat along with latest prompt
    redis: CacheBackendDep,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),  # noqa: B008
    user: Users = Depends(auth_middleware),  # noqa: B008
    subscription: Subscription = Depends(subscription_middleware),  # noqa: B008
    featrue_usage=Depends(chat_usage_middleware),  # noqa: B008
) -> AsyncIterable[ChatStreamingResponseSchema]:

    redis_message_key = (
        f"mes_history:chat_uid:{uid}:message_uid:{message_data.message_uid}"
    )
    redis_message_key_exp = 60 * 60 * 12  # 12 hour

    # Redis indempotency check : return message if already exists
    stored_message = await redis.get(redis_message_key)

    if stored_message:
        yield ChatStreamingResponseSchema(
            message_uid=message_data.message_uid,
            content=stored_message,
            status="cached",
        )
        return
    # Check if db for existing message
    db_message = (
        db.query(Messages)
        .filter_by(
            chat_uid=uid,
            message_uid=message_data.message_uid,
        )
        .first()
    )

    if db_message:
        # set message in cache
        await redis.set(
            redis_message_key, db_message.content, ttl=redis_message_key_exp
        )

        yield ChatStreamingResponseSchema(
            message_uid=message_data.message_uid,
            content=db_message.content,
            status="cached",
        )
        return

    # Store user message in db
    new_message = Messages(
        chat_uid=uid,
        content=message_data.content,
        user_id=user.id,
        message_uid=message_data,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # Store user message's embbeding
    background_tasks.add_task(
        store_chat_embeddings, new_message.id, new_message.content
    )

    # Build conversation chat history from db or cache
    redis_chat_history_key: str = f"chat_history:chat_uid:{uid}"
    redis_chat_history_key_exp: int = 60 * 60 * 12  # 12 hour
    message_window_length: int = 40
    stored_chat_history: list[dict] = (
        await redis.get(redis_chat_history_key, default=[]) or []
    )

    # If cached history is empty
    # fetch from db and store in cache
    if not stored_chat_history:
        chat_history = (
            db.query(Messages.content, Messages.role)
            .filter_by(chat_uid=uid)
            .order_by(Messages.created_at.desc())
            .limit(message_window_length)
            .all()
        )

        if chat_history:
            _chat_history: list = []
            for message in chat_history:
                _chat_history.append({"role": message.role, "content": message.content})
            _chat_history.reverse()
            # Set chat history in cachedb
            await redis.set(
                redis_chat_history_key, _chat_history, ttl=redis_chat_history_key_exp
            )
            stored_chat_history.extend(_chat_history)

    # Append latest message to history
    stored_chat_history.append(
        {"role": ChatRoleType.USER.value, "content": message_data.content}
    )
    # Limit message history to 40 message
    if len(stored_chat_history) > message_window_length:
        stored_chat_history = stored_chat_history[-message_window_length:]

    # Initialize time to calcluate llm response duration
    initial_time = time.time()
    # Call agent and send message history with latest message
    event = chat_agent(json.dumps(stored_chat_history))

    full_response = ""
    time_taken: float | None = None
    last_stream = None
    assistent_uid: uuid.UUID = str(uuid.uuid4())
    try:
        async for chunk in event:
            if hasattr(chunk, "usage") and chunk.usage:
                end_time = time.time()
                last_stream = chunk
                time_taken = end_time - initial_time
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
            yield ChatStreamingResponseSchema(
                message_uid=message_data.message_uid,
                content=content,
                status="loading",
            )

        # store agent response to DB
        agent_res = Messages(
            chat_uid=uid,
            content=full_response,
            role="assistant",
            message_uid=assistent_uid,
        )
        db.add(agent_res)
        db.commit()

        # TODO: look into this way
        # Cache agent message and append in history
        await redis.set(redis_message_key, full_response, ttl=redis_message_key_exp)
        stored_chat_history.append(
            {"role": ChatRoleType.ASSISTANT, "content": full_response}
        )
        await redis.set(
            redis_chat_history_key,
            stored_chat_history,
            ttl=redis_chat_history_key_exp,
        )
        print(last_stream.dict())
        # Store feature_usage
        background_tasks.add_task(track_feature_usage, user_id=user.id, feature_id=2)

        # Store llm usage
        background_tasks.add_task(
            track_llm_usage,
            subscription_id=subscription.id,
            message_uid=assistent_uid,
            user_id=user.id,
            feature_id=2,
            provider="openrouter",
            model=last_stream.model,
            prompt_tokens=last_stream.usage.prompt_tokens,
            completion_tokens=last_stream.usage.completion_tokens,
            completion_tokens_details=last_stream.usage.completion_tokens_details.dict(),
            total_tokens=last_stream.usage.total_tokens,
            cost=last_stream.usage.cost,
            cost_details=last_stream.usage.cost_details.dict(),
            prompt_tokens_details=last_stream.usage.prompt_tokens_details.dict(),
            request_id=last_stream.id,
            time_taken=round(time_taken, 2),
        )
        yield ChatStreamingResponseSchema(
            message_uid=message_data.message_uid, status="success"
        )

    except Exception:
        logger.exception("Error while message generation")

        yield UserChatsResponseSchema(
            message_uid=message_data.message_uid,
            content="Sorry, I encountered an error processing your request.",
            status="error",
        )
