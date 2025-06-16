# batch_converter.py

import os
from pydub import AudioSegment

def convert_folder_to_wav(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(('.mp3', '.m4a', '.aac', '.ogg', '.flac', '.wav')):
            continue

        input_path = os.path.join(input_folder, filename)
        output_filename = os.path.splitext(filename)[0] + ".wav"
        output_path = os.path.join(output_folder, output_filename)

        try:
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format="wav")
        except Exception as e:
            print(f"Error converting {filename}: {e}")
