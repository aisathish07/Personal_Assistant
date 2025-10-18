# stats_dashboard.py - Real-time statistics and monitoring dashboard
import tkinter as tk
import customtkinter as ctk
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from typing import Dict, List, Tuple
import threading

ctk.set_appearance_mode("dark")


class StatsDashboard:
    """Real-time statistics and monitoring dashboard for Jarvis"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Jarvis Statistics Dashboard")
        self.root.geometry("1000x700")
        
        # Data
        self.update_interval = 1000  # ms
        self.running = True
        
        # Create UI
        self.create_ui()
        
        # Start update loop
        self.update_stats()
    
    def create_ui(self):
        """Create dashboard UI"""
        # Header
        header = ctk.CTkFrame(self.root, height=80)
        header.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(
            header,
            text="📊 Jarvis Statistics Dashboard",
            font=("Arial", 24, "bold")
        ).pack(side="left", padx=20, pady=20)
        
        self.status_label = ctk.CTkLabel(
            header,
            text="🟢 Active",
            font=("Arial", 14)
        )
        self.status_label.pack(side="right", padx=20)
        
        # Main content
        content = ctk.CTkFrame(self.root)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - System resources
        left_panel = ctk.CTkFrame(content, width=480)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.create_system_panel(left_panel)
        
        # Right panel - Usage stats
        right_panel = ctk.CTkFrame(content, width=480)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.create_usage_panel(right_panel)
    
    def create_system_panel(self, parent):
        """Create system resources panel"""
        ctk.CTkLabel(
            parent,
            text="System Resources",
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 10))
        
        # CPU
        self.cpu_frame = self.create_metric_card(parent, "CPU Usage")
        self.cpu_label = ctk.CTkLabel(self.cpu_frame, text="0%", font=("Arial", 32, "bold"))
        self.cpu_label.pack(pady=10)
        self.cpu_bar = ctk.CTkProgressBar(self.cpu_frame, width=400)
        self.cpu_bar.pack(pady=10)
        self.cpu_bar.set(0)
        
        # RAM
        self.ram_frame = self.create_metric_card(parent, "RAM Usage")
        self.ram_label = ctk.CTkLabel(self.ram_frame, text="0 GB / 0 GB", font=("Arial", 20, "bold"))
        self.ram_label.pack(pady=10)
        self.ram_bar = ctk.CTkProgressBar(self.ram_frame, width=400)
        self.ram_bar.pack(pady=10)
        self.ram_bar.set(0)
        
        # GPU (if available)
        self.gpu_frame = self.create_metric_card(parent, "GPU (RTX 3050)")
        self.gpu_label = ctk.CTkLabel(self.gpu_frame, text="Monitoring...", font=("Arial", 16))
        self.gpu_label.pack(pady=10)
        
        # Disk
        self.disk_frame = self.create_metric_card(parent, "Disk Usage")
        self.disk_label = ctk.CTkLabel(self.disk_frame, text="0 GB free", font=("Arial", 16))
        self.disk_label.pack(pady=10)
    
    def create_usage_panel(self, parent):
        """Create usage statistics panel"""
        ctk.CTkLabel(
            parent,
            text="Usage Statistics",
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 10))
        
        # Commands
        commands_frame = self.create_metric_card(parent, "Commands Today")
        self.commands_label = ctk.CTkLabel(commands_frame, text="0", font=("Arial", 32, "bold"))
        self.commands_label.pack(pady=10)
        
        # Apps launched
        apps_frame = self.create_metric_card(parent, "Apps Launched")
        self.apps_label = ctk.CTkLabel(apps_frame, text="0", font=("Arial", 32, "bold"))
        self.apps_label.pack(pady=10)
        
        # Most used apps
        most_used_frame = self.create_metric_card(parent, "Most Used Apps")
        self.most_used_text = ctk.CTkTextbox(most_used_frame, height=100, width=400)
        self.most_used_text.pack(pady=10, padx=10)
        
        # Recent activity
        activity_frame = self.create_metric_card(parent, "Recent Activity")
        self.activity_text = ctk.CTkTextbox(activity_frame, height=150, width=400)
        self.activity_text.pack(pady=10, padx=10)
        
        # Uptime
        uptime_frame = self.create_metric_card(parent, "Session Info")
        self.uptime_label = ctk.CTkLabel(uptime_frame, text="Uptime: 0h 0m", font=("Arial", 14))
        self.uptime_label.pack(pady=5)
        self.start_time = time.time()
    
    def create_metric_card(self, parent, title: str):
        """Create a metric card"""
        frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            frame,
            text=title,
            font=("Arial", 14, "bold")
        ).pack(pady=(10, 5))
        
        return frame
    
    def update_stats(self):
        """Update all statistics"""
        if not self.running:
            return
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_label.configure(text=f"{cpu_percent:.1f}%")
            self.cpu_bar.set(cpu_percent / 100)
            
            # Set color based on usage
            if cpu_percent > 80:
                self.cpu_label.configure(text_color="#ff4444")
            elif cpu_percent > 50:
                self.cpu_label.configure(text_color="#ffaa44")
            else:
                self.cpu_label.configure(text_color="#00ff88")
            
            # RAM
            ram = psutil.virtual_memory()
            ram_used_gb = ram.used / (1024**3)
            ram_total_gb = ram.total / (1024**3)
            self.ram_label.configure(text=f"{ram_used_gb:.1f} GB / {ram_total_gb:.1f} GB")
            self.ram_bar.set(ram.percent / 100)
            
            # Disk
            disk = psutil.disk_usage('.')
            disk_free_gb = disk.free / (1024**3)
            self.disk_label.configure(text=f"{disk_free_gb:.1f} GB free ({disk.percent}% used)")
            
            # GPU (if NVIDIA)
            try:
                import subprocess
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    gpu_util, gpu_mem_used, gpu_mem_total = result.stdout.strip().split(',')
                    self.gpu_label.configure(
                        text=f"GPU: {gpu_util.strip()}% | VRAM: {gpu_mem_used.strip()}/{gpu_mem_total.strip()} MB"
                    )
            except:
                self.gpu_label.configure(text="GPU monitoring unavailable")
            
            # Usage stats from database
            self.update_usage_stats()
            
            # Uptime
            uptime_seconds = int(time.time() - self.start_time)
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            self.uptime_label.configure(text=f"Uptime: {hours}h {minutes}m")
            
        except Exception as e:
            print(f"Error updating stats: {e}")
        
        # Schedule next update
        self.root.after(self.update_interval, self.update_stats)
    
    def update_usage_stats(self):
        """Update usage statistics from database"""
        try:
            db_path = Path("assistant_memory.db")
            if not db_path.exists():
                return
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Commands today
            today = datetime.now().date()
            cursor.execute("""
                SELECT COUNT(*) FROM commands 
                WHERE date(timestamp) = ?
            """, (today,))
            commands_today = cursor.fetchone()[0]
            self.commands_label.configure(text=str(commands_today))
            
            # Most used apps
            cursor.execute("""
                SELECT name, usage_count FROM apps 
                ORDER BY usage_count DESC 
                LIMIT 5
            """)
            most_used = cursor.fetchall()
            
            self.most_used_text.delete("1.0", "end")
            for i, (name, count) in enumerate(most_used, 1):
                self.most_used_text.insert("end", f"{i}. {name.title()}: {count} times\n")
            
            # Recent activity
            cursor.execute("""
                SELECT command_text, timestamp FROM commands 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            recent = cursor.fetchall()
            
            self.activity_text.delete("1.0", "end")
            for cmd, ts in recent:
                try:
                    time_str = datetime.fromisoformat(ts).strftime("%H:%M")
                    self.activity_text.insert("end", f"[{time_str}] {cmd[:40]}\n")
                except:
                    self.activity_text.insert("end", f"{cmd[:40]}\n")
            
            # Apps launched (approximate)
            cursor.execute("SELECT SUM(usage_count) FROM apps")
            result = cursor.fetchone()
            apps_launched = result[0] if result[0] else 0
            self.apps_label.configure(text=str(apps_launched))
            
            conn.close()
            
        except Exception as e:
            print(f"Error updating usage stats: {e}")
    
    def run(self):
        """Run dashboard"""
        try:
            self.root.mainloop()
        finally:
            self.running = False


if __name__ == "__main__":
    dashboard = StatsDashboard()
    dashboard.run()