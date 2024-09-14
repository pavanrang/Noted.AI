from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq()

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
