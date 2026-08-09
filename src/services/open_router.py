import os
import time

from dotenv import load_dotenv
from openrouter import OpenRouter

load_dotenv()
initial_time = time.time()

subs_chunks = "filecontent.srt"
with open(subs_chunks, "r") as f:
    content = f.readlines(2100)


async def process_subtitile_data():
    with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
        response = client.chat.send(
            models=[
                "inclusionai/ling-3.0-flash:free",
                "deepseek/deepseek-v4-flash-0731",
                "cohere/north-mini-code:free",
                # "nvidia/nemotron-3-ultra-550b-a55b:free",
                # "openrouter/free",
                # "tencent/hy3",
            ],
            messages=[
                {
                    "role": "system",
                    "content": """Find advance, midium and basic english senetece or words from the text \n
                    return respnse in this format using json 
                    do not return anything else just return json format
                    avoid using backtics ```json {}```, so it will be easy to convert into python json object
                    e.g [
                        "id": {
                            "type": [advance or midium or basic]
                            "sentence": "",
                            "meaning": ""
                            "usage": []
                        },
                    ]
                    """,
                },
                {"role": "user", "content": str(content)},
            ],
        )
        print(response.model)
        print(response.choices[0].message.content)
        last_time = time.time()

        print(last_time - initial_time, "seconds")
