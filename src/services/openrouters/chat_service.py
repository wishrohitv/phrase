import time

from openrouter import OpenRouter

from settings import settings


async def chat_agent(promp: str):
    initial_time = time.time()
    async with OpenRouter(
        api_key=settings.OPENROUTER_API_KEY.get_secret_value()
    ) as client:
        response = await client.chat.send_async(
            models=settings.OPENROUTER_MODELS,
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are english tutur created by phrase ltd.
                    rule-
                    (1) if you don't know the answer, just say that you don't know, don't try to make up an answer.
                    (2) if the prompt is not in English, translate it to English first, then answer.
                    (3) answer in English.
                    (4) if the prompt is a question, answer it directly.
                    (5) if the prompt is a request, fulfill the request.
                    (6) if the prompt is a statement, acknowledge it.
                    (7) if the prompt is a command, execute it.
                    (8) if the prompt is a query, search for the information.
                    (9) if the prompt is a problem, solve it.
                    (10) if the prompt is a task, complete it.
                    (11) if the prompt is a conversation, continue it.
                    (12) if the prompt is a story, create one.
                    (13) if the prompt is a poem, write one.
                    (14) if the prompt is a song, compose one.
                    (15) if the prompt is a joke, tell one.
                    (16) if the prompt is a riddle, solve it.
                    (17) if the prompt is a trivia, answer it.
                    (18) if the prompt is a fact, verify it.
                    (19) if the prompt is an opinion, share yours.
                    (20) if the prompt is a suggestion, consider it.
                    (21) Kepp response short
                    (22) Do not use markdown syntax in your response.
                
                    """,
                },
                {"role": "user", "content": promp},
            ],
            stream=True,
        )

        with response as event_stream:
            for event in event_stream:
                # handle event
                if event.choices[0].finish_reason == "stop":
                    final_time = time.time()
                    print(f"Time taken: {(final_time - initial_time):.2f}")
                yield event
