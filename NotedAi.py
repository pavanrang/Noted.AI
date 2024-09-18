import streamlit as st
import io
import os
import json
from audio_recorder_streamlit import audio_recorder
from backend_services import transcribe_audio, generate_summary, generate_detailed_analysis, chatbot_response, extract_links, export_notes

st.set_page_config(page_title="NotedAi", page_icon="🪶", layout="wide")

st.title("NotedAi🪶")

# Initialize session state for storing transcripts
if 'transcripts' not in st.session_state:
    st.session_state.transcripts = {}

# Sidebar for audio input options and transcript management
st.sidebar.header("Audio Management")
input_option = st.sidebar.radio("Choose action:", ("New Audio", "Manage Existing"))

if input_option == "New Audio":
    st.sidebar.header("Audio Input")
    input_method = st.sidebar.radio("Choose input method:", ("Upload Audio", "Record Audio"))

    audio_input = None

    if input_method == "Upload Audio":
        uploaded_file = st.sidebar.file_uploader("Choose an audio file", type=["mp3", "wav"])
        if uploaded_file:
            audio_input = uploaded_file
    else:
        st.sidebar.write("Click the button below to start recording:")
        audio_bytes = audio_recorder()
        if audio_bytes:
            st.sidebar.audio(audio_bytes, format="audio/wav")
            audio_input = io.BytesIO(audio_bytes)

    if audio_input is not None:
        try:
            transcription = transcribe_audio(audio_input)
            
            # Save the new transcript
            transcript_name = st.text_input("Enter a name for this transcript:")
            if st.button("Save Transcript") and transcript_name:
                st.session_state.transcripts[transcript_name] = transcription
                st.success(f"Transcript '{transcript_name}' saved successfully!")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your internet connection, API key, and try again.")

else:
    # Manage existing transcripts
    st.sidebar.header("Manage Existing Transcripts")
    selected_transcript = st.sidebar.selectbox("Select a transcript", list(st.session_state.transcripts.keys()))

    if selected_transcript:
        transcription = st.session_state.transcripts[selected_transcript]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Transcription (Editable)")
            edited_transcript = st.text_area("Edit the transcript if needed:", value=transcription['text'], height=300)
            
            if st.button("Update Transcript"):
                st.session_state.transcripts[selected_transcript]['text'] = edited_transcript
                st.success("Transcript updated successfully!")

            if transcription['segments']:
                st.subheader("Segments")
                for segment in transcription['segments']:
                    st.write(f"Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
                    st.write(f"Text: {segment['text']}")
                    st.write("---")

        with col2:
            if st.button("Generate Summary"):
                summary = generate_summary(edited_transcript)
                st.subheader("Summary")
                st.write(summary)

            if st.button("Generate Detailed Analysis"):
                detailed_analysis = generate_detailed_analysis(edited_transcript)
                st.subheader("Detailed Analysis")
                st.write(detailed_analysis)

            st.subheader("Ask a question about the audio:")
            user_question = st.text_input("Enter your question here:")
            if st.button("Get Answer"):
                if user_question:
                    answer = chatbot_response(edited_transcript, user_question)
                    st.write("Answer:")
                    st.write(answer)
                else:
                    st.write("Please enter a question.")

        # Extract and display relevant links
        links = extract_links(edited_transcript)
        if links:
            st.subheader("Relevant Links")
            for link in links:
                st.markdown(f"[{link['title']}]({link['url']})")

        # Export notes
        if st.button("Export Notes"):
            summary = generate_summary(edited_transcript)
            analysis = generate_detailed_analysis(edited_transcript)
            notes = export_notes(edited_transcript, summary, analysis, links)
            st.download_button(
                label="Download Notes",
                data=notes,
                file_name=f"{selected_transcript}_analysis_notes.md",
                mime="text/markdown"
            )

# Add option to delete transcripts
if st.session_state.transcripts:
    st.sidebar.header("Delete Transcripts")
    transcript_to_delete = st.sidebar.selectbox("Select transcript to delete", list(st.session_state.transcripts.keys()))
    if st.sidebar.button("Delete Selected Transcript"):
        del st.session_state.transcripts[transcript_to_delete]
        st.sidebar.success(f"Transcript '{transcript_to_delete}' deleted successfully!")
