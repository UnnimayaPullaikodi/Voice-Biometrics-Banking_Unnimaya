import streamlit as st
import sounddevice as sd
import scipy.io.wavfile as wav
import os
import datetime
from voice_verification import verify_user_voice

# --------- Setup ---------
RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)
USER_INPUT = "user_input"
os.makedirs(USER_INPUT, exist_ok=True)

st.set_page_config(page_title="Voice Biometrics", layout="centered")
st.title("🔊 Voice Biometrics ")

# Navigation
page = st.sidebar.radio("Navigation", ["Register", "Money Transfer"])

# --------- Voice Recording Function ---------
def record_audio(duration=5, fs=16000):
    st.info(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    st.success("Recording complete.")
    return audio, fs

# --------- Save Audio Function ---------
def save_audio(audio, fs, filename):
    wav.write(filename, fs, audio)
    st.success(f"Audio saved: {filename}")

# --------- Check if User ID Already Exists ---------
def is_user_id_taken(user_id):
    """Check if a user ID already exists in the recordings directory"""
    audio_path = os.path.join(RECORDINGS_DIR, f"{user_id}.wav")
    return os.path.exists(audio_path)

# --------- Get List of Registered Users ---------
def get_registered_users():
    """Get list of all registered user IDs"""
    users = []
    if os.path.exists(RECORDINGS_DIR):
        for file in os.listdir(RECORDINGS_DIR):
            if file.endswith('.wav'):
                user_id = file.replace('.wav', '')
                users.append(user_id)
    return users

# --------- Register Page ---------
if page == "Register":
    st.subheader("📋 Register New User")
    
    # Show existing users (optional - for reference)
    existing_users = get_registered_users()
    # if existing_users:
    #     st.info(f"📝 Existing users: {', '.join(existing_users)}")
    
    user_id = st.text_input("Enter a Unique User ID")

    if user_id:
        # Check if user ID already exists
        if is_user_id_taken(user_id):
            st.error(f"❌ User ID '{user_id}' is already taken. Please choose a different username.")
        else:
            st.success(f"✅ User ID '{user_id}' is available!")
            
            if st.button("Record Voice Sample"):
                audio, fs = record_audio()
                audio_path = os.path.join(RECORDINGS_DIR, f"{user_id}.wav")
                save_audio(audio, fs, audio_path)
                st.audio(audio_path, format='audio/wav')
                st.success(f"✅ User '{user_id}' registered successfully!")
    else:
        st.warning("Please enter a User ID before recording.")

# --------- Money Transfer Page ---------
elif page == "Money Transfer":
    st.subheader("💸 Money Transfer with Voice Verification")

    user_id = st.text_input("Enter Your User ID")
    recipient = st.selectbox("Send Money To", ["John", "Alice", "Bob", "Emily"])
    amount = st.number_input("Amount to Transfer ($)", min_value=1.0, step=1.0)
    note = st.text_input("Note (optional)", placeholder="e.g., for rent")

    phrase = f"Transfer ${int(amount)} to {recipient}"
    st.markdown(f"### 🗣 Please say this phrase:\n> **\"{phrase}\"**")

    if user_id and st.button("Record & Verify"):
        # Check if reference voice sample exists
        reference_file = os.path.join(RECORDINGS_DIR, f"{user_id}.wav")

        if os.path.exists(reference_file):
            # Proceed to record
            audio, fs = record_audio()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            user_audio_path = os.path.join(USER_INPUT, f"{user_id}_transfer_{timestamp}.wav")
            save_audio(audio, fs, user_audio_path)
            st.audio(user_audio_path, format='audio/wav')

            st.info("🔍 Verifying voice...")

            try:
                verified = verify_user_voice(reference_file, user_audio_path)
            except Exception as e:
                st.error(f"❌ Verification error: {e}")
                verified = False

            if verified:
                st.success(f"✅ Voice verified. ${int(amount)} sent to {recipient}.")
                st.balloons()
            else:
                st.error("❌ Voice mismatch. Transaction blocked.")
        else:
            st.error(f"🚫 No registered voice found for '{user_id}'. Please register first.")
