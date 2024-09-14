import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


client = Groq()


st.set_page_config(page_title="Audio to Text Converter",page_icon="📢",  layout="centered", )
st.title("📢 Audio to Text Converter")
st.header("Upload an audio file")

uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])

if uploaded_file is not None:
    temp_filename = "temp_audio_file" + os.path.splitext(uploaded_file.name)[1]
    with open(temp_filename, "wb") as temp_file:
        temp_file.write(uploaded_file.read())

    with open(temp_filename, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(temp_filename, file.read()),
            model="whisper-large-v3",
            prompt="Specify context or spelling",  # Optional
            response_format="json",  # Optional
            language="en",  # Optional
            temperature=0.0  # Optional
        )

    st.write("Transcription:")
    st.write(transcription.text)
    
    os.remove(temp_filename)