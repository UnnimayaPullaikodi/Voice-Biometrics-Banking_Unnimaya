# Voice-Biometrics-Banking
Capstone Project - Real-Time Voice Biometrics System for Secure Banking Authentication
Course Code: AML 3406 | Section 1  
Team Name: Group C  
Faculty Supervisor: William Pourmajidi

##Team Members

- Pallavi Sathyanarayana – C0935830  
- Shihana Binumon – C0891803  
- Unnimaya Pullaikodi – C0936758  
- Uma Varadaraj – C0935831

---

##Project Overview

This project aims to develop a real-time **Voice Biometric System** for secure banking authentication, combining:

- Speaker Verification** (to verify the identity of the user)
- Anti-Spoofing Detection** (to prevent voice playback and synthetic attacks)

---

##Key Features

- ECAPA-TDNN (Speaker verification)
- CNN/LSTM (Spoof detection)
- Datasets: VoxCeleb, ASVspoof 2019
- FastAPI + Flask for backend
- Optional: Streamlit frontend / Twilio integration

---

## Minimum Viable Product (MVP)

1. Speaker verification using ECAPA-TDNN on VoxCeleb
2. Basic spoof detection pipeline using ASVspoof data
3. Flask interface for voice input and results
4. Evaluation metrics: EER, accuracy, precision, recall

---

## Tools & Tech Stack

- Python 3.10+
- PyTorch, SpeechBrain
- Librosa, NumPy, Scikit-learn
- Flask / Streamlit / FastAPI
- Docker (for containerization)
- GitHub + Zenhub (for project management)

---

## Folder Structure

