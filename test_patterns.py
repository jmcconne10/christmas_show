#!/usr/bin/env python3

import time
from gpio_controller import GPIOController
import patterns

def main():
    gpio = GPIOController()

    try:
        print("Test 1: blink_all")
        patterns.blink_all(gpio, duration=4.0, interval=0.5)
        time.sleep(1)

        print("Test 2: alternate_trees_and_bulbs")
        patterns.alternate_trees_and_bulbs(gpio, duration=6.0, interval=0.4)
        time.sleep(1)

        print("Test 3: wave_trees")
        patterns.wave_trees(gpio, duration=6.0, step_interval=0.25)
        time.sleep(1)

        print("Test 4: chase_bulbs")
        patterns.chase_bulbs(gpio, duration=6.0, step_interval=0.2)
        time.sleep(1)

        print("Test 5: sparkle")
        patterns.sparkle(gpio, duration=6.0, interval=0.08, on_fraction=0.5)
        time.sleep(1)

        print("Test 6: finale_flash")
        patterns.finale_flash(gpio, duration=3.0, interval=0.12)

    finally:
        print("All off, exiting.")
        gpio.all_off()

if __name__ == "__main__":
    main()
