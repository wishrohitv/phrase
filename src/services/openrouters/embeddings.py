import json

import requests

from settings import settings


def get_embedding(text: str) -> list[float]:
    response = requests.post(
        url="https://openrouter.ai/api/v1/embeddings",
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY.get_secret_value()}",
            "Content-Type": "application/json",
            # "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
            "X-OpenRouter-Title": settings.APP_NAME,  # Optional. Site title for rankings on openrouter.ai.
        },
        data=json.dumps(
            {
                "model": "nvidia/nemotron-3.5-embed-1b:free",
                "input": text,
                # "input": ["text1", "text2", "text3"], # batch embeddings also supported!
                "encoding_format": "float",
            }
        ),
    )
    result: dict = response.json()

    return result["data"][0]["embedding"]
