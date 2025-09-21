from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from rag_utils import hybrid_search

from datetime import datetime

from pathlib import Path

from backend_google.google_drive2 import send_to_google_drive

LOG_FILE = Path("answers.log")

class_selected = [""]
#make a ceng351 notesheet on memory adders
def change_selected_class_tools(new_class):
    class_selected[0] = new_class
    print(class_selected[0])

class QueryInput(BaseModel): 
    prompt: str = Field(description="The query from the user")

class AIResponseInput(BaseModel):
    ai_response: str = Field(description="The response from the AI to answer the users question.")

class NoteSheetInput(BaseModel):
    content: str = Field(description="The note sheet itself. This field is the content of the note sheet.")
    title: str = Field(description="A short descriptive title for the note sheet")

class LecturePathInformation(BaseModel):
    lecture_path: str = Field(description="The lecture Path to get the entire lecture notes.")


@tool("get_information_from_database", args_schema=QueryInput, return_direct=False)
def get_information_from_database(prompt: str):
    """Accesses student data and returns important information. This calls the database to give the AI relevant information"""
    try:
        # response = llm.invoke(prompt)
        important_information = hybrid_search(prompt, class_selected, k_final=5, w_emb=0.7, w_bm25=0.3)
        return important_information
    except Exception as e:
        return {"error": str(e)}

@tool("create_note_sheet", args_schema=NoteSheetInput, return_direct=True)
def create_note_sheet(content: str, title: str):
    """Sends AI response to a google doc to create a note sheet. The AI needs to have already generated the note sheet content. This is just to create the google doc."""
    try:
        send_to_google_drive(content, title)
    except Exception as e:
        return {"error": str(e)}
    
@tool("answer_question", args_schema=AIResponseInput, return_direct=True)
def answer_question(ai_response: str):
    """
    Answers the user question by sending the AI response to the user. 
    """
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(ai_response + "\n\n")  # double newline for readability
        return {"success": True, "saved_to": str(LOG_FILE)}
    except Exception as e:
        return {"error": str(e)}

@tool("get_entire_lecture_notes", args_schema=LecturePathInformation, return_direct=False)
def get_entire_lecture_notes(lecture_path: str):
    """Gets the entire lecture notes for a specific lecture from a .txt file."""
    try:
        with open(lecture_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Return as a plain string so LLM can process the full lecture notes
        return content
    except FileNotFoundError:
        return {"error": f"Lecture file not found at path: {lecture_path}"}
    except Exception as e:
        return {"error": str(e)}

@tool("get_current_date", return_direct=False)
def get_current_date(_=None):
    """Gets the current date in YYYY-MM-DD format."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        return today
    except Exception as e:
        return {"error": str(e)}






tools = [get_information_from_database, create_note_sheet, answer_question, get_entire_lecture_notes, get_current_date]
