from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq()

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
