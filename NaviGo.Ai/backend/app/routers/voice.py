from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from backend.app.services.voice import parse_audio_voice_input, parse_voice_transcript_heuristics

router = APIRouter(prefix="/voice", tags=["Voice Assistant"])

class VoiceTranscriptRequest(BaseModel):
    transcript: str

class VoiceParseResponse(BaseModel):
    transcript: str
    language: str
    params: Dict[str, Any]
    missing_fields: List[str]

@router.post("/parse", response_model=VoiceParseResponse)
async def parse_voice(
    file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None)
):
    if file:
        contents = await file.read()
        res = await parse_audio_voice_input(contents, file.filename or "recording.webm")
        return VoiceParseResponse(**res)
    elif transcript:
        res = parse_voice_transcript_heuristics(transcript)
        return VoiceParseResponse(**res)
    else:
        raise HTTPException(status_code=400, detail="Provide an audio file or transcript text.")
