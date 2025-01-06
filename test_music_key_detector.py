import unittest
import os
from subprocess import run, PIPE

class TestMusicKeyDetector(unittest.TestCase):
    def setUp(self):
        # Directory containing test WAV files
        self.tones_dir = "wavs/tones"
        self.scales_dir = "wavs/scales"
        self.script = "music_key_detector.py"  # Path to your detector script

        # Ensure directories and test files exist
        if not os.path.exists(self.tones_dir) or not os.path.exists(self.scales_dir):
            self.fail("Test WAV files are missing. Please generate them first.")

    # Normalize the output by stripping whitespace and removing newlines
    def run_detector(self, file_path):
        """Run the music_key_detector script on a file and return the detected key or mode."""
    
        command = ['python3', self.script, file_path, '--plot', 'file.png']
        result = run(command, stdout=PIPE, stderr=PIPE, text=True)
        if result.returncode != 0:
            self.fail(f"Detector script failed with error: {result.stderr}")
        
        # Look for either 'Detected Key:' or 'Detected Mode:' in the output
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if "Detected Key:" in line or "Detected Mode:" in line:
                return line.strip()
        
        self.fail("No 'Detected Key:' or 'Detected Mode:' line found in script output.")
    
    def test_single_tones(self):
        """Test key detection for isolated tones."""
        expected_results = {
            "A#.wav": "Detected Key: A# (Single Tone)",
            "G#.wav": "Detected Key: G# (Single Tone)",
            "C#.wav": "Detected Key: C# (Single Tone)",
            "D.wav": "Detected Key: D (Single Tone)",
            "F#.wav": "Detected Key: F# (Single Tone)",
            "G.wav": "Detected Key: G (Single Tone)",
            "A.wav": "Detected Key: A (Single Tone)",
            "B.wav": "Detected Key: B (Single Tone)",
            "F.wav": "Detected Key: F (Single Tone)",
            "E.wav": "Detected Key: E (Single Tone)",
            "C.wav": "Detected Key: C (Single Tone)",
            "D#.wav": "Detected Key: D# (Single Tone)",
        }
        for note_file, expected_output in expected_results.items():
            with self.subTest(note=note_file):
                file_path = os.path.join(self.tones_dir, note_file)
                detected_output = self.run_detector(file_path)
                self.assertEqual(detected_output, expected_output, 
                                 f"Output for {note_file} was {detected_output}, expected {expected_output}.")

    def test_keys_and_modes(self):
        """Test key detection for keys."""
        expected_results = {
            # Keys
            "C_Major.wav": "Detected Key: C Major",
            "C_Natural Minor.wav": "Detected Key: C Natural Minor",
            "C_Harmonic Minor.wav": "Detected Key: C Harmonic Minor",
            "C_Melodic Minor.wav": "Detected Key: C Melodic Minor",
            # Modes
            "C_Dorian.wav": "Detected Mode: C Dorian",
            "C_Phrygian.wav": "Detected Mode: C Phrygian",
            "C_Lydian.wav": "Detected Mode: C Lydian",
            "C_Mixolydian.wav": "Detected Mode: C Mixolydian",
            "C_Locrian.wav": "Detected Mode: C Locrian"
        }
        for scale_file, expected_output in expected_results.items():
            with self.subTest(key=scale_file):
                file_path = os.path.join(self.scales_dir, scale_file)
                detected_output = self.run_detector(file_path)
                self.assertEqual(
                    detected_output, 
                    expected_output, 
                    f"Output for {scale_file} was {detected_output}, expected {expected_output}."
                )

if __name__ == "__main__":
    unittest.main()
