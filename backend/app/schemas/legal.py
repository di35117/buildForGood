from pydantic import BaseModel
from typing import List

class ComplaintDraftResponse(BaseModel):
    transcription: str
    summary: str
    complaint_draft: str
    severity: str
    next_steps: List[str]