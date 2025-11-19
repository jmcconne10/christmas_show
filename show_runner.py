#!/usr/bin/env python3

import time
import yaml
import pygame
from gpio_controller import GPIOController
import patterns


def load_show(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def play_song(song_file):
    pygame.mixer.init()
    pygame.mixer.music.load(song_file)
    pygame.mixer.music.play()
    return time.time()


def run_show(show):
    gpio = GPIOController()

    sections = show["sections"]
    audio_file = show["file"]

    print(f"Playing: {audio_file}")

    start_time = play_song(audio_file)

    try:
        for section in sections:
            pattern_name = section["pattern"]
            start = section["start"]
            end = section["end"]

            while time.time() - start_time < start:
                time.sleep(0.05)

            print(f"Running {pattern_name} from {start} to {end}")

            duration = end - start
            args = section.get("options", {})

            # Lookup pattern function dynamically
            pattern_func = getattr(patterns, pattern_name)
            pattern_func(gpio, duration=duration, **args)

        # Wait for music to end
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    finally:
        print("Show done. Turning everything off.")
        gpio.all_off()
