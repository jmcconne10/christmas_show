#!/usr/bin/env python3
"""
Light Show Simulator - Visual development tool for light shows.
Uses the same YAML files as show_runner.py but displays lights on screen instead.
"""

import os
import sys
import time
import yaml
import pygame
from pygame import gfxdraw

# Color definitions
BG_COLOR = (20, 20, 30)
TREE_COLOR_ON = (255, 215, 0)  # Gold for tree lights
TREE_COLOR_OFF = (40, 35, 15)
BULB_COLOR_ON = {
    "B1": (255, 50, 50),    # Red
    "B2": (50, 255, 50),    # Green
    "B3": (50, 50, 255),    # Blue
    "B4": (255, 150, 50)    # Orange
}
BULB_COLOR_OFF = (30, 30, 30)
TEXT_COLOR = (200, 200, 200)
LABEL_COLOR = (150, 150, 150)

class SimulatorGPIO:
    """Mock GPIO controller that tracks state instead of controlling hardware."""
    
    def __init__(self):
        # Initialize all channels to OFF
        self.channels = {
            "T1": False,
            "T2": False,
            "T3": False,
            "BigTree": False,
            "B1": False,
            "B2": False,
            "B3": False,
            "B4": False
        }
    
    def on(self, name):
        """Turn a channel ON."""
        if name in self.channels:
            self.channels[name] = True
    
    def off(self, name):
        """Turn a channel OFF."""
        if name in self.channels:
            self.channels[name] = False
    
    def all_on(self):
        """Turn ALL channels on."""
        for name in self.channels:
            self.channels[name] = True
    
    def all_off(self):
        """Turn ALL channels off."""
        for name in self.channels:
            self.channels[name] = False


