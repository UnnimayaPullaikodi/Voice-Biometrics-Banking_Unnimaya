import os
import uuid
import torch
import torchaudio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import noisereduce as nr
from pydub import AudioSegment
from speechbrain.pretrained import EncoderClassifier
import pinecone
from typing import List, Union

# Constants
PINECONE_API_KEY = "pcsk_2yzKnb_DusX4M95CU1KTjQxkZFPdYWbtFghFc7kUD2cHzpUT4hWPLmMbPgEgT5NgoX3Fib"
PINECONE_ENV = "us-east-1"
INDEX_NAME = "voicebiometrics-forbanking"
EMBEDDING_DIM = 192
UPSERT_BATCH_SIZE = 100

# Initialize model
model = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb",
    run_opts={"skip_vad": True}
)

def convert_to_wav_universal(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith((".mp3", ".wav", ".m4a", ".flac")):
            input_path = os.path.join(input_folder, file_name)
            audio = AudioSegment.from_file(input_path)
            out_path = os.path.join(output_folder, os.path.splitext(file_name)[0] + ".wav")
            audio.export(out_path, format="wav")
            print(f"✔ Converted {file_name} to wav")

def audio_to_embedding_enhanced(audio_path):
    try:
        audio = AudioSegment.from_file(audio_path)
        normalized_audio = audio.apply_gain(-audio.dBFS)
        temp_path = audio_path.replace(".wav", "_normalized.wav")
        normalized_audio.export(temp_path, format="wav")

        waveform, sample_rate = torchaudio.load(temp_path)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)

        denoised = nr.reduce_noise(y=waveform.squeeze().numpy(), sr=16000)
        waveform = torch.tensor(denoised).unsqueeze(0)

        vad = torchaudio.transforms.Vad(sample_rate=16000)
        waveform = vad(waveform)

        if waveform.numel() == 0:
            raise ValueError("Empty VAD result.")

        waveform = waveform / waveform.abs().max()
        if waveform.shape[1] < 16000:
            waveform = torch.nn.functional.pad(waveform, (0, 16000 - waveform.shape[1]))

        waveform = waveform.unsqueeze(0).squeeze(1)
        embedding = model.encode_batch(waveform)
        os.remove(temp_path)
        return embedding.squeeze().numpy()

    except Exception as e:
        print(f"[❌ ERROR] {e}")
        return None

def init_pinecone():
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=pinecone.PodSpec(environment=PINECONE_ENV)
        )
    return pc.Index(INDEX_NAME)

def format_embeddings(vectors, ids, metadata_list=None):
    return [
        (ids[i], vectors[i].tolist(), metadata_list[i] if metadata_list else None)
        for i in range(len(vectors))
    ]

def batch_upsert(index, data, batch_size=10):
    for i in range(0, len(data), batch_size):
        index.upsert(vectors=data[i:i + batch_size])
        print(f"✅ Upserted batch {i // batch_size + 1}")

def process_audio_directory(input_folder, wav_folder, save_csv=True, upsert_to_pinecone=True, limit=None):
    convert_to_wav_universal(input_folder, wav_folder)
    embeddings, ids, metadata = [], [], []

    index = init_pinecone() if upsert_to_pinecone else None
    wav_files = [f for f in os.listdir(wav_folder) if f.endswith(".wav")]
    if limit:
        wav_files = wav_files[:limit]

    for file in wav_files:
        path = os.path.join(wav_folder, file)
        emb = audio_to_embedding_enhanced(path)
        if emb is not None:
            uid = str(uuid.uuid4())
            embeddings.append(emb)
            ids.append(uid)
            metadata.append({"file_name": file})
            print(f"🎧 Processed: {file}")

    if upsert_to_pinecone:
        formatted = format_embeddings(embeddings, ids, metadata)
        batch_upsert(index, formatted)

    if save_csv:
        df = pd.DataFrame(embeddings, index=ids)
        df.index.name = 'id'
        df.to_csv("embeddings.csv")

    return embeddings, ids, metadata

def similarity_search(audio_path: str, index, top_k: int = 5):
    query_embedding = audio_to_embedding_enhanced(audio_path)
    return index.query(vector=query_embedding.tolist(), top_k=top_k, include_metadata=True)


if __name__ == "__main__":
    embeddings, ids, metadata_list = process_audio_directory(
        input_folder="recordings_training",
        wav_folder="data/Convert2wav",
        save_csv=True,
        upsert_to_pinecone=True,
        limit=100
    )
