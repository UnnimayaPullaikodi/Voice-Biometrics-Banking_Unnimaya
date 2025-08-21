import sys
import streamlit as st
import os
import datetime
from faker import Faker
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import numpy as np
import scipy.io.wavfile as wav

# Custom imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.training_evaluation import audio_to_embedding_enhanced, init_pinecone

# -------------------- Setup --------------------
RECORDINGS_DIR = "data/recordings"
USER_INPUT = "data/user_input"
fake = Faker()

for d in [RECORDINGS_DIR, USER_INPUT]:
    os.makedirs(d, exist_ok=True)

st.set_page_config(page_title="Voice Biometrics", layout="centered")
st.title("🔊 Voice Biometrics")

# -------------------- Navigation --------------------
page = st.sidebar.radio("Navigation", ["Register", "Money Transfer"])
user_id = st.text_input("Enter Your User ID")

# -------------------- WebRTC Audio Processor --------------------
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        self.frames.append(frame.to_ndarray())
        return frame

# -------------------- Helper: Save Audio --------------------
def save_audio_frames(frames, filename, fs=16000):
    if frames:
        audio = np.concatenate(frames, axis=0).astype(np.int16)
        wav.write(filename, fs, audio)
        return filename
    else:
        return None

# -------------------- REGISTER --------------------
if page == "Register":
    st.subheader("📝 Register Your Voice")
    st.info(fake.sentence())

    if user_id:
        if "register_frames" not in st.session_state:
            st.session_state.register_frames = []

        ctx = webrtc_streamer(
            key=f"register-{user_id}",
            mode=WebRtcMode.SENDRECV,
            audio_processor_factory=AudioProcessor,
            media_stream_constraints={"audio": True, "video": False},
        )

        if ctx.audio_processor:
            st.info("🎙️ Recording... speak into your microphone.")

            if st.button("✅ Stop & Save Recording"):
                frames = ctx.audio_processor.frames
                filename = os.path.join(RECORDINGS_DIR, f"{user_id}.wav")
                saved_file = save_audio_frames(frames, filename)
                if saved_file:
                    st.success(f"🎧 Audio recorded and saved: {saved_file}")
                    st.audio(saved_file, format="audio/wav")

                    # Generate embedding and store in Pinecone
                    try:
                        index = init_pinecone()
                        embedding = audio_to_embedding_enhanced(saved_file)
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
                    st.error("❌ No audio frames captured. Please try again.")
    else:
        st.warning("⚠️ Please enter a User ID.")

# -------------------- MONEY TRANSFER --------------------
elif page == "Money Transfer":
    st.subheader("💸 Money Transfer with Voice Verification")

    recipient = st.selectbox("Send Money To", ["John", "Alice", "Bob", "Emily"])
    amount = st.number_input("Amount to Transfer ($)", min_value=1.0, step=1.0)
    note = st.text_input("Note (optional)", placeholder="e.g., for rent")
    phrase = fake.sentence()
    st.markdown(f"### 🗣 Please say this phrase:\n> **\"{phrase}\"**")

    if user_id:
        reference_file = os.path.join(RECORDINGS_DIR, f"{user_id}.wav")
        if os.path.exists(reference_file):
            if "transfer_frames" not in st.session_state:
                st.session_state.transfer_frames = []

            ctx = webrtc_streamer(
                key=f"transfer-{user_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                mode=WebRtcMode.SENDRECV,
                audio_processor_factory=AudioProcessor,
                media_stream_constraints={"audio": True, "video": False},
            )

            if ctx.audio_processor:
                st.info("🎙️ Recording... speak the phrase now.")

                if st.button("✅ Stop & Verify Recording"):
                    frames = ctx.audio_processor.frames
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    test_path = os.path.join(USER_INPUT, f"{user_id}_test_{timestamp}.wav")
                    saved_file = save_audio_frames(frames, test_path)
                    if saved_file:
                        st.success(f"🎧 Audio recorded and saved: {saved_file}")
                        st.audio(saved_file, format="audio/wav")

                        # Generate embedding and query Pinecone
                        try:
                            index = init_pinecone()
                            query_embedding = audio_to_embedding_enhanced(saved_file)
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
                        st.error("❌ No audio frames captured. Please try again.")
        else:
            st.error(f"🚫 No registered voice found for '{user_id}'.")
    else:
        st.warning("⚠️ Please enter a User ID.")
