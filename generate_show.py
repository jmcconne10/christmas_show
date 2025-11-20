#!/usr/bin/env python3
"""
Auto-generate light show YAML from an MP3 file using audio analysis.
Requires: librosa, numpy, pyyaml

Install with: pip3 install librosa numpy pyyaml
"""

import sys
import os
import librosa
import numpy as np
import yaml

# Available patterns from patterns.py
PATTERNS = [
    "sparkle",
    "wave_trees",
    "alternate_trees_and_bulbs",
    "blink_all",
    "chase_bulbs",
    "finale_flash"
]

# Pattern intensity levels (0=calm, 1=medium, 2=high energy)
PATTERN_INTENSITY = {
    "sparkle": 0,
    "wave_trees": 0,
    "alternate_trees_and_bulbs": 1,
    "blink_all": 2,
    "chase_bulbs": 1,
    "finale_flash": 2
}

def analyze_audio(audio_path):
    """
    Analyze audio file and return useful features:
    - tempo (BPM)
    - beat times
    - energy profile over time
    """
    print(f"Loading audio file: {audio_path}")
    y, sr = librosa.load(audio_path)
    duration = librosa.get_duration(y=y, sr=sr)
    
    print(f"Duration: {duration:.2f} seconds")
    print("Analyzing tempo and beats...")
    
    # Detect tempo and beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # Convert tempo to scalar if it's an array
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo.item())
    else:
        tempo = float(tempo)
    
    print(f"Detected tempo: {tempo:.1f} BPM")
    print(f"Found {len(beat_times)} beats")
    
    # Calculate energy over time (RMS)
    print("Calculating energy profile...")
    hop_length = 512
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    
    # Normalize energy to 0-1 range
    rms_norm = (rms - rms.min()) / (rms.max() - rms.min())
    
    return {
        'duration': duration,
        'tempo': tempo,
        'beat_times': beat_times,
        'energy': rms_norm,
        'energy_times': times,
        'sr': sr,
        'y': y
    }

def get_energy_at_time(analysis, t):
    """Get normalized energy level at a specific time."""
    idx = np.searchsorted(analysis['energy_times'], t)
    if idx >= len(analysis['energy']):
        idx = len(analysis['energy']) - 1
    return analysis['energy'][idx]

def select_pattern_for_energy(energy, prev_pattern=None):
    """
    Select a pattern based on energy level.
    Avoid repeating the same pattern consecutively.
    """
    if energy < 0.3:
        # Low energy - calm patterns
        candidates = ["sparkle", "wave_trees"]
    elif energy < 0.6:
        # Medium energy
        candidates = ["alternate_trees_and_bulbs", "chase_bulbs", "wave_trees"]
    else:
        # High energy
        candidates = ["blink_all", "alternate_trees_and_bulbs", "chase_bulbs"]
    
    # Remove previous pattern if possible to add variety
    if prev_pattern in candidates and len(candidates) > 1:
        candidates = [p for p in candidates if p != prev_pattern]
    
    return np.random.choice(candidates)

def get_pattern_options(pattern, tempo, energy):
    """
    Generate appropriate options for a pattern based on tempo and energy.
    """
    # Calculate interval based on tempo (60s / BPM = seconds per beat)
    beat_duration = 60.0 / tempo
    
    options = {}
    
    if pattern == "sparkle":
        # Faster sparkle for higher energy
        options['interval'] = float(max(0.06, 0.15 - (energy * 0.09)))
        options['on_fraction'] = float(min(0.8, 0.3 + (energy * 0.5)))
    
    elif pattern == "wave_trees":
        # Sync to beat
        options['step_interval'] = float(beat_duration / 2)
    
    elif pattern == "alternate_trees_and_bulbs":
        # Sync to beat
        options['interval'] = float(beat_duration / 2)
    
    elif pattern == "blink_all":
        # Sync to beat, faster for high energy
        options['interval'] = float(beat_duration / (2 if energy > 0.7 else 1.5))
    
    elif pattern == "chase_bulbs":
        # Faster chase for higher energy
        options['step_interval'] = float(beat_duration / 4)
    
    elif pattern == "finale_flash":
        # Rapid strobe
        options['interval'] = 0.10
    
    return options

def detect_sections(analysis, section_length=12.0):
    """
    Divide the song into sections based on energy changes.
    """
    duration = analysis['duration']
    sections = []
    
    # Start at 0
    current_time = 0.0
    prev_pattern = None
    
    while current_time < duration:
        # Calculate section end
        section_end = min(current_time + section_length, duration)
        
        # Get average energy for this section
        section_energy = get_energy_at_time(analysis, (current_time + section_end) / 2)
        
        # Select pattern
        pattern = select_pattern_for_energy(section_energy, prev_pattern)
        
        # Get pattern options
        options = get_pattern_options(pattern, analysis['tempo'], section_energy)
        
        sections.append({
            'start': round(current_time, 1),
            'end': round(section_end, 1),
            'pattern': str(pattern),  # Convert to plain string
            'options': options
        })
        
        prev_pattern = pattern
        current_time = section_end
    
    return sections

def detect_finale(analysis, finale_duration=15.0):
    """
    Detect if there's a high-energy finale and replace last sections.
    """
    duration = analysis['duration']
    finale_start = duration - finale_duration
    
    if finale_start < 0:
        return None
    
    # Check if final section has sustained high energy
    finale_times = analysis['energy_times'][analysis['energy_times'] >= finale_start]
    finale_energies = analysis['energy'][len(analysis['energy']) - len(finale_times):]
    
    avg_finale_energy = np.mean(finale_energies)
    
    # If finale is energetic enough, create special finale sections
    if avg_finale_energy > 0.65:
        return finale_start
    
    return None

def generate_show(audio_path, output_yaml, section_length=12.0):
    """
    Main function to generate a light show YAML from an audio file.
    """
    # Analyze audio
    analysis = analyze_audio(audio_path)
    
    # Generate sections
    print(f"Generating sections ({section_length}s each)...")
    sections = detect_sections(analysis, section_length=section_length)
    
    # Check for finale
    finale_start = detect_finale(analysis)
    if finale_start:
        print(f"Detected high-energy finale starting at {finale_start:.1f}s")
        # Remove sections that overlap with finale
        sections = [s for s in sections if s['end'] <= finale_start]
        
        # Add finale sections
        tempo = analysis['tempo']
        beat_duration = 60.0 / tempo
        
        # Build-up section
        sections.append({
            'start': round(finale_start, 1),
            'end': round(finale_start + 8.0, 1),
            'pattern': 'blink_all',
            'options': {'interval': float(beat_duration / 2)}
        })
        
        sections.append({
            'start': round(finale_start + 8.0, 1),
            'end': round(finale_start + 12.0, 1),
            'pattern': 'alternate_trees_and_bulbs',
            'options': {'interval': float(beat_duration / 3)}
        })
        
        # Final explosion
        sections.append({
            'start': round(analysis['duration'] - 5.0, 1),
            'end': round(analysis['duration'], 1),
            'pattern': 'finale_flash',
            'options': {'interval': 0.08}
        })
    
    # Create YAML structure
    audio_filename = os.path.basename(audio_path)
    show = {
        'file': audio_filename,
        'sections': sections
    }
    
    # Write to file
    print(f"Writing show to {output_yaml}...")
    with open(output_yaml, 'w') as f:
        # Add header comment
        f.write(f"# Auto-generated light show for {audio_filename}\n")
        f.write(f"# Duration: {analysis['duration']:.2f}s, Tempo: {analysis['tempo']:.1f} BPM\n")
        f.write(f"# Generated with {len(sections)} sections\n\n")
        yaml.dump(show, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Show generated successfully!")
    print(f"  Sections: {len(sections)}")
    print(f"  Total duration: {analysis['duration']:.2f}s")
    print(f"\nRun with: python3 show_runner.py {output_yaml}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_show.py <audio_file.mp3> [output.yaml] [section_length]")
        print("\nExamples:")
        print("  python3 generate_show.py sarajevo.mp3")
        print("  python3 generate_show.py sarajevo.mp3 my_show.yaml")
        print("  python3 generate_show.py sarajevo.mp3 my_show.yaml 10")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    # Default output name based on input
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base = os.path.splitext(os.path.basename(audio_file))[0]
        output_file = f"{base}_show.yaml"
    
    # Optional section length
    section_length = 12.0
    if len(sys.argv) >= 4:
        section_length = float(sys.argv[3])
    
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}")
        sys.exit(1)
    
    generate_show(audio_file, output_file, section_length=section_length)