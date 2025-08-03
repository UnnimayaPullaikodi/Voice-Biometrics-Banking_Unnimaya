import sys
import streamlit as st
import sounddevice as sd
import scipy.io.wavfile as wav
import os
import datetime
from faker import Faker
#from models.training_evaluation import audio_to_embedding_enhanced, init_pinecone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.training_evaluation import audio_to_embedding_enhanced, init_pinecone

# Setup
RECORDINGS_DIR = "data/recordings"
USER_INPUT = "data/user_input"
fake = Faker()

for d in [RECORDINGS_DIR, USER_INPUT]:
    os.makedirs(d, exist_ok=True)

st.set_page_config(page_title="Voice Biometrics", layout="centered")
st.title("🔊 Voice Biometrics")

# Navigation
page = st.sidebar.radio("Navigation", ["Register", "Money Transfer"])
user_id = st.text_input("Enter Your User ID")

# Record Audio Function
def record_audio(duration=5, fs=16000):
    st.info(f"🎙️ Recording for {duration} seconds...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    st.success("✅ Recording complete.")
    return audio, fs

# Save Audio Function
def save_audio(audio, fs, filename):
    wav.write(filename, fs, audio)
    st.success(f"🎧 Audio saved: {filename}")

# ---------- REGISTER ----------
if page == "Register":
    st.subheader("📝 Register Your Voice")
    st.info(fake.sentence())

    if user_id:
        if st.button("🎤 Record Voice Sample"):
            audio, fs = record_audio()
            raw_path = os.path.join(RECORDINGS_DIR, f"{user_id}.wav")
            save_audio(audio, fs, raw_path)
            st.audio(raw_path, format='audio/wav')

            try:
                index = init_pinecone()
                embedding = audio_to_embedding_enhanced(raw_path)

                if embedding is not None:
                    index.upsert([
                        (user_id, embedding.tolist(), {"source": "registration", "file": f"{user_id}.wav"})
                    ])
                    st.success("✅ Voice registered and stored in Pinecone.")
                else:
                    st.error("❌ Failed to extract voice embedding.")
            except Exception as e:
                st.error(f"💥 Error during registration: {e}")
    else:
        st.warning("⚠️ Please enter a User ID.")

# ---------- MONEY TRANSFER ----------
elif page == "Money Transfer":
    st.subheader("💸 Money Transfer with Voice Verification")

    recipient = st.selectbox("Send Money To", ["John", "Alice", "Bob", "Emily"])
    amount = st.number_input("Amount to Transfer ($)", min_value=1.0, step=1.0)
    note = st.text_input("Note (optional)", placeholder="e.g., for rent")
    phrase = fake.sentence()
    st.markdown(f"### 🗣 Please say this phrase:\n> **\"{phrase}\"**")

    if user_id and st.button("🎙 Record & Verify"):
        reference_file = os.path.join(RECORDINGS_DIR, f"{user_id}.wav")

        if os.path.exists(reference_file):
            audio, fs = record_audio()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            test_path = os.path.join(USER_INPUT, f"{user_id}_test_{timestamp}.wav")
            save_audio(audio, fs, test_path)
            st.audio(test_path, format='audio/wav')

            try:
                index = init_pinecone()
                query_embedding = audio_to_embedding_enhanced(test_path)

                if query_embedding is not None:
                    matches = index.query(vector=query_embedding.tolist(), top_k=1, include_metadata=True)
                    if matches and matches['matches']:
                        match = matches['matches'][0]
                        st.write(f"🔍 Match Found: **{match['id']}** | Score: `{match['score']:.4f}`")

                        if match['id'] == user_id:
                            st.success(f"✅ Voice verified. ${int(amount)} sent to {recipient}.")
                            st.balloons()
                        else:
                            st.error("❌ Voice mismatch. Transaction blocked.")
                    else:
                        st.warning("⚠️ No match found.")
                else:
                    st.error("❌ Failed to extract embedding from test audio.")
            except Exception as e:
                st.error(f"💥 Verification failed: {e}")
        else:
            st.error(f"🚫 No registered voice found for '{user_id}'.")
