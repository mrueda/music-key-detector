#!/usr/bin/env python3
#
# Music Key Detection Script
# Author: Manuel Rueda, PhD (2024)
# License: MIT License

import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal.windows import hann
from pydub import AudioSegment
import os
import matplotlib.pyplot as plt
import sys
import argparse

# Define scales
CHROMATIC_SCALE = ['C', 'C#', 'D', 'D#', 'E', 'F',
                  'F#', 'G', 'G#', 'A', 'A#', 'B']
SCALES = {
    "Major": [2, 2, 1, 2, 2, 2, 1],
    "Natural Minor": [2, 1, 2, 2, 1, 2, 2],
    "Harmonic Minor": [2, 1, 2, 2, 1, 3, 1],
    "Melodic Minor": [2, 1, 2, 2, 2, 2, 1],
    "Dorian": [2, 1, 2, 2, 2, 1, 2],
    "Phrygian": [1, 2, 2, 2, 1, 2, 2],
    "Lydian": [2, 2, 2, 1, 2, 2, 1],
    "Mixolydian": [2, 2, 1, 2, 2, 1, 2],
    "Locrian": [1, 2, 2, 1, 2, 2, 2]
}

# Define which scales are considered keys and which are modes
KEY_SCALES = ["Major", "Natural Minor", "Harmonic Minor", "Melodic Minor"]
MODE_SCALES = ["Dorian", "Phrygian", "Lydian", "Mixolydian", "Locrian"]

# Generate scale profiles
def generate_scale(root, intervals):
    scale = [root]
    index = CHROMATIC_SCALE.index(root)
    for step in intervals:
        index = (index + step) % len(CHROMATIC_SCALE)
        scale.append(CHROMATIC_SCALE[index])
    return scale

def pitch_class_profile(scale):
    df = pd.DataFrame({'Note': CHROMATIC_SCALE, 'Value': np.zeros(12)})
    for note in scale:
        df.loc[df['Note'] == note, 'Value'] = 1
    return df['Value'].values / df['Value'].sum()

# Generate profiles for all scales
scale_profiles = {
    scale_name: [pitch_class_profile(generate_scale(note, intervals))
                for note in CHROMATIC_SCALE]
    for scale_name, intervals in SCALES.items()
}

# Function to convert MP3 or other formats to WAV
def convert_to_wav(input_file):
    audio = AudioSegment.from_file(input_file)
    output_file = "temp_audio.wav"
    audio.export(output_file, format="wav")
    return output_file

# Ensure the audio file exists and is valid
def load_audio(file_path):
    if file_path.endswith(".mp3") or file_path.endswith(".ogg"):
        file_path = convert_to_wav(file_path)
    sample_rate, data = wavfile.read(file_path)
    if len(data.shape) > 1:
        data = data[:, 0]  # Use the first channel for stereo audio
    # Avoid division by zero
    if np.max(np.abs(data)) == 0:
        return sample_rate, data
    data = data / np.max(np.abs(data))  # Normalize audio
    return sample_rate, data

# Plot the FFT magnitude spectrum with notes on a secondary axis
def plot_fft_with_note_axis(frequencies, magnitude, plot_name):
    plt.figure(figsize=(12, 7))
    plt.plot(frequencies, magnitude, color='blue', label='FFT Magnitude')
    plt.title('FFT Magnitude Spectrum with Notes')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.grid(True)

    # Map frequencies to notes for the secondary axis
    displayed_notes = []
    for freq in frequencies:
        if 20 <= freq <= 20000:  # Only process within a musical range
            midi = 69 + 12 * np.log2(freq / 440.0)
            pitch_class = int(round(midi)) % 12
            note = CHROMATIC_SCALE[pitch_class]
            if not displayed_notes or freq - displayed_notes[-1][0] > 1000:
                displayed_notes.append((freq, note))

    # Add a secondary axis with spaced notes
    ax = plt.gca()
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks([item[0] for item in displayed_notes])
    ax2.set_xticklabels([item[1] for item in displayed_notes], fontsize=10, rotation=45)
    ax2.set_xlabel('Notes')

    if plot_name:
        plt.savefig(plot_name)
        print(f"Plot saved as {plot_name}")
    else:
        plt.show()

