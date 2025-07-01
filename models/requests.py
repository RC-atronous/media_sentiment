from pydantic import BaseModel
from typing import Optional

class AnalyzeMediaRequest(BaseModel):
    "Request transcription and analysis via link"

    link: str #hyperlink to media

class AnalysisResponse(BaseModel):
    "Response from Analysis"
    success: bool
    details: Optional[dict] = None