
from optparse import Option
from typing import TypedDict, Optional, Dict,List
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

class AgentState(BaseModel):
    user_inp: HumanMessage
    news: Optional[List[Dict]] = None
    prices : Optional[List[Dict]] = None
    sentiment: Optional[str] = None
    recommendation: Optional[str] = None
    user_feedback: Optional[str] = None
    result: Optional[str] = None