class LightVisualizer:
    """Pygame window that displays the current state of all lights."""
    
    def __init__(self, width=1000, height=700):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Christmas Light Show Simulator")
        
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Layout positions for lights
        self.tree_positions = {
            "T1": (200, 300),
            "T2": (350, 300),
            "T3": (500, 300),
            "BigTree": (700, 300)
        }
        
        self.bulb_positions = {
            "B1": (200, 500),
            "B2": (350, 500),
            "B3": (500, 500),
            "B4": (650, 500)
        }
        
        # Size definitions
        self.tree_sizes = {
            "T1": 60,
            "T2": 60,
            "T3": 60,
            "BigTree": 100
        }
        
        self.bulb_size = 70
        
        self.current_pattern = "Idle"
        self.current_time = 0.0
        self.song_duration = 0.0
    
    def draw_tree(self, pos, size, is_on, label):
        """Draw a Christmas tree shape."""
        x, y = pos
        color = TREE_COLOR_ON if is_on else TREE_COLOR_OFF
        
        # Draw triangle tree
        points = [
            (x, y - size),           # Top
            (x - size//2, y + size//3),  # Bottom left
            (x + size//2, y + size//3)   # Bottom right
        ]
        pygame.draw.polygon(self.screen, color, points)
        
        # Draw trunk
        trunk_width = size // 5
        trunk_height = size // 4
        trunk_rect = pygame.Rect(x - trunk_width//2, y + size//3, trunk_width, trunk_height)
        trunk_color = (101, 67, 33) if is_on else (40, 30, 20)
        pygame.draw.rect(self.screen, trunk_color, trunk_rect)
        
        # Add glow effect when on
        if is_on:
            glow_radius = size + 15
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*TREE_COLOR_ON, 30), (glow_radius, glow_radius), glow_radius)
            self.screen.blit(glow_surface, (x - glow_radius, y - glow_radius))
        
        # Label
        label_surface = self.small_font.render(label, True, LABEL_COLOR)
        label_rect = label_surface.get_rect(center=(x, y + size//2 + 40))
        self.screen.blit(label_surface, label_rect)
    
    def draw_bulb(self, pos, is_on, label, color_on):
        """Draw a large decorative bulb."""
        x, y = pos
        color = color_on if is_on else BULB_COLOR_OFF
        
        # Draw bulb circle
        pygame.draw.circle(self.screen, color, (x, y), self.bulb_size // 2)
        
        # Add glow effect when on
        if is_on:
            glow_radius = self.bulb_size
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*color_on, 50), (glow_radius, glow_radius), glow_radius)
            self.screen.blit(glow_surface, (x - glow_radius, y - glow_radius))
        
        # Draw base/socket
        base_rect = pygame.Rect(x - 8, y - self.bulb_size//2 - 15, 16, 15)
        base_color = (80, 80, 80) if is_on else (40, 40, 40)
        pygame.draw.rect(self.screen, base_color, base_rect)
        
        # Label
        label_surface = self.small_font.render(label, True, LABEL_COLOR)
        label_rect = label_surface.get_rect(center=(x, y + self.bulb_size//2 + 25))
        self.screen.blit(label_surface, label_rect)
    
    def draw_info_panel(self):
        """Draw information panel at the top."""
        # Title
        title = self.font.render("Light Show Simulator", True, TEXT_COLOR)
        self.screen.blit(title, (20, 20))
        
        # Current pattern
        pattern_text = f"Pattern: {self.current_pattern}"
        pattern_surface = self.small_font.render(pattern_text, True, TEXT_COLOR)
        self.screen.blit(pattern_surface, (20, 70))
        
        # Time display
        if self.song_duration > 0:
            time_text = f"Time: {self.current_time:.1f}s / {self.song_duration:.1f}s"
            time_surface = self.small_font.render(time_text, True, TEXT_COLOR)
            self.screen.blit(time_surface, (20, 100))
            
            # Progress bar
            bar_width = 400
            bar_height = 20
            bar_x = 20
            bar_y = 130
            
            # Background
            pygame.draw.rect(self.screen, (60, 60, 70), (bar_x, bar_y, bar_width, bar_height))
            
            # Progress
            progress = min(1.0, self.current_time / self.song_duration)
            progress_width = int(bar_width * progress)
            pygame.draw.rect(self.screen, (100, 200, 100), (bar_x, bar_y, progress_width, bar_height))
            
            # Border
            pygame.draw.rect(self.screen, TEXT_COLOR, (bar_x, bar_y, bar_width, bar_height), 2)
    
    def update(self, gpio, pattern_name="", elapsed_time=0.0, total_duration=0.0):
        """Update the display with current GPIO state."""
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False
        
        # Clear screen
        self.screen.fill(BG_COLOR)
        
        # Update info
        self.current_pattern = pattern_name
        self.current_time = elapsed_time
        self.song_duration = total_duration
        
        # Draw info panel
        self.draw_info_panel()
        
        # Draw section label
        section_label = self.font.render("Trees", True, TEXT_COLOR)
        self.screen.blit(section_label, (370, 220))
        
        bulb_label = self.font.render("Bulbs", True, TEXT_COLOR)
        self.screen.blit(bulb_label, (380, 420))
        
        # Draw all trees
        for name, pos in self.tree_positions.items():
            size = self.tree_sizes[name]
            is_on = gpio.channels.get(name, False)
            self.draw_tree(pos, size, is_on, name)
        
        # Draw all bulbs
        for name, pos in self.bulb_positions.items():
            is_on = gpio.channels.get(name, False)
            color = BULB_COLOR_ON[name]
            self.draw_bulb(pos, is_on, name, color)
        
        # Update display
        pygame.display.flip()
        return True


def load_show(file_path):
    """Load a YAML show file."""
    base_dir = os.path.dirname(os.path.abspath(file_path)) or "."
    with open(file_path, "r") as f:
        show = yaml.safe_load(f)
    return show, base_dir


def play_song(song_path):
    """Initialize pygame mixer and start playing the audio file."""
    if not os.path.exists(song_path):
        print(f"Warning: Audio file not found: {song_path}")
        print("Running without audio...")
        return None
    
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100)
    
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()
    return time.time()


def run_simulation(show, base_dir="."):
    """Run the light show simulation."""
    # Import patterns module
    try:
        import patterns
    except ImportError:
        print("Error: patterns.py not found in the current directory")
        sys.exit(1)
    
    # Create simulator GPIO and visualizer
    gpio = SimulatorGPIO()
    visualizer = LightVisualizer()
    
    sections = show["sections"]
    audio_file = show["file"]
    audio_path = os.path.join(base_dir, audio_file)
    
    # Calculate total duration
    total_duration = max(s["end"] for s in sections) if sections else 0
    
    print(f"Starting simulation for: {audio_file}")
    print(f"Total duration: {total_duration:.1f}s")
    print(f"Sections: {len(sections)}")
    print("\nPress ESC or Q to quit\n")
    
    # Start audio
    start_time = play_song(audio_path)
    if start_time is None:
        start_time = time.time()
    
    clock = pygame.time.Clock()
    running = True
    
    try:
        for section in sections:
            if not running:
                break
            
            pattern_name = section["pattern"]
            start = float(section["start"])
            end = float(section["end"])
            duration = end - start
            
            if duration <= 0:
                continue
            
            # Wait until it's time for this section
            while time.time() - start_time < start:
                if not visualizer.update(gpio, "Waiting...", time.time() - start_time, total_duration):
                    running = False
                    break
                clock.tick(60)  # 60 FPS
            
            if not running:
                break
            
            print(f"[{start:5.1f}–{end:5.1f}] Running pattern: {pattern_name}")
            
            # Get pattern function
            if not hasattr(patterns, pattern_name):
                print(f"WARNING: Pattern '{pattern_name}' not found. Skipping.")
                continue
            
            pattern_func = getattr(patterns, pattern_name)
            args = section.get("options", {})
            
            # Run pattern in a non-blocking way
            pattern_start = time.time()
            pattern_thread_done = False
            
            # We need to run the pattern alongside visualization
            # The pattern will control gpio state, visualizer will display it
            import threading
            
            def run_pattern():
                nonlocal pattern_thread_done
                pattern_func(gpio, duration=duration, **args)
                pattern_thread_done = True
            
            thread = threading.Thread(target=run_pattern, daemon=True)
            thread.start()
            
            # Update visualization while pattern runs
            while not pattern_thread_done and running:
                elapsed = time.time() - start_time
                if not visualizer.update(gpio, pattern_name, elapsed, total_duration):
                    running = False
                    break
                clock.tick(60)  # 60 FPS
            
            thread.join(timeout=0.1)
        
        # Wait for music to finish if still playing
        if running:
            while pygame.mixer.music.get_busy():
                elapsed = time.time() - start_time
                if not visualizer.update(gpio, "Finished", elapsed, total_duration):
                    break
                clock.tick(60)
    
    finally:
        print("\nSimulation complete. Closing...")
        gpio.all_off()
        try:
            pygame.mixer.music.stop()
        except:
            pass
        pygame.quit()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 show_simulator.py <show_yaml_file>")
        print("\nExample:")
        print("  python3 show_simulator.py songs/christmas_eve_show.yaml")
        sys.exit(1)
    
    show_file = sys.argv[1]
    
    if not os.path.exists(show_file):
        print(f"Error: Show file not found: {show_file}")
        sys.exit(1)
    
    print(f"Loading show from {show_file}...")
    show_config, base_dir = load_show(show_file)
    run_simulation(show_config, base_dir=base_dir)