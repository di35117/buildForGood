import os
import json
from google import genai
from google.genai import types
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def process_incident_audio(audio_file_path: str, dossier_data: dict = None) -> dict:
    """
    [P0] LLM reasoning engine. Fortified with hard sensor data if bridged from Module 1.
    """
    audio_file = client.files.upload(file=audio_file_path)
    context_injection = ""
    if dossier_data:
        context_injection = f"\n\nCRITICAL CONTEXT: The user's device automatically triggered an SOS. Here is the verified telemetry and sensor data from the event: {json.dumps(dossier_data)}. Integrate this undeniable evidence into the complaint draft."

    prompt = f"""
    You are a legal assistant for a women's safety platform in India.
    Listen to this audio (which may be in Hindi, regional languages, or English) 
    and provide a structured JSON response with the following keys:
    - "transcription": The raw text of what was said.
    - "summary": A concise 2-sentence summary of the incident.
    - "complaint_draft": A structured, formal complaint draft ready for NGO/human review.
    - "severity": Classify as 'High', 'Medium', or 'Low'.
    - "next_steps": A list of 3 immediate safety or legal steps the user should take.
    {context_injection}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, audio_file],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    client.files.delete(name=audio_file.name)
    return json.loads(response.text)

def transcribe_incident_audio(audio_file_path: str) -> str:
    """[P0] Takes raw audio from a community incident report and transcribes it to plain text."""
    audio_file = client.files.upload(file=audio_file_path)
    prompt = "Listen to this audio and provide a highly accurate, plain-text transcription of what is being said. Translate to English if it is in a regional language."
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, audio_file]
    )
    
    client.files.delete(name=audio_file.name)
    return response.text

def moderate_forum_post(content: str) -> bool:
    """[P1] Module 3 AI Moderator: Scans anonymous forum posts for crisis signals."""
    prompt = f"""
    You are a safety moderator for an anonymous peer support forum for young girls in India. 
    Read the following post. Does it contain immediate threats of suicide, self-harm, severe domestic abuse, or a critical medical emergency?
    
    If YES (it is a crisis), reply with exactly the word: TRUE
    If NO (it is a normal health question, venting, or peer advice), reply with exactly the word: FALSE
    
    Do not include any other text, punctuation, or explanation. Just TRUE or FALSE.
    
    Post content: "{content}"
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        result = response.text.strip().upper()
        
        if "TRUE" in result:
            return True
        return False
        
    except Exception as e:
        print(f"AI Moderation Failed: {e}. Defaulting to safe (False).")
        return False