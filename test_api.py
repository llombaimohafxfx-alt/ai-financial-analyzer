import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="In one sentence, what is EBITDA?"
)

print(response.text)
