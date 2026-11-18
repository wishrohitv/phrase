import json
import time
import uuid
from collections.abc import AsyncIterable, Iterable
from logging import getLogger

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.sse import EventSourceResponse
from redis_fastapi import CacheBackendDep, cache
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
    ChatMessageSchema,
    ChatStreamingResponseSchema,
    UserChatsResponseSchema,
)

chats = APIRouter(prefix="/chat", tags=["Chats"])

logger = getLogger(__name__)


@chats.get(
    "",
    dependencies=[Depends(cache(ttl=60 * 60 * 24 * 3, eviction_group="user_chats"))],
    response_model=SuccessSchema[PaginatedSchema[UserChatsResponseSchema]],
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
    message_data: ChatMessageSchema,
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Create new chat session, generate chat uid

    Args:
        - message_data (ChatMessageSchema):
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


@chats.get(
    "/{uid}/message",
    dependencies=[Depends(cache(ttl=60 * 60 * 24 * 3, eviction_group="chat_message"))],
    response_model=SuccessSchema[PaginatedSchema[ChatMessageResponseSchema]],
    status_code=200,
)
async def get_chat_message(
    uid: uuid.UUID,
    after_uid: int | None = Query(None, description="Last chat ID"),
    after_date: float | None = Query(None, description="Last created_at"),
    limit: int = Query(10, ge=1, le=50),
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Get all chat messages in descending order

    Args:
        - uid (uuid): Take chat uid from path params
        - after_uid (int): Message id from query params
        - after_date (int): Unix Timestamp from query params
        - limit (int): Limit range between (1 to 50) from query params
    Returns:
        - SuccessSchema[PaginatedSchema[list[ChatMessageResponseSchema]]: Paginated model
    """
    query = (
        db.query(Messages)
        .filter_by(chat_uid=uid)
        .order_by(Messages.created_at.desc(), Messages.id.desc())
    )

    # Aply the keyset filter
    if after_uid is not None and after_date is not None:
        query = query.filter(
            or_(
                Messages.created_at < datetime_from_unix(after_date),
                and_(
                    Messages.created_at == datetime_from_unix(after_date),
                    Messages.id < after_uid,
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

    return SuccessSchema(data=response)


@chats.post(
    "/{uid}/message",
    response_class=EventSourceResponse,
    response_model=None,
)
async def chat(
    uid: uuid.UUID,
    message_data: ChatMessageSchema,  # Expect body contain entire history of chat along with latest prompt
    redis: CacheBackendDep,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),  # noqa: B008
    user: Users = Depends(auth_middleware),  # noqa: B008
    subscription: Subscription = Depends(subscription_middleware),  # noqa: B008
    featrue_usage=Depends(chat_usage_middleware),  # noqa: B008
) -> AsyncIterable[ChatStreamingResponseSchema]:
    """
    Agent Chat streaming enpoints
    Args:
        - uid (uuid): Chat uid from path params
        - message_data (UserChatsResponseSchema): Body object from body
    Returns:
        - AsyncIterable[ChatStreamingResponseSchema]: Streamable object
    """
    FEATURE_ID = 2  # FOR CHAT USAGE
    # Redis key for
    REDIS_MESSAGE_KEY = (
        f"mes_history:chat_uid:{uid}:message_uid:{message_data.message_uid}"
    )
    REDIS_MESSAGE_KEY_EXP = 60 * 60 * 12  # 12 hour

    # Redis indempotency check : return message if already exists
    stored_message = await redis.get(REDIS_MESSAGE_KEY)

    if stored_message:
        yield ChatStreamingResponseSchema(
            message_uid=message_data.message_uid,
            content=stored_message,
            status="cached",
        )
        return
    # Check if db for existing assistans's response for given message_uid
    db_message = (
        db.query(Messages)
        .filter_by(
            chat_uid=uid,
            message_uid=message_data.message_uid,
            role=ChatRoleType.ASSISTANT,
        )
        .first()
    )

    if db_message:
        # set message in cache
        await redis.set(
            REDIS_MESSAGE_KEY, db_message.content, ttl=REDIS_MESSAGE_KEY_EXP
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
        message_uid=message_data.message_uid,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # Store user message's embbeding
    background_tasks.add_task(
        store_chat_embeddings, new_message.id, new_message.content
    )

    # Build conversation chat history from db or cache
    REDIS_CHAT_HISTORY_KEY: str = f"chat_history:chat_uid:{uid}"
    REDIS_CHAT_HISTORY_KEY_EXP: int = 60 * 60 * 12  # 12 hour
    MESSAGE_WINDOW_LENGTH: int = 40
    stored_chat_history: list[dict] = (
        await redis.get(REDIS_CHAT_HISTORY_KEY, default=[]) or []
    )

    # If cached history is empty
    # fetch from db and store in cache
    if not stored_chat_history:
        chat_history = (
            db.query(Messages.content, Messages.role)
            .filter_by(chat_uid=uid)
            .order_by(Messages.created_at.desc())
            .limit(MESSAGE_WINDOW_LENGTH)
            .all()
        )

        if chat_history:
            _chat_history: list = []
            for message in chat_history:
                _chat_history.append({"role": message.role, "content": message.content})
            _chat_history.reverse()
            # Set chat history in cachedb
            await redis.set(
                REDIS_CHAT_HISTORY_KEY, _chat_history, ttl=REDIS_CHAT_HISTORY_KEY_EXP
            )
            stored_chat_history.extend(_chat_history)
    else:
        # Append user's latest message to history
        stored_chat_history.append(
            {"role": ChatRoleType.USER.value, "content": message_data.content}
        )
    # Limit message history to 40 message
    if len(stored_chat_history) > MESSAGE_WINDOW_LENGTH:
        stored_chat_history = stored_chat_history[-MESSAGE_WINDOW_LENGTH:]

    # Initialize time to calcluate llm response duration
    initial_time = time.time()
    # Call agent and send message history with latest message
    event = chat_agent(json.dumps(stored_chat_history))

    full_response = ""
    time_taken: float | None = None
    last_stream = None
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
            message_uid=message_data.message_uid,
        )
        db.add(agent_res)
        db.commit()

        # Cache agent message with message_uid
        await redis.set(REDIS_MESSAGE_KEY, full_response, ttl=REDIS_MESSAGE_KEY_EXP)
        # Append agent message in history and cache message_history
        stored_chat_history.append(
            {"role": ChatRoleType.ASSISTANT, "content": full_response}
        )
        await redis.set(
            REDIS_CHAT_HISTORY_KEY,
            stored_chat_history,
            ttl=REDIS_CHAT_HISTORY_KEY_EXP,
        )
        logger.info(last_stream.dict())
        # Store feature_usage
        background_tasks.add_task(
            track_feature_usage, user_id=user.id, feature_id=FEATURE_ID
        )

        # Store llm usage
        background_tasks.add_task(
            track_llm_usage,
            subscription_id=subscription.id,
            message_uid=message_data.message_uid,
            user_id=user.id,
            feature_id=FEATURE_ID,
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
        logger.info("LLM streaming completed")
        logger.info("Assistant response saved")
        logger.info("Redis cache updated")
        logger.info("Background tasks registered")
        yield ChatStreamingResponseSchema(
            message_uid=message_data.message_uid, content="", status="success"
        )

    except Exception:
        logger.exception("Error while message generation")

        yield ChatStreamingResponseSchema(
            message_uid=message_data.message_uid,
            content="Sorry, I encountered an error processing your request.",
            status="error",
        )
