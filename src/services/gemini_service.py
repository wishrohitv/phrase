from google import genai
from settings import settings


print("sldkfdskkkkkkkkkkkk")
print("Geminikey", settings.GEMINI_API_KEY.get_secret_value())
client = genai.Client(api_key=settings.GEMINI_API_KEY.get_secret_value())


def gemini_service():

    interaction = client.interactions.create(
        model="gemini-3.5-flash", input="Explain how AI works in a few words"
    )
    print(interaction.output_text)
