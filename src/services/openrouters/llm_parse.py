import os
import time
from logging import getLogger

from openrouter import OpenRouter
from pydantic import TypeAdapter

from common.pydantic_schema import PhraseOrSentence
from settings import settings

logger = getLogger(__name__)


ListSchemaAdapter = TypeAdapter(list[PhraseOrSentence])

SCHEMA = ListSchemaAdapter.json_schema()

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "PhraseOrSentenceList",
        "strict": True,
        "schema": SCHEMA,
    },
}
INSTRUCTION_FILE_PATH = os.path.join(
    os.getcwd(), "src/services/openrouters/llm_subtitle_instruction.md"
)
llm_instruction_promp = None
with open(
    INSTRUCTION_FILE_PATH,
) as f:
    llm_instruction_promp = f.read()

# context = {
#     "subtitle_filename": "Breaking.Bad.S01E01.srt",
#     "learning_language": "English",
#     "native_language": "Hindi",
#     "subtitle_chunk_text": subtitle_content,
# }


async def llm_process_subtitle_data(context: str):

    initial_time = time.time()
    async with OpenRouter(
        api_key=settings.OPENROUTER_API_KEY.get_secret_value()
    ) as client:
        response = await client.chat.send_async(
            models=settings.OPENROUTER_MODELS,
            messages=[
                {
                    "role": "system",
                    "content": llm_instruction_promp,
                },
                {"role": "user", "content": str(context)},
            ],
            response_format=RESPONSE_FORMAT,
        )

        last_time = time.time()

        logger.info(
            f"OpenRouter API call model used: {response.model}, Token used: {response.usage.dict()}"
        )
        logger.info(
            f"OpenRouter API call took {(last_time - initial_time):.2f} seconds for extracting Subtitle file"
        )
        return response.choices[0].message.content
