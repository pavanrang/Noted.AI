import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq()

def transcribe_audio(uploaded_file):
    temp_filename = "temp_audio_file" + os.path.splitext(uploaded_file.name)[1]
    with open(temp_filename, "wb") as temp_file:
        temp_file.write(uploaded_file.read())

    with open(temp_filename, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(temp_filename, file.read()),
            model="whisper-large-v3",
            prompt="Specify context or spelling",
            response_format="json",
            language="en",
            temperature=0.0
        )

    os.remove(temp_filename)
    
    # Convert the Transcription object to a dictionary
    return {
        "text": transcription.text,
        "segments": [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            }
            for segment in transcription.segments
        ] if hasattr(transcription, 'segments') else []
    }