import base64
import json
from datetime import datetime


def encode_cursor(article_id: int, created_at: datetime) -> str:
    """
    Encode pagination cursor from article data.

    Uses base64 encoding to hide implementation details.
    """
    cursor_data = {
        "id": article_id,
        "created_at": created_at.isoformat()
    }
    json_str = json.dumps(cursor_data)
    return base64.urlsafe_b64encode(json_str.encode()).decode()

def decode_cursor(cursor: str) -> dict:
    """
    Decode cursor back to usable data.

    Raises HTTPException if cursor is invalid.
    """
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(json_str)
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return data
    except Exception:
        raise
        # raise HTTPException(status_code=400, detail="Invalid cursor")