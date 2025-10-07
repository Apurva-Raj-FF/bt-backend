from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Param(BaseModel):
    name: str
    id: int

class DataItem(BaseModel):
    param: Param
    period: Optional[int] = None
    sign: str
    threshold: float

class Filter(BaseModel):
    Data: DataItem
    Operator: str

class DataEntry(BaseModel):
    filters: List[Filter]

class QueryExecutionRequest(BaseModel):
    session_id: str
    user_token: str
    data: List[DataEntry]

# Schema for Saving Strategy 
class SaveStrategyRequest(BaseModel):
    session_id: str
    strat_name_alias: str
    isPublic: int
    