from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import time

class SimpleSTT:
    def __init__(self):
        print("Loading Whisper tiny.en model...")
        self.model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        print("Model loaded successfully!")

    def listen(self, max_duration=20, silence_timeout=1.8):
        fs = 16000
        chunk_duration = 0.3
        chunk_size = int(fs * chunk_duration)
        max_silence_chunks = int(silence_timeout / chunk_duration)
        audio_buffer = []
        silence_chunks = 0

        print("[DEBUG] Recording started. Speak now...")

        try:
            with sd.InputStream(
                samplerate=fs,
                channels=1,
                dtype='float32',
                blocksize=chunk_size
            ) as stream:
                start_time = time.time()
                while time.time() - start_time < max_duration:
                    chunk, overflowed = stream.read(chunk_size)
                    if overflowed:
                        print("[DEBUG] Overflow detected, skipping chunk")
                        continue

                    chunk = chunk.flatten()
                    audio_buffer.append(chunk)

                    energy = np.mean(np.abs(chunk))
                    print(f"[DEBUG] Energy level: {energy:.6f}")

                    if energy < 0.012:  # ← threshold thoda barhaya (low voice ke liye)
                        silence_chunks += 1
                        if silence_chunks >= max_silence_chunks:
                            print("[DEBUG] Silence detected, stopping recording")
                            break
                    else:
                        silence_chunks = 0

            if not audio_buffer:
                print("[DEBUG] No audio captured at all")
                return ""

            audio = np.concatenate(audio_buffer)
            print(f"[DEBUG] Audio captured: {len(audio)} samples")

            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.9

            segments, info = self.model.transcribe(
                audio,
                beam_size=5,
                language="en",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300, threshold=0.4)
            )

            text = " ".join([seg.text.strip() for seg in segments]).strip().lower()
            print(f"[DEBUG] Transcribed text: '{text}'")

            if len(text) < 3 or text in ["you", "yeah", "hi", "hello", "okay", "hmm", ""]:
                print("[DEBUG] Weak/empty transcription")
                return ""

            print(f"[SUCCESS] You said: {text}")
            return text

        except Exception as e:
            print(f"[ERROR] Recording failed: {str(e)}")
            return ""