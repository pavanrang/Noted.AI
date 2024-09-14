import streamlit as st

def display_segments(segments):
    for segment in segments:
        st.write(f"Time: {segment['start']:.2f}s - {segment['end']:.2f}s")
        st.write(f"Text: {segment['text']}")
        st.write("---")