# Map FFT magnitudes to pitch classes
def compute_pitch_class_profile(frequencies, magnitude):
    pitch_class_profile = np.zeros(12)
    for i, freq in enumerate(frequencies):
        if 20 <= freq <= 5000:
            midi = 69 + 12 * np.log2(freq / 440.0)
            pitch_class = int(round(midi)) % 12
            pitch_class_profile[pitch_class] += magnitude[i]
    # Avoid division by zero
    total = np.sum(pitch_class_profile)
    if total == 0:
        return pitch_class_profile
    return pitch_class_profile / total

# Parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Detect the musical key or mode of an audio file.")
    parser.add_argument('audio_file', type=str, help='Path to the input audio file (WAV, MP3, OGG).')
    parser.add_argument('--plot', type=str, default=None, help='Optional: Path to save the FFT plot image.')
    parser.add_argument('--show-scores', action='store_true',
                        help='Optional: If set, print all key and mode scores sorted by score.')
    return parser.parse_args()

# Main function
def main():
    args = parse_arguments()
    
    audio_file = args.audio_file
    plot_name = args.plot
    show_scores = args.show_scores
    
    if not os.path.exists(audio_file):
        print(f"Error: '{audio_file}' not found.")
        sys.exit(1)
    
    # Load the audio file
    sample_rate, data = load_audio(audio_file)
    
    # FFT parameters
    window_size = 4096
    step_size = 2048  # Overlap of 50%
    hanning_window = hann(window_size, sym=False)
    
    # Compute FFT from the audio
    frequencies = np.fft.rfftfreq(window_size, d=1 / sample_rate)
    magnitude = np.zeros(len(frequencies))
    
    for start in range(0, len(data) - window_size, step_size):
        segment = data[start:start + window_size] * hanning_window
        fft = np.fft.rfft(segment)
        magnitude += np.abs(fft)
    
    # Average the magnitude
    num_windows = (len(data) - window_size) // step_size
    if num_windows > 0:
        magnitude /= num_windows
    else:
        print("Warning: Not enough data for FFT.")
    
    # Plot FFT if requested
    plot_fft_with_note_axis(frequencies, magnitude, plot_name)
    
    # Compute Pitch Class Profile (PCP)
    pcp_accum = compute_pitch_class_profile(frequencies, magnitude)
    
    # Scale detection
    if pcp_accum.max() > 0.4:  # Single-tone threshold
        detected_note = CHROMATIC_SCALE[np.argmax(pcp_accum)]
        print(f"Detected Key: {detected_note} (Single Tone)")
    else:
        key_scores = []
        for scale_name, profiles in scale_profiles.items():
            for i, profile in enumerate(profiles):
                score = np.sum(pcp_accum * profile)
                key_scores.append((CHROMATIC_SCALE[i], scale_name, score))
        
        # Sort scores: first by score descending, then by chromatic order ascending
        key_scores_sorted = sorted(
            key_scores,
            key=lambda x: (-x[2], CHROMATIC_SCALE.index(x[0]))
        )
        
        if show_scores:
            print("\nScores for all keys and modes:")
            for root, scale_name, score in key_scores_sorted:
                scale_type = "Key" if scale_name in KEY_SCALES else "Mode"
                print(f"{scale_type}: {root} {scale_name} - Score: {score:.4f}")
        
        # The best key or mode (handling ties by chromatic order)
        best_key = key_scores_sorted[0]
        scale_type = "Key" if best_key[1] in KEY_SCALES else "Mode"
        print(f"\nDetected {scale_type}: {best_key[0]} {best_key[1]}")

if __name__ == "__main__":
    main()
