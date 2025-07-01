from fastapi import FastAPI
from .models.requests import AnalyzeMediaRequest, AnalysisResponse
from .Transcription.transcriptor import AnalyzeMediaLink
from .Transcription.analysis import analyzeTranscript, keywordExtractor
import logging

app = FastAPI()

logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {"message": "Initial"}

@app.post("/transcription_analyzer")
async def transcriptor(data : AnalyzeMediaRequest):
    hyperlink_to_analyze = data.link

    logger.info(f"Analyzing the following media link {hyperlink_to_analyze}")

    if hyperlink_to_analyze is None:
        logger.warn("No link to analyze")
        response = AnalysisResponse(success=False, details={})
        return response
    
    print(hyperlink_to_analyze)

    Link = AnalyzeMediaLink()

    transcript_final = await Link.transcript(hyperlink_to_analyze)


    keywords = ["Placeholder1","Placeholder2","Placeholder3"]

    analysis = await analyzeTranscript(transcript_final)

    keywords = await keywordExtractor(analysis)

    

    details = {
        "hyperlink": hyperlink_to_analyze,
        "transcript": transcript_final,
        "important frags": analysis,
        "keywords": keywords

    }

    response = AnalysisResponse(success=True,details=details)

    return response