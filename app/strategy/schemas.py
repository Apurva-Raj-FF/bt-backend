from pydantic import BaseModel

# Schema for Query Execution 
class QueryExecutionRequest(BaseModel):
    session_id: str
    user_token: str
    data: dict

# Schema for Saving Strategy 
class SaveStrategyRequest(BaseModel):
    session_id: str
    strat_name_alias: str
    isPublic: int
    