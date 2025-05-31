from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NewsItem(BaseModel):
    title: str
    description: str
    link: str
    date: str # Keep as string for simplicity, as it's already formatted
    tags: List[str]
    authors: List[str]
    source: str

class NewsResponse(BaseModel):
    section_title: str
    items: List[NewsItem]
    summary: Optional[str] = None
