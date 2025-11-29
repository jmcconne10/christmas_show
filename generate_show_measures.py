#!/usr/bin/env python3
"""
Auto-generate measure-based light show YAML from an MP3 file.
Outputs sections in measures instead of seconds for easier musical editing.
"""

import sys
import os
import librosa
import numpy as np
import yaml

# Available patterns
PATTERNS = [
    "sparkle",
    "wave_trees",
    "alternate_trees_and_bulbs",
    "blink_all",
    "chase_bulbs",
    "finale_flash"
]


def analyze_audio(audio_path):
    """Analyze audio file and return tempo, beats, energy, etc."""
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


def seconds_to_measures(seconds, bpm, beats_per_measure=4):
    """Convert seconds to measures."""
    beats = (seconds * bpm) / 60.0
    measures = beats / beats_per_measure
    return measures


def measures_to_seconds(measures, bpm, beats_per_measure=4):
    """Convert measures to seconds."""
    beats = measures * beats_per_measure
    seconds = (beats * 60.0) / bpm
    return seconds


def get_energy_at_time(analysis, t):
    """Get normalized energy level at a specific time."""
    idx = np.searchsorted(analysis['energy_times'], t)
    if idx >= len(analysis['energy']):
        idx = len(analysis['energy']) - 1
    return analysis['energy'][idx]


def select_pattern_for_energy(energy, prev_pattern=None):
    """Select a pattern based on energy level."""
    if energy < 0.3:
        candidates = ["sparkle", "wave_trees"]
    elif energy < 0.6:
        candidates = ["alternate_trees_and_bulbs", "chase_bulbs", "wave_trees"]
    else:
        candidates = ["blink_all", "alternate_trees_and_bulbs", "chase_bulbs"]
    
    if prev_pattern in candidates and len(candidates) > 1:
        candidates = [p for p in candidates if p != prev_pattern]
    
    return np.random.choice(candidates)


def get_pattern_options(pattern, tempo, energy):
    """Generate appropriate options for a pattern based on tempo and energy."""
    beat_duration = 60.0 / tempo
    options = {}
    
    if pattern == "sparkle":
        options['interval'] = float(max(0.06, 0.15 - (energy * 0.09)))
        options['on_fraction'] = float(min(0.8, 0.3 + (energy * 0.5)))
    elif pattern == "wave_trees":
        options['step_interval'] = float(beat_duration / 2)
    elif pattern == "alternate_trees_and_bulbs":
        options['interval'] = float(beat_duration / 2)
    elif pattern == "blink_all":
        options['interval'] = float(beat_duration / (2 if energy > 0.7 else 1.5))
    elif pattern == "chase_bulbs":
        options['step_interval'] = float(beat_duration / 4)
    elif pattern == "finale_flash":
        options['interval'] = 0.10
    
    return options


def detect_sections(analysis, section_measures=8, beats_per_measure=4):
    """
    Divide the song into sections based on measures.
    """
    duration = analysis['duration']
    tempo = analysis['tempo']
    
    sections = []
    current_measure = 0
    prev_pattern = None
    
    # Calculate total measures in song
    total_measures = int(seconds_to_measures(duration, tempo, beats_per_measure))
    
    while current_measure < total_measures:
        # Calculate section end
        end_measure = min(current_measure + section_measures, total_measures)
        
        # Convert to seconds for energy analysis
        current_time = measures_to_seconds(current_measure, tempo, beats_per_measure)
        end_time = measures_to_seconds(end_measure, tempo, beats_per_measure)
        
        # Get average energy for this section
        section_energy = get_energy_at_time(analysis, (current_time + end_time) / 2)
        
        # Select pattern
        pattern = select_pattern_for_energy(section_energy, prev_pattern)
        
        # Get pattern options
        options = get_pattern_options(pattern, tempo, section_energy)
        
        sections.append({
            'start_measure': int(current_measure),
            'end_measure': int(end_measure),
            'pattern': str(pattern),
            'options': options
        })
        
        prev_pattern = pattern
        current_measure = end_measure
    
    return sections


def detect_finale(analysis, finale_measures=32, beats_per_measure=4):
    """Detect if there's a high-energy finale."""
    duration = analysis['duration']
    tempo = analysis['tempo']
    
    finale_seconds = measures_to_seconds(finale_measures, tempo, beats_per_measure)
    finale_start_seconds = duration - finale_seconds
    
    if finale_start_seconds < 0:
        return None
    
    # Check if final section has sustained high energy
    finale_times = analysis['energy_times'][analysis['energy_times'] >= finale_start_seconds]
    finale_energies = analysis['energy'][len(analysis['energy']) - len(finale_times):]
    
    avg_finale_energy = np.mean(finale_energies)
    
    if avg_finale_energy > 0.65:
        finale_start_measure = int(seconds_to_measures(finale_start_seconds, tempo, beats_per_measure))
        return finale_start_measure
    
    return None


def generate_show(audio_path, output_yaml, section_measures=8, beats_per_measure=4):
    """Main function to generate a measure-based light show YAML."""
    # Analyze audio
    analysis = analyze_audio(audio_path)
    tempo = analysis['tempo']
    
    print(f"\nGenerating sections ({section_measures} measures each)...")
    print(f"Time signature: {beats_per_measure}/4")
    
    # Generate sections
    sections = detect_sections(analysis, section_measures, beats_per_measure)
    
    # Check for finale
    finale_start_measure = detect_finale(analysis, finale_measures=32, beats_per_measure=beats_per_measure)
    if finale_start_measure:
        total_measures = int(seconds_to_measures(analysis['duration'], tempo, beats_per_measure))
        print(f"Detected high-energy finale starting at measure {finale_start_measure}")
        
        # Remove sections that overlap with finale
        sections = [s for s in sections if s['end_measure'] <= finale_start_measure]
        
        # Add finale sections
        beat_duration = 60.0 / tempo
        
        # Build-up section (16 measures)
        sections.append({
            'start_measure': finale_start_measure,
            'end_measure': finale_start_measure + 16,
            'pattern': 'blink_all',
            'options': {'interval': float(beat_duration / 2)}
        })
        
        # Intense section (8 measures)
        sections.append({
            'start_measure': finale_start_measure + 16,
            'end_measure': finale_start_measure + 24,
            'pattern': 'alternate_trees_and_bulbs',
            'options': {'interval': float(beat_duration / 3)}
        })
        
        # Final explosion (remaining measures)
        sections.append({
            'start_measure': finale_start_measure + 24,
            'end_measure': total_measures,
            'pattern': 'finale_flash',
            'options': {'interval': 0.08}
        })
    
    # Create YAML structure
    audio_filename = os.path.basename(audio_path)
    total_measures = sections[-1]['end_measure'] if sections else 0
    
    show = {
        'file': audio_filename,
        'bpm': round(tempo, 1),
        'beats_per_measure': beats_per_measure,
        'sections': sections
    }
    
    # Write to file
    print(f"Writing show to {output_yaml}...")
    with open(output_yaml, 'w') as f:
        # Add header comment
        f.write(f"# Auto-generated light show for {audio_filename}\n")
        f.write(f"# Duration: {analysis['duration']:.2f}s, Tempo: {tempo:.1f} BPM\n")
        f.write(f"# Time signature: {beats_per_measure}/4\n")
        f.write(f"# Total measures: {total_measures}\n")
        f.write(f"# Generated with {len(sections)} sections\n\n")
        yaml.dump(show, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Show generated successfully!")
    print(f"  Sections: {len(sections)}")
    print(f"  Total measures: {total_measures}")
    print(f"  Duration: {analysis['duration']:.2f}s")
    print(f"\nRun with: python3 show_runner_measures.py {output_yaml}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_show_measures.py <audio_file.mp3> [output.yaml] [measures_per_section] [beats_per_measure]")
        print("\nExamples:")
        print("  python3 generate_show_measures.py sarajevo.mp3")
        print("  python3 generate_show_measures.py sarajevo.mp3 show.yaml 8")
        print("  python3 generate_show_measures.py sarajevo.mp3 show.yaml 8 4  # 8 measures per section, 4/4 time")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    # Default output name
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base = os.path.splitext(os.path.basename(audio_file))[0]
        output_file = f"{base}_show.yaml"
    
    # Section length in measures (default 8)
    section_measures = 8
    if len(sys.argv) >= 4:
        section_measures = int(sys.argv[3])
    
    # Beats per measure (default 4 for 4/4 time)
    beats_per_measure = 4
    if len(sys.argv) >= 5:
        beats_per_measure = int(sys.argv[4])
    
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}")
        sys.exit(1)
    
    generate_show(audio_file, output_file, section_measures, beats_per_measure)