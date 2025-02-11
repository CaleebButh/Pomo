import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import math
import pygame
import os

from datetime import datetime, timedelta

class PomoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("POMO")
        self.root.geometry("400x525")
        
        # Color scheme
        self.bg_color = "#004d4d"  # Dark teal
        self.fg_color = "#ffffff"  # White
        self.accent_color = "#006666"  # Slightly lighter teal for hover effects
        
        # Configure root window background
        self.root.configure(bg=self.bg_color)
        
        # Custom button style
        self.style = ttk.Style()
        self.style.configure(
            "Custom.TButton",
            background=self.bg_color,
            foreground=self.fg_color,
            borderwidth=2,
            relief="flat",
            padding=5,
            font=("Arial", 14)
        )
        
        # Configure the button colors properly
        self.style.map(
            "Custom.TButton",
            background=[("active", self.accent_color), ("!active", self.bg_color)],
            foreground=[("active", self.fg_color), ("!active", self.fg_color)],
            bordercolor=[("active", self.fg_color), ("!active", self.fg_color)]
        )
        
        # Configure specific button elements
        self.style.layout("Custom.TButton", [
            ("Button.padding", {
                "children": [
                    ("Button.label", {"sticky": "nswe"})
                ],
                "sticky": "nswe"
            })
        ])
        
        # Configure colors for specific button elements
        self.style.configure(
            "Custom.TButton",
            background=self.bg_color,
            foreground=self.fg_color,
            borderwidth=1,
            bordercolor=self.fg_color,
            lightcolor=self.fg_color,
            darkcolor=self.fg_color,
            focuscolor=self.accent_color
        )
        
        # Initialize pygame mixer for sounds
        pygame.mixer.init()
        
        # Get current working directory and construct absolute paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tickPath = os.path.join(current_dir, "assets", "tick.wav")
        notificationPath = os.path.join(current_dir, "assets", "notification.wav")
        
        # Debug prints
        print(f"Current directory: {current_dir}")
        print(f"Looking for tick sound at: {tickPath}")
        print(f"Looking for notification sound at: {notificationPath}")
        
        # Load sounds
        try:
            if not os.path.exists(tickPath):
                print(f"Tick sound file does not exist at: {tickPath}")
            if not os.path.exists(notificationPath):
                print(f"Notification sound file does not exist at: {notificationPath}")
                
            self.tick_sound = pygame.mixer.Sound(tickPath)
            self.notification_sound = pygame.mixer.Sound(notificationPath)
            print("Sound files loaded successfully!")
            
        except Exception as e:
            print(f"Error loading sound files: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            # Initialize with None so the app can still run without sounds
            self.tick_sound = None
            self.notification_sound = None
        
        # State variables
        self.timer_duration = 25 * 60  # 25 minutes in seconds
        self.time_remaining = 0
        self.is_running = False
        self.is_rest_period = False
        self.total_focus_time = 0
        self.rest_periods = 0
        self.drag_start = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Logo
        logo_label = tk.Label(
            self.root,
            text="POMO",
            font=("Arial", 24, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        logo_label.pack(pady=20)

        # Help icon in top right
        help_frame = tk.Frame(self.root, bg=self.bg_color)
        help_frame.place(relx=0.95, rely=0.02, anchor="ne")
        
        help_button = ttk.Button(
            help_frame,
            text="?",
            command=self.show_help,
            style="Custom.TButton",
            width=2
        )
        help_button.pack()
        
        # Timer canvas
        self.canvas = tk.Canvas(
            self.root,
            width=300,
            height=300,
            bg=self.bg_color,
            highlightthickness=0  # Remove canvas border
        )
        self.canvas.pack(pady=20)
        
        # Draw timer circle
        self.draw_timer()
        
        # Add label below the timer circle
        self.drag_label = tk.Label(
            self.root,
            text="Drag to change time",
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.fg_color
        )
        self.drag_label.pack(pady=1)
        
        # Buttons frame
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(pady=20)
        
        self.begin_button = ttk.Button(
            button_frame,
            text="Begin",
            command=self.start_timer,
            style="Custom.TButton"
        )
        self.begin_button.pack(side=tk.LEFT, padx=10)
        
        self.end_button = ttk.Button(
            button_frame,
            text="End",
            command=self.end_session,
            style="Custom.TButton"
        )
        self.end_button.pack(side=tk.LEFT, padx=10)
        
        # Bind mouse events for timer adjustment
        self.canvas.bind("<Button-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_end)
    
    def draw_timer(self):
        self.canvas.delete("all")
        
        # Draw outer circle
        self.canvas.create_oval(
            10, 10, 290, 290,
            width=2,
            outline=self.fg_color
        )
        
        # Draw timer arc
        angle = (self.timer_duration / (60 * 60)) * 360
        self.canvas.create_arc(
            10, 10, 290, 290,
            start=90,
            extent=-angle,
            fill=self.accent_color,
            outline=self.fg_color
        )
        
        # Draw time text
        minutes = self.timer_duration // 60
        self.canvas.create_text(
            150, 150,
            text=f"{minutes} minutes",
            font=("Arial", 20),
            fill=self.fg_color
        )

    def on_drag_start(self, event):
        self.drag_start = (event.x, event.y)

    def on_drag(self, event):
        if self.drag_start:
            center_x, center_y = 150, 150
            angle = math.degrees(math.atan2(event.y - center_y, event.x - center_x))
            
            # Convert angle to minutes (0 to 60)
            minutes = int(((angle + 90) % 360) / 6)
            if minutes < 1:
                minutes = 1
            elif minutes >= 60:
                minutes = 60
            
            old_duration = self.timer_duration
            self.timer_duration = minutes * 60
            
            # Play tick sound if minute value changed
            if abs(old_duration - self.timer_duration) >= 60:
                try:
                    self.tick_sound.play()
                except:
                    pass
            
            self.draw_timer()

    def on_drag_end(self, event):
        self.drag_start = None

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.time_remaining = self.timer_duration
            self.begin_button.configure(state="disabled")
            self.update_timer()

    def update_timer(self):
        if self.is_running and self.time_remaining > 0:
            self.time_remaining -= 1
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_oval(
                10, 10, 290, 290,
                width=2,
                outline=self.fg_color
            )
            angle = (self.time_remaining / self.timer_duration) * 360
            self.canvas.create_arc(
                10, 10, 290, 290,
                start=90,
                extent=-angle,
                fill=self.accent_color,
                outline=self.fg_color
            )
            self.canvas.create_text(
                150, 150,
                text=f"{minutes}:{seconds:02d}",
                font=("Arial", 20),
                fill=self.fg_color
            )
            
            self.root.after(1000, self.update_timer)
        elif self.is_running:
            self.start_rest_period()

    def start_rest_period(self):
        self.is_rest_period = True
        self.total_focus_time += self.timer_duration
        self.time_remaining = 15 * 60  # 15 minutes rest
        try:
            self.notification_sound.play()
        except:
            pass
        
        self.update_rest_timer()

    def update_rest_timer(self):
        if self.is_rest_period and self.time_remaining > 0:
            self.time_remaining -= 1
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            
            self.canvas.delete("all")
            self.canvas.create_oval(
                10, 10, 290, 290,
                width=2,
                outline=self.fg_color
            )
            self.canvas.create_text(
                150, 150,
                text=f"Rest\n{minutes}:{seconds:02d}",
                font=("Arial", 20),
                fill=self.fg_color
            )
            
            self.root.after(1000, self.update_rest_timer)
        elif self.is_rest_period:
            self.rest_periods += 1
            self.is_rest_period = False
            self.is_running = False
            self.begin_button.configure(state="normal")
            try:
                self.notification_sound.play()
            except:
                pass
            self.draw_timer()

    def end_session(self):
        if self.is_running or self.is_rest_period:
            self.show_summary()
        self.is_running = False
        self.is_rest_period = False
        self.begin_button.configure(state="normal")
        self.draw_timer()

    def show_summary(self):
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Session Summary")
        summary_window.geometry("300x200")
        summary_window.configure(bg=self.bg_color)
        
        total_minutes = self.total_focus_time // 60
        
        tk.Label(
            summary_window,
            text="Session Summary",
            font=("Arial", 16, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(pady=20)
        
        tk.Label(
            summary_window,
            text=f"Total Focus Time: {total_minutes} minutes",
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(pady=10)
        
        tk.Label(
            summary_window,
            text=f"Rest Periods: {self.rest_periods}",
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(pady=10)

    def show_help(self):
        messagebox.showinfo(
            "Help",
            "Welcome to Pomo!\n\n"
            "• Click and drag the timer circle to adjust time\n"
            "• Click 'Begin' to start the timer\n" 
            "• Click 'End' to stop the current session\n\n"
            "The timer will automatically switch between:\n"
            "- Your set focus period\n"
            "- 15 min rest period\n"
            "Until you end the session"
        
        )
        
        # Timer canvas
        self.canvas = tk.Canvas(
            self.root,
            width=300,
            height=300,
            bg=self.bg_color,
            highlightthickness=0  # Remove canvas border
        )
        self.canvas.pack(pady=20)
        
        # Draw timer circle
        self.draw_timer()
        
        # Add label below the timer circle
        self.drag_label = tk.Label(
            self.root,
            text="Drag to change time",
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.fg_color
        )
        self.drag_label.pack(pady=1)
        
        # Buttons frame
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(pady=20)
        
        self.begin_button = ttk.Button(
            button_frame,
            text="Begin",
            command=self.start_timer,
            style="Custom.TButton"
        )
        self.begin_button.pack(side=tk.LEFT, padx=10)
        
        self.end_button = ttk.Button(
            button_frame,
            text="End",
            command=self.end_session,
            style="Custom.TButton"
        )
        self.end_button.pack(side=tk.LEFT, padx=10)
        
        # Bind mouse events for timer adjustment
        self.canvas.bind("<Button-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_end)

def main():
    root = tk.Tk()
    app = PomoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 