from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NewsItem(BaseModel):
    title: str
    description: str
    quote: Optional[str] = None
    source: str
    reference_link: Optional[str] = None

class NewsResponse(BaseModel):
    section_title: str
    items: List[NewsItem]
    summary: Optional[str] = None
