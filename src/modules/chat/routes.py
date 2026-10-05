import json
import uuid
from logging import getLogger

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from redis_fastapi import CacheBackendDep
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_

from database import get_db
from middlewares.auth_middleware import auth_middleware
from models import ChatRoleType, Chats, Messages, Users
from services.chat_service import chat_agent
from tasks.chats import store_chat_embeddings
from utils.errors import BadRequestException
from utils.success import Success

from .pydantic_schema import ChatMessageSchema, NewChatSchema

chats = APIRouter(prefix="/chats")

logger = getLogger(__name__)


@chats.get("")
async def get_user_chats(
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    List all chats and return title , id ,last created
    """
    chats = (
        db.query(Chats.uid, Chats.title, Chats.updated_at)
        .filter_by(owner_id=user.id)
        .order_by(
            Chats.updated_at.desc(),
        )
        .limit(10)
    ).all()

    return [
        {
            "uid": str(chat.uid),
            "title": chat.title,
            "updated_at": chat.updated_at,
        }
        for chat in chats
    ]


@chats.post("")
async def create_chat_session(
    new_chat_data: NewChatSchema,
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Create new chat session, generate chat uid
    """
    new_chat = Chats(
        title=new_chat_data.title,
        owner_id=user.id,
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return Success({"uid": str(new_chat.uid)}, status_code=201)


@chats.delete("/{uid}")
async def delete_chat_session(
    uid: uuid.UUID,
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
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
    return Success("Chat deleted successfully")


@chats.get("/{uid/messages}")
async def get_chat_message(
    uid: uuid.UUID,
    last_id=0,
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Get all chats message from the end using
    """
    chats = (
        db.query(Messages)
        .filter_by(chat_uid=uid)
        .order_by(
            Messages.created_at.desc(),
        )
        .limit(10)
    ).all()
    if not chats:
        raise BadRequestException("Chat not found")
    return chats


@chats.post("/{uid}/messages")
async def chat(
    uid: uuid.UUID,
    message_data: ChatMessageSchema,  # Expect body contain entire history of chat along with latest prompt
    redis: CacheBackendDep,
    background_tasks: BackgroundTasks,
    user: Users = Depends(auth_middleware),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):

    redis_message_key = (
        f"mes_history:chat_uid:{uid}:message_uid:{message_data.message_uid}"
    )
    redis_message_key_exp = 60 * 60 * 12  # 12 hour

    # Redis indempotency check : return message if already exists
    stored_message = await redis.get(redis_message_key)

    if stored_message:

        async def cached_stream():
            yield f"data: {json.dumps({'chunk': stored_message, 'status': 'cached'})}\n\n"

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

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
        await redis.set({"role": db_message.role, "content": db_message.content})

        async def cached_stream():
            yield f"chunks: {json.dumps({'data': stored_message}), 'status': 'cached', }\n\n"

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

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
    redis_chat_history_key: str = f"chat_history:uid:{uid}"
    redis_chat_history_key_exp: int = 60 * 60 * 12  # 12 hour
    message_window_length: int = 40
    stored_chat_history: list[dict] = (
        await redis.get(redis_chat_history_key, default=[]) or []
    )

    if stored_chat_history:
        chat_history = (
            db.query(Messages.content, Messages.role)
            .filter_by(chat_uid=uid)
            .order_by(Messages.created_at.desc())
            .all()
        )

        if chat_history:
            _chat_history: list = []
            for message in chat_history:
                _chat_history.append({"role": message.role, "content": message.content})
            _chat_history.reverse()
            await redis.set(
                redis_chat_history_key, _chat_history, ttl=redis_chat_history_key_exp
            )
            stored_chat_history.extend(_chat_history)

    stored_chat_history.append(
        {"role": ChatRoleType.USER.value, "content": message_data.content}
    )

    if len(stored_chat_history) > message_window_length:
        stored_chat_history = stored_chat_history[-message_window_length:]

    # Call agent and send message history with latest message
    event = chat_agent(json.dumps(stored_chat_history))

    # return res
    async def agent_event():
        full_response = ""
        assistent_uid = str(uuid.uuid4())
        try:
            async for chunk in event:
                data_chunk = {
                    "chunk": chunk.choices[0].delta.content,
                    "status": "loading",
                }
                full_response += chunk.choices[0].delta.content
                yield f"data: {json.dumps(data_chunk)}\n\n"

            # store agent response to DB
            agent_res = Messages(
                chat_uid=uid,
                content=full_response,
                role="assistant",
                message_uid=assistent_uid,
            )
            db.add(agent_res)
            db.commit()

            # Cache message and append in history
            await redis.set(redis_message_key, full_response, ttl=redis_message_key_exp)
            stored_chat_history.append(
                {"role": ChatRoleType.ASSISTANT, "content": full_response}
            )
            await redis.set(
                redis_chat_history_key,
                stored_chat_history,
                ttl=redis_chat_history_key_exp,
            )

            # Signal end of stream
            yield f"data: {json.dumps({'status': 'success', 'message_uid': assistent_uid})} \n\n"
        except Exception as e:
            logger.exception("Error while message generation")
            data_chunk = {
                "chunk": "Sorry, I encountered an error processing your request.",
                "status": "error",
            }
            yield f"data: {json.dumps({'chunk': data_chunk, 'status': 'failed', 'error': str(e)})}\n\n"

    return StreamingResponse(agent_event(), media_type="text/event-stream")
