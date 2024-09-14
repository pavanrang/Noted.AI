import streamlit as st
from transcription_service import transcribe_audio
from summary_service import generate_summary
from detailed_analysis_service import generate_detailed_analysis
from segment_display_service import display_segments
from chatbot_service import chatbot_response

st.set_page_config(page_title="Advanced Audio Analyzer", page_icon="📢", layout="centered")
st.title("📢 Advanced Audio Analyzer")
st.header("Upload an audio file")

uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])

if uploaded_file is not None:
    transcription = transcribe_audio(uploaded_file)
    
    st.subheader("Transcription:")
    st.write(transcription['text'])
    
    if transcription['segments']:
        st.subheader("Segments:")
        display_segments(transcription['segments'])
    else:
        st.write("No detailed segments available.")
    
    if st.button("Generate Summary"):
        summary = generate_summary(transcription['text'])
        st.subheader("Summary:")
        st.write(summary)
    
    if st.button("Generate Detailed Analysis"):
        detailed_analysis = generate_detailed_analysis(transcription['text'])
        st.subheader("Detailed Analysis:")
        st.write(detailed_analysis)
    
    st.subheader("Ask a question about the audio:")
    user_question = st.text_input("Enter your question here:")
    if st.button("Get Answer"):
        if user_question:
            answer = chatbot_response(transcription['text'], user_question)
            st.write("Answer:")
            st.write(answer)
        else:
            st.write("Please enter a question.")