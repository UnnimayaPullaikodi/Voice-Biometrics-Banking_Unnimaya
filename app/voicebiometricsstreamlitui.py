"""import streamlit as st

from pyngrok import ngrok
from audio_recorder_streamlit import audio_recorder

# Start tunnel
#public_url = ngrok.connect(8501)
#print("Public URL:", public_url)


st.title("Helllooo")



audio_bytes = audio_recorder(energy_threshold=(-1.0, 1.0),
  pause_threshold=4.0,)
if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")


uploaded_file = st.file_uploader("Choose a file",type=['.mp3','.ogg','.flac'])
if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    st.write(bytes_data)
if __name__ == "__main__":
    from pyngrok import ngrok
    public_url = ngrok.connect(8501)
    print("Public URL:", public_url)"""
    
    # streamlit_app.py

import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Convert2Wav.ConvertAudioToWav import convert_folder_to_wav
from io import BytesIO


UPLOAD_DIR = "uploaded_audio"
OUTPUT_DIR = "converted_audio"

st.title("🎵 Voice Biometrics for Safe Banking")

uploaded_files = st.file_uploader("Upload audio files", type=["mp3", "m4a", "aac", "ogg", "flac", "wav"], accept_multiple_files=True)

if uploaded_files:
    # Create folders if they don't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: Save uploaded files
    for file in uploaded_files:
        with open(os.path.join(UPLOAD_DIR, file.name), "wb") as f:
            f.write(file.read())

    st.success(f"Uploaded {len(uploaded_files)} files.")

    # Step 2: Convert using your batch_converter
    convert_folder_to_wav(UPLOAD_DIR, OUTPUT_DIR)

    # Step 3: Display and allow download
    st.header("🎧 Converted WAV Files")
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(".wav"):
            file_path = os.path.join(OUTPUT_DIR, filename)
            with open(file_path, "rb") as f:
                st.audio(f.read(), format="audio/wav")
                f.seek(0)
                st.download_button("Download " + filename, data=f, file_name=filename, mime="audio/wav")


#streamlit run StreamlitUI/voicebiometricsstreamlitui.py