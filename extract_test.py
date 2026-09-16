import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Upload the PDF to Google's Files API so we can reference it in the prompt
pdf_file = client.files.upload(file="reports/aldar_2025.pdf")

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=[
        pdf_file,
        "What was Aldar's total revenue for the most recent full year reported "
        "in this document? State the exact figure, the currency, and the exact "
        "page number of the PDF where you found it."
    ]
)

print(response.text)