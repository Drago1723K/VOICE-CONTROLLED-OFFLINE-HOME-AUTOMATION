import os
import queue
import sys
import json
import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer
import RPi.GPIO as GPIO
import time

# Path to your Vosk model
MODEL_PATH = "/usr/src/Python-3.9.18/vosk-model-small-en-us-0.15"

# GPIO pin setup
RELAY_PIN = 17  # Use GPIO17 for relay control
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setup(RELAY_PIN, GPIO.OUT)  # Set pin as output

# Load the Vosk model
if not os.path.exists(MODEL_PATH):
    print("Please download the model from https://alphacephei.com/vosk/models and unpack it.")
    exit(1)

print("Loading model...")
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

# Queue to store audio data
audio_queue = queue.Queue()

# Audio callback function
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Error: {status}", file=sys.stderr)
    audio_queue.put(np.frombuffer(indata, dtype=np.int16))

# Relay control function
def control_relay(command):
    if "turn on" in command:
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        print("Relay turned ON")
    elif "turn off" in command:
        GPIO.output(RELAY_PIN, GPIO.LOW)
        print("Relay turned OFF")
    else:
        print("Unknown command")

# Speech-to-text function
def speech_to_text():
    print("Listening...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                           channels=1, callback=audio_callback):
        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data.tobytes()):
                result = json.loads(recognizer.Result())
                recognized_text = result.get("text", "")
                print("Recognized Text:", recognized_text)
                
                # Control the relay based on recognized text
                control_relay(recognized_text)

# Run the function
if __name__ == "__main__":
    try:
        speech_to_text()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        GPIO.cleanup()  # Cleanup GPIO on exit
