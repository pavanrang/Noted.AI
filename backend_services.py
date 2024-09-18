import os
import json
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq()

def transcribe_audio(audio_file):
    temp_filename = "temp_audio_file.wav"
    with open(temp_filename, "wb") as temp_file:
        temp_file.write(audio_file.read())

    try:
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
    except Exception as e:
        os.remove(temp_filename)
        raise Exception(f"An unexpected error occurred: {str(e)}")

def generate_summary(text):
    prompt = f"Please provide a concise summary of the following text:\n\n{text}\n\nSummary:"
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="mixtral-8x7b-32768",
        max_tokens=150,
    )
    
    return response.choices[0].message.content

def generate_detailed_analysis(text):
    prompt = f"""Please provide a detailed analysis of the following text, including main topics and subtopics in bullet points:

{text}

Detailed Analysis:"""
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="mixtral-8x7b-32768",
        max_tokens=500,
    )
    
    return response.choices[0].message.content

def chatbot_response(transcription, question):
    prompt = f"""You are an AI assistant that answers questions about an audio transcription. 
    Here's the transcription:

    {transcription}

    Now, please answer the following question about the transcription:
    {question}

    If the answer is explicitly stated in the transcription, provide it. 
    If it's not explicitly stated but can be inferred, provide your best inference and note that it's an inference. 
    If the information is not available in the transcription, please say so.
    """

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions about audio transcriptions.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="mixtral-8x7b-32768",
        max_tokens=300,
    )
    
    return response.choices[0].message.content

def extract_links(text):
    prompt = f"""Please extract and list all websites, articles, or documents mentioned in the following text. 
    If no specific links are mentioned, suggest up to 3 relevant resources based on the content:

    {text}

    Format the output as a JSON list of objects, each with 'title' and 'url' fields."""

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that extracts or suggests relevant links from text.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="mixtral-8x7b-32768",
        max_tokens=300,
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return []
def save_transcript(name, transcript_data, storage_dir="transcripts"):
    """Save a transcript to a JSON file."""
    os.makedirs(storage_dir, exist_ok=True)
    file_path = os.path.join(storage_dir, f"{name}.json")
    with open(file_path, "w") as f:
        json.dump(transcript_data, f)

def load_transcript(name, storage_dir="transcripts"):
    """Load a transcript from a JSON file."""
    file_path = os.path.join(storage_dir, f"{name}.json")
    with open(file_path, "r") as f:
        return json.load(f)

def list_transcripts(storage_dir="transcripts"):
    """List all saved transcripts."""
    os.makedirs(storage_dir, exist_ok=True)
    return [f.split(".")[0] for f in os.listdir(storage_dir) if f.endswith(".json")]

def delete_transcript(name, storage_dir="transcripts"):
    """Delete a saved transcript."""
    file_path = os.path.join(storage_dir, f"{name}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
def export_notes(transcription, summary, analysis, links):
    notes = f"""# Audio Analysis Notes

## Transcription
{transcription}

## Summary
{summary}

## Detailed Analysis
{analysis}

## Relevant Links
"""
    for link in links:
        notes += f"- [{link['title']}]({link['url']})\n"
    
    return notes
