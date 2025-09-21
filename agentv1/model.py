import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI

from tools import tools

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model= "gemini-2.0-flash",
    temperature=0.3,
    max_retries=2,
    google_api_key=api_key,
)

# bind tools to the model, tools = [get_text_response, create_note_sheet]
model = llm.bind_tools([tools[0], tools[1], tools[2], tools[3], tools[4]])

