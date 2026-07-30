from pydantic import BaseModel
from typing import List, Dict, Optional

class PatchInput(BaseModel):
    game_id: str
    text: str
    custom_instructions: Optional[str] = None

class SummaryResponse(BaseModel):
    tl_dr: List[str]
    categorized: Dict[str, List[str]]
    things_to_recheck: List[str]
    meta_impact_notes: List[str]
    impact_score: int
    impact_reason: str