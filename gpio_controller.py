#!/usr/bin/env python3

import yaml
from gpiozero import OutputDevice


class GPIOController:
    def __init__(self, map_file="channel_map.yaml"):
        # Load the mapping file
        with open(map_file, "r") as f:
            mapping = yaml.safe_load(f)

        self.channels = {}

        # Load trees
        for name, pin in mapping.get("trees", {}).items():
            self.channels[name] = OutputDevice(
                pin,
                active_high=True,
                initial_value=False
            )

        # Load bulbs
        for name, pin in mapping.get("bulbs", {}).items():
            self.channels[name] = OutputDevice(
                pin,
                active_high=True,
                initial_value=False
            )

    def on(self, name):
        """Turn a channel ON by name (e.g., 'T1')."""
        if name in self.channels:
            self.channels[name].on()

    def off(self, name):
        """Turn a channel OFF by name."""
        if name in self.channels:
            self.channels[name].off()

    def all_on(self):
        """Turn ALL channels on."""
        for dev in self.channels.values():
            dev.on()

    def all_off(self):
        """Turn ALL channels off."""
        for dev in self.channels.values():
            dev.off()

    def test_blink(self, duration=5, interval=0.5):
        """Blink each channel in sequence for testing."""
        import time
        names = list(self.channels.keys())
        end = time.time() + duration
        i = 0

        while time.time() < end:
            self.all_off()
            name = names[i % len(names)]
            print(f"ON: {name}")
            self.on(name)
            time.sleep(interval)
            i += 1

        self.all_off()
