# first_run_wizard.py - Interactive first-run setup wizard (FIXED)
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from pathlib import Path
import os
import subprocess
import webbrowser
from typing import Optional
import json

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FirstRunWizard:
    """Interactive setup wizard for first-time Jarvis users"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Jarvis Setup Wizard")
        self.root.geometry("900x700")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        # Setup data
        self.config = {
            "gemini_api_key": "",
            "elevenlabs_api_key": "",
            "auto_start": True,
            "web_agent_mode": "balanced",
            "whisper_model": "base",
            "hotkey": "ctrl+space",
            "install_ollama": False,
        }
        
        self.current_page = 0
        self.pages = [
            self.create_welcome_page,
            self.create_system_check_page,
            self.create_api_keys_page,
            self.create_performance_page,
            self.create_features_page,
            self.create_final_page,
        ]
        
        # Main container
        self.container = ctk.CTkFrame(self.root)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Bottom navigation frame
        self.nav_frame = ctk.CTkFrame(self.root)
        self.nav_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Progress indicator
        self.progress_label = ctk.CTkLabel(self.nav_frame, text="", font=("Arial", 10))
        self.progress_label.pack(side="left", padx=5)
        
        # Buttons container
        button_container = ctk.CTkFrame(self.nav_frame)
        button_container.pack(side="right", padx=0)
        
        self.back_btn = ctk.CTkButton(
            button_container,
            text="← Back",
            command=self.prev_page,
            width=100,
            height=40,
            state="disabled",
            fg_color="#666666"
        )
        self.back_btn.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(
            button_container,
            text="Next →",
            command=self.next_page,
            width=120,
            height=40,
            fg_color="#00ff88",
            text_color="black",
            font=("Arial", 12, "bold")
        )
        self.next_btn.pack(side="left", padx=5)
        
        self.cancel_btn = ctk.CTkButton(
            button_container,
            text="Cancel",
            command=self.cancel,
            width=100,
            height=40,
            fg_color="#666666"
        )
        self.cancel_btn.pack(side="left", padx=5)
        
        # Show first page
        self.show_page(0)
    
    def clear_container(self):
        """Clear current page"""
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def show_page(self, page_num: int):
        """Display specific page"""
        self.clear_container()
        self.current_page = page_num
        self.pages[page_num]()
        
        # Update progress
        total = len(self.pages)
        self.progress_label.configure(text=f"Step {page_num + 1} of {total}")
        
        # Update navigation buttons
        self.back_btn.configure(state="normal" if page_num > 0 else "disabled")
        
        if page_num == len(self.pages) - 1:
            self.next_btn.configure(text="Finish ✓", fg_color="#00dd00")
        else:
            self.next_btn.configure(text="Next →", fg_color="#00ff88")
    
    def next_page(self):
        """Go to next page"""
        if self.current_page == len(self.pages) - 1:
            self.finish()
        else:
            self.show_page(self.current_page + 1)
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.show_page(self.current_page - 1)
    
    def cancel(self):
        """Cancel setup"""
        if messagebox.askyesno("Cancel Setup", "Are you sure? You can run setup again later."):
            self.root.quit()
    
    def finish(self):
        """Complete setup"""
        try:
            # Validate Gemini key
            if not self.config["gemini_api_key"] or "your_" in self.config["gemini_api_key"]:
                messagebox.showwarning(
                    "Missing API Key",
                    "Please enter your Gemini API key.\n\nYou can get one free from ai.google.dev"
                )
                self.show_page(2)  # Go back to API keys page
                return
            
            self.save_config()
            
            messagebox.showinfo(
                "Setup Complete!",
                "Jarvis is now configured!\n\nClick OK to launch Jarvis."
            )
            self.root.quit()
            
            # Launch Jarvis
            import subprocess
            subprocess.Popen(["python", "main_standalone.py"])
            
        except Exception as e:
            messagebox.showerror("Error", f"Setup failed:\n{e}")
    
    def save_config(self):
        """Save configuration to .env"""
        env_content = f"""# Jarvis Assistant Configuration
# Generated by Setup Wizard

# === API KEYS ===
GEMINI_API_KEY={self.config['gemini_api_key']}
ELEVENLABS_API_KEY={self.config['elevenlabs_api_key']}

# === PERFORMANCE ===
WEB_AGENT_MODE={self.config['web_agent_mode']}
WHISPER_MODEL_SIZE={self.config['whisper_model']}
WEB_AGENT_ENABLED=true
WEB_AGENT_VISION_ENABLED=true

