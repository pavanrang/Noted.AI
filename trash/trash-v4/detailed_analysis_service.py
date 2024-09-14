from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq()

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
