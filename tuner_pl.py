import tkinter as tk
import sounddevice as sd
import numpy as np
import scipy.fftpack
import os
import serial
import pygame
import time

# Initialize pygame mixer
pygame.mixer.init()

# General settings
SAMPLE_FREQ = 44100  # sample frequency in Hz
WINDOW_SIZE = 44100  # window size of the DFT in samples
WINDOW_STEP = 21050  # step size of window
windowSamples = [0 for _ in range(WINDOW_SIZE)]

ser = serial.Serial('/dev/ttyUSB0', 115200)
# Noise threshold
NOISE_THRESHOLD = 11.0  # Set this threshold based on your environment and microphone

# Tuning settings
CONCERT_PITCH = 440
ALL_NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

# Define target frequencies and ranges for standard tuning (E2, A2, D3, G3, B3, e4) and their higher versions
TARGET_FREQUENCIES = [(82, 165), (110, 220), (147, 294), (196, 392), (247, 494), (330, 659)]
STRING_NAMES = ["E2/E3", "A2/A3", "D3/D4", "G3/G4", "B3/B4", "e4/e5"]
FREQUENCY_RANGES = [(75, 90, 150, 180), (100, 120, 200, 240), (140, 155, 280, 310), (180, 210, 370, 410), (230, 260, 460, 520), (310, 350, 620, 700)]
current_string = 0  # Start with the first string (E2/E3)

def find_closest_note(pitch):
    i = int(np.round(np.log2(pitch / CONCERT_PITCH) * 12))
    closest_note = ALL_NOTES[i % 12] + str(4 + (i + 9) // 12)
    closest_pitch = CONCERT_PITCH * 2 ** (i / 12)
    return closest_note, closest_pitch

def callback(indata, frames, time, status):
    global windowSamples, current_string
    if status:
        print(status)
    if any(indata):
        windowSamples = np.concatenate((windowSamples, indata[:, 0]))  # append new samples
        windowSamples = windowSamples[len(indata[:, 0]):]  # remove old samples
        magnitudeSpec = abs(scipy.fftpack.fft(windowSamples)[:len(windowSamples) // 2])

        for i in range(int(62 / (SAMPLE_FREQ / WINDOW_SIZE))):
            magnitudeSpec[i] = 0  # suppress mains hum

        # Apply noise threshold
        if np.max(magnitudeSpec) < NOISE_THRESHOLD:
            return  # Ignore this frame if below the noise threshold

        maxInd = np.argmax(magnitudeSpec)
        maxFreq = int(maxInd * (SAMPLE_FREQ / WINDOW_SIZE))  # Use integer part of the frequency
        closestNote, closestPitch = find_closest_note(maxFreq)

        # Update GUI with current string, tuning status, detected frequency, and target frequency
        update_gui(current_string, closestNote, maxFreq)

        target_freq1, target_freq2 = TARGET_FREQUENCIES[current_string]
        freq_range1_low, freq_range1_high, freq_range2_low, freq_range2_high = FREQUENCY_RANGES[current_string]

        # Check if detected frequency is within either acceptable range for the current string
        if (freq_range1_low <= maxFreq <= freq_range1_high) or (freq_range2_low <= maxFreq <= freq_range2_high):
            if (target_freq1 - 2 <= maxFreq <= target_freq1 + 2) or (target_freq2 - 2 <= maxFreq <= target_freq2 + 2):
                print(f"{STRING_NAMES[current_string]} string is in tune")
                ser.write(b'STOP\n')  # Stop adjustments via serial
                os.system('echo "Tuned" | festival --tts')  # Speak "Tuned" using festival
                update_gui_status("Tuned")
                # Play sound
                play_tuned_sound()
                # Move to the next string
                current_string += 1
                if current_string >= len(TARGET_FREQUENCIES):
                    print("All strings are tuned.")
                    ser.write(b'STOP\n')
                    raise sd.CallbackStop()
            else:
                if maxFreq < target_freq1 - 1 or maxFreq < target_freq2 - 1:
                    print(f"{STRING_NAMES[current_string]} string: Increase tension")
                    ser.write(b'0')
                    
                    update_gui_status("Adjusting tension")
                elif maxFreq > target_freq1 + 1 or maxFreq > target_freq2 + 1:
                    print(f"{STRING_NAMES[current_string]} string: Decrease tension")
                    ser.write(b'1')
                    2
                   
                    update_gui_status("Adjusting tension")
        else:
            ser.write(b'0')
            update_gui_status("Out of range, adjust manually")
            print(f"{STRING_NAMES[current_string]} string: Detected frequency {maxFreq} Hz is out of range. Please adjust manually.")

    else:
        print('no input')

def update_gui(string_index, closest_note, detected_freq):
    target_freq1, target_freq2 = TARGET_FREQUENCIES[string_index]
    target_freq_text = f"Target Frequency: {target_freq1}/{target_freq2} Hz"
    
    string_label.config(text=f"String: {STRING_NAMES[string_index]}", font=("Arial", 36), pady=20, anchor='center')
    note_label.config(text=f"Closest Note: {closest_note}", font=("Arial", 36), pady=20, anchor='center')
    freq_label.config(text=f"Detected Frequency: {detected_freq} Hz\n{target_freq_text}", font=("Arial", 36), pady=20, anchor='center')

def update_gui_status(status_text):
    status_label.config(text=status_text, font=("Arial", 24), pady=10, anchor='center')

def play_tuned_sound():
    pygame.mixer.music.load('tunessh.mp3')
    pygame.mixer.music.play()

# GUI setup
root = tk.Tk()
root.title("Guitar Tuner")
root.attributes('-fullscreen', True)  # Fullscreen mode

# Create a frame to hold the labels
frame = tk.Frame(root)
frame.pack(expand=True, fill='both')  # Expand to fill the entire window

string_label = tk.Label(frame, text="String: ", font=("Arial", 36), pady=20, anchor='center')
string_label.pack(expand=True, fill='both')

note_label = tk.Label(frame, text="Closest Note: ", font=("Arial", 36), pady=20, anchor='center')
note_label.pack(expand=True, fill='both')

freq_label = tk.Label(frame, text="Detected Frequency: ", font=("Arial", 36), pady=20, anchor='center')
freq_label.pack(expand=True, fill='both')

status_label = tk.Label(frame, text="", font=("Arial", 24), pady=10, anchor='center')
status_label.pack(expand=True, fill='both')

# Start the microphone input stream
try:
    with sd.InputStream(channels=1, callback=callback, blocksize=WINDOW_STEP, samplerate=SAMPLE_FREQ):
        root.mainloop()
except Exception as e:
    print(str(e))
