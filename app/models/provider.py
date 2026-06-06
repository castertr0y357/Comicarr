from typing import Optional
from sqlmodel import SQLModel, Field

class SearchProvider(SQLModel, table=True):
    __tablename__: str = "search_providers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: str  # "newznab", "torznab", "prowlarr"
    url: str
    apikey: Optional[str] = None
    enabled: bool = Field(default=True)
    categories: Optional[str] = Field(default="7030,8020")
