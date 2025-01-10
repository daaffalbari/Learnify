from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class InputChapter(BaseModel):
    title: str = Field(..., title="Title of the chapter")
    units: List[str] = Field(..., title="List of units")

class InputMaterial(BaseModel):
    materi: str = Field(..., title="Material for generating questions")


class ListQuestion(BaseModel):
    questions: List[str] = Field(..., title="List of questions")


class Input(BaseModel):
    title: str = Field(..., title="Title of the course")
    youtube_query: str = Field(..., title="YouTube search query")


class ChatRequest(BaseModel):
    message: str