# === LLM ===
LLM_PRIORITY=["gemini", "ollama"]
LOCAL_ONLY=false

# === TTS ===
TTS_PRIORITY=["elevenlabs", "gtts", "piper"]

# === SYSTEM ===
AUTO_START={str(self.config['auto_start']).lower()}
HOTKEY={self.config['hotkey']}
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        # Create first-run marker
        Path("cache").mkdir(exist_ok=True)
        (Path("cache") / ".first_run_complete").touch()

    # ===== PAGE CREATORS =====
    
    def create_welcome_page(self):
        """Welcome page"""
        frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        
        # Title
        title = ctk.CTkLabel(
            frame,
            text="Welcome to Jarvis! 🤖",
            font=("Arial", 36, "bold"),
            text_color="#00ff88"
        )
        title.pack(pady=(40, 10))
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            frame,
            text="Your Personal AI Assistant",
            font=("Arial", 18),
            text_color="#cccccc"
        )
        subtitle.pack(pady=(0, 40))
        
        # Features list
        features_frame = ctk.CTkFrame(frame, fg_color="transparent")
        features_frame.pack(pady=20, padx=40)
        
        features = [
            ("🎤", "Voice-activated with 'Hey Jarvis' wake word"),
            ("🧠", "Powered by Google Gemini AI"),
            ("🌐", "Web browsing and automation"),
            ("📱", "Control your applications"),
            ("⏰", "Smart reminders and scheduling"),
            ("💬", "Natural conversation with memory"),
        ]
        
        for emoji, feature in features:
            item_frame = ctk.CTkFrame(features_frame, fg_color="transparent")
            item_frame.pack(anchor="w", pady=8, fill="x")
            
            label = ctk.CTkLabel(
                item_frame,
                text=f"{emoji}  {feature}",
                font=("Arial", 14),
                anchor="w"
            )
            label.pack(anchor="w")
        
        # System info
        try:
            import psutil
            ram = psutil.virtual_memory().total / (1024**3)
            info_text = f"Detected System: {ram:.0f}GB RAM | Windows"
        except:
            info_text = "Detected System: Windows"
        
        info = ctk.CTkLabel(
            frame,
            text=info_text,
            font=("Arial", 12),
            text_color="#888888"
        )
        info.pack(pady=(40, 20))
        
        # Instructions
        instr = ctk.CTkLabel(
            frame,
            text="👉 Click 'Next →' to continue setup",
            font=("Arial", 13, "bold"),
            text_color="#00ff88"
        )
        instr.pack(pady=(20, 0))
    
    def create_system_check_page(self):
        """System requirements check"""
        frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        
        title = ctk.CTkLabel(
            frame,
            text="System Check ✓",
            font=("Arial", 28, "bold"),
            text_color="#00ff88"
        )
        title.pack(pady=(20, 30))
        
        # Check items
        checks = [
            ("Python 3.10+", self.check_python()),
            ("Internet Connection", self.check_internet()),
            ("Microphone Access", self.check_microphone()),
            ("RAM (8GB+)", self.check_ram()),
        ]
        
        for name, status in checks:
            self.create_check_item(frame, name, status)
        
        # Summary
        passed = sum(1 for _, s in checks if s)
        total = len(checks)
        
        summary = ctk.CTkLabel(
            frame,
            text=f"System Status: {passed}/{total} checks passed",
            font=("Arial", 13),
            text_color="#00ff88" if passed == total else "#ffaa00"
        )
        summary.pack(pady=(30, 0))
    
    def create_check_item(self, parent, name: str, passed: bool):
        """Create a check item"""
        item_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=8)
        item_frame.pack(fill="x", padx=20, pady=8)
        
        icon = "✓" if passed else "⚠"
        color = "#00ff88" if passed else "#ffaa00"
        
        label = ctk.CTkLabel(
            item_frame,
            text=f"{icon} {name}",
            font=("Arial", 13),
            text_color=color
        )
        label.pack(side="left", padx=15, pady=12)
    
    def create_api_keys_page(self):
        """API keys configuration"""
        frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        
        title = ctk.CTkLabel(
            frame,
            text="API Keys Configuration ⚙️",
            font=("Arial", 28, "bold"),
            text_color="#00ff88"
        )
        title.pack(pady=(10, 5))
        
        subtitle = ctk.CTkLabel(
            frame,
            text="Required for Jarvis to work",
            font=("Arial", 13),
            text_color="#888888"
        )
        subtitle.pack(pady=(0, 30))
        
        # Gemini API Key (Required)
        self.create_api_input(
            frame,
            "Google Gemini API Key (Required) ⭐",
            "gemini_api_key",
            "https://ai.google.dev",
            "Get free API key from ai.google.dev",
            required=True
        )
        
        # ElevenLabs (Optional)
        self.create_api_input(
            frame,
            "ElevenLabs API Key (Optional)",
            "elevenlabs_api_key",
            "https://elevenlabs.io",
            "For premium text-to-speech (leave blank for free Google TTS)",
            required=False
        )
    
    def create_api_input(self, parent, label: str, key: str, url: str, help_text: str, required: bool):
        """Create API key input field"""
        container = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=8)
        container.pack(fill="x", padx=20, pady=15)
        
        # Label
        title = ctk.CTkLabel(
            container,
            text=label,
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        title.pack(fill="x", padx=15, pady=(10, 5))
        
        # Help text
        help_label = ctk.CTkLabel(
            container,
            text=help_text,
            font=("Arial", 10),
            text_color="#888888",
            anchor="w"
        )
        help_label.pack(fill="x", padx=15, pady=(0, 8))
        
        # Input frame
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Entry
        entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Paste your API key here" if required else "Optional - leave blank for default TTS",
            width=500
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry.bind("<KeyRelease>", lambda e: self.update_config(key, entry.get()))
        
        # Get key button
        btn = ctk.CTkButton(
            input_frame,
            text="Get Key 🔗",
            command=lambda: webbrowser.open(url),
            width=100,
            height=32,
            fg_color="#0088ff"
        )
        btn.pack(side="right")
    
    def create_performance_page(self):
        """Performance settings"""
        frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        
        title = ctk.CTkLabel(
            frame,
            text="Performance Settings ⚡",
            font=("Arial", 28, "bold"),
            text_color="#00ff88"
        )
        title.pack(pady=(10, 5))
        
        # Detect system
        try:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024**3)
        except:
            ram_gb = 16
        
        info = ctk.CTkLabel(
            frame,
            text=f"Detected: {ram_gb:.0f}GB RAM",
            font=("Arial", 12),
            text_color="#888888"
        )
        info.pack(pady=(0, 20))
        
        # Web Agent Mode
        mode_frame = ctk.CTkFrame(frame, fg_color="#2b2b2b", corner_radius=8)
        mode_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            mode_frame,
            text="Web Agent Performance:",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        mode_var = tk.StringVar(value="balanced")
        
        modes = [
            ("lightweight", "🪶 Lightweight (300MB, basic)"),
            ("balanced", "⚖️ Balanced (600MB, recommended)"),
            ("full", "🚀 Full (1GB, all features)"),
        ]
        
        for value, label in modes:
            radio = ctk.CTkRadioButton(
                mode_frame,
                text=label,
                variable=mode_var,
                value=value,
                command=lambda v=value: self.update_config("web_agent_mode", v)
            )
            radio.pack(anchor="w", padx=30, pady=5)
        
        # Whisper Model
        whisper_frame = ctk.CTkFrame(frame, fg_color="#2b2b2b", corner_radius=8)
        whisper_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            whisper_frame,
            text="Speech Recognition Model:",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        whisper_var = tk.StringVar(value="base")
        
        whisper_models = [
            ("tiny", "🏃 Tiny (Fastest)"),
            ("base", "⚡ Base (Recommended)"),
            ("small", "🎯 Small (Better accuracy)"),
        ]
        
        for value, label in whisper_models:
            radio = ctk.CTkRadioButton(
                whisper_frame,
                text=label,
                variable=whisper_var,
                value=value,
                command=lambda v=value: self.update_config("whisper_model", v)
            )
            radio.pack(anchor="w", padx=30, pady=5)
        
        ctk.CTkLabel(whisper_frame, text="").pack(pady=5)
    
    def create_features_page(self):
        """Feature selection"""
        frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        
        title = ctk.CTkLabel(
            frame,
            text="Features & Settings 🎯",
            font=("Arial", 28, "bold"),
            text_color="#00ff88"
        )
        title.pack(pady=(10, 30))
        
        # Auto-start
        auto_var = tk.BooleanVar(value=True)
        auto_check = ctk.CTkCheckBox(
            frame,
            text="🚀 Start Jarvis automatically when Windows starts",
            variable=auto_var,
            font=("Arial", 12),
            command=lambda: self.update_config("auto_start", auto_var.get())
        )
        auto_check.pack(anchor="w", padx=40, pady=15)
        
        # Hotkey info
        hotkey_frame = ctk.CTkFrame(frame, fg_color="#2b2b2b", corner_radius=8)
        hotkey_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            hotkey_frame,
            text="⌨️ Global Hotkey",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            hotkey_frame,
            text="Default: Ctrl+Space to activate voice input\nCan be changed in settings later",
            font=("Arial", 11),
            text_color="#888888",
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 15))
    
    def create_final_page(self):
        """Final confirmation"""
        frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        frame.pack(fill="both", expand=True)
        
        title = ctk.CTkLabel(
            frame,
            text="Setup Complete! 🎉",
            font=("Arial", 32, "bold"),
            text_color="#00ff88"
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            frame,
            text="Jarvis is ready to launch",
            font=("Arial", 16),
            text_color="#cccccc"
        )
        subtitle.pack(pady=(0, 40))
        
        # Summary
        summary_frame = ctk.CTkFrame(frame, fg_color="#2b2b2b", corner_radius=8)
        summary_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            summary_frame,
            text="Configuration Summary",
            font=("Arial", 14, "bold")
        ).pack(pady=(15, 10))
        
        summary_items = [
            ("🔑 Gemini API", "Configured ✓" if self.config['gemini_api_key'] else "Missing ⚠"),
            ("⚡ Performance", self.config['web_agent_mode'].upper()),
            ("🎤 Speech Model", self.config['whisper_model'].upper()),
            ("🚀 Auto-start", "Enabled" if self.config['auto_start'] else "Disabled"),
        ]
        
        for label, value in summary_items:
            item_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
            item_frame.pack(fill="x", padx=15, pady=5)
            
            ctk.CTkLabel(
                item_frame,
                text=label,
                font=("Arial", 11),
                anchor="w"
            ).pack(side="left", padx=5)
            
            ctk.CTkLabel(
                item_frame,
                text=value,
                font=("Arial", 11, "bold"),
                text_color="#00ff88",
                anchor="e"
            ).pack(side="right", padx=5)
        
        # Next steps
        next_steps_frame = ctk.CTkFrame(frame, fg_color="#2b2b2b", corner_radius=8)
        next_steps_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            next_steps_frame,
            text="🚀 Next Steps",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 8))
        
        tips = [
            "Say 'Hey Jarvis' to activate",
            "Press Ctrl+Space for manual activation",
            "Try: 'What time is it?'",
            "Right-click system tray for settings",
        ]
        
        for tip in tips:
            ctk.CTkLabel(
                next_steps_frame,
                text=f"• {tip}",
                font=("Arial", 11),
                anchor="w"
            ).pack(anchor="w", padx=25, pady=2)
        
        ctk.CTkLabel(next_steps_frame, text="").pack(pady=5)
        
        # Instructions
        instr = ctk.CTkLabel(
            frame,
            text="👉 Click 'Finish ✓' to complete setup and launch Jarvis",
            font=("Arial", 13, "bold"),
            text_color="#00ff88"
        )
        instr.pack(pady=(30, 0))
    
    # Helper methods
    def update_config(self, key: str, value):
        """Update configuration"""
        self.config[key] = value
    
    def check_python(self) -> bool:
        import sys
        return sys.version_info >= (3, 8)
    
    def check_internet(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen('http://www.google.com', timeout=3)
            return True
        except:
            return False
    
    def check_microphone(self) -> bool:
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            return any(d['max_input_channels'] > 0 for d in devices)
        except:
            return False
    
    def check_ram(self) -> bool:
        try:
            import psutil
            return psutil.virtual_memory().total >= 8 * 1024**3
        except:
            return True
    
    def run(self):
        """Start wizard"""
        self.root.mainloop()


def should_run_wizard() -> bool:
    """Check if first-run wizard should run"""
    marker = Path("cache") / ".first_run_complete"
    env_exists = Path(".env").exists()
    
    return not marker.exists() or not env_exists


if __name__ == "__main__":
    if should_run_wizard():
        wizard = FirstRunWizard()
        wizard.run()
    else:
        print("Setup already complete.")