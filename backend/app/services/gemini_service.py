import os
import json
from google import genai
from google.genai import types
from app.core.config import settings

# Initialize the new Google GenAI SDK client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

def process_incident_audio(audio_file_path: str) -> dict:
    """
    [P0] Takes raw audio, transcribes it, and structures it into a 
    legal complaint draft using LLM reasoning.
    """
    # 1. Upload the temporary audio file using the new Files API
    audio_file = client.files.upload(file=audio_file_path)
    
    # 2. Prompt the AI for structured output
    prompt = """
    You are a legal assistant for a women's safety platform in India.
    Listen to this audio (which may be in Hindi, regional languages, or English) 
    and provide a structured JSON response with the following keys:
    - "transcription": The raw text of what was said.
    - "summary": A concise 2-sentence summary of the incident.
    - "complaint_draft": A structured, formal complaint draft ready for NGO/human review.
    - "severity": Classify as 'High', 'Medium', or 'Low'.
    - "next_steps": A list of 3 immediate safety or legal steps the user should take.
    """
    
    # 3. Generate the response using Gemini 2.5 Flash
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, audio_file],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    # 4. Clean up the file from Gemini servers immediately
    client.files.delete(name=audio_file.name)
    
    # 5. Parse the guaranteed JSON string back into a Python dictionary
    return json.loads(response.text)

def transcribe_incident_audio(audio_file_path: str) -> str:
    """
    [P0] Takes raw audio from a community incident report and transcribes it to plain text.
    """
    audio_file = client.files.upload(file=audio_file_path)
    
    prompt = "Listen to this audio and provide a highly accurate, plain-text transcription of what is being said. Translate to English if it is in a regional language."
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, audio_file]
    )
    
    client.files.delete(name=audio_file.name)
    return response.text
def moderate_forum_post(content: str) -> bool:
    """
    [P1] Module 3 AI Moderator: Scans anonymous forum posts for crisis signals.
    Returns True if the post requires human NGO review, False if it's safe to publish.
    """
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
        
        # Clean the response to ensure we just get the boolean
        result = response.text.strip().upper()
        
        if "TRUE" in result:
            return True
        return False
        
    except Exception as e:
        print(f"AI Moderation Failed: {e}. Defaulting to safe (False).")
        return False