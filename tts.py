from transformers import pipeline
import soundfile as sf
import numpy as np
import uuid
import os

class SimpleTTS:
    def __init__(self):
        try:
            print("Loading facebook/mms-tts-eng model...")
            self.pipe = pipeline("text-to-speech", model="facebook/mms-tts-eng", device=-1)  # CPU
            print("TTS model loaded!")
        except Exception as e:
            print(f"TTS init error: {e}")
            self.pipe = None

    def speak_to_file(self, text):
        if self.pipe is None or not text.strip():
            return None
        try:
            speech = self.pipe(text)
            audio_array = speech["audio"].squeeze()
            samplerate = speech["sampling_rate"]
            if np.max(np.abs(audio_array)) > 0:
                audio_array /= np.max(np.abs(audio_array)) * 0.9
            filename = f"tts_{uuid.uuid4().hex}.wav"
            sf.write(filename, audio_array, samplerate)
            print(f"Generated: {filename}")
            return filename
        except Exception as e:
            print(f"TTS error: {e}")
            return None

    # Deprecated for Streamlit (desktop only)
    def speak(self, text):
        filename = self.speak_to_file(text)
        if filename:
            print(f"Playing: {text}")
            # Use if running console: import simpleaudio as sa; wave = sa.WaveObject.from_wave_file(filename); play = wave.play(); play.wait_done()
            os.remove(filename)