#!/usr/bin/env python3
"""
Setup fix script for Jarvis AI Assistant on Windows
This script fixes common setup issues and creates necessary configuration
"""

import os
import sys
import platform
from pathlib import Path

# Force UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
        kernel32.SetConsoleCP(65001)        # UTF-8 input
    except:
        pass

def create_env_file():
    """Create a .env file with default configurations"""
    env_content = """# Jarvis AI Assistant Configuration
# Please add your API keys below to enable all features

# Required API Keys (get these from the respective services)
# PICOVOICE_ACCESS_KEY=your_picovoice_key_here
# GEMINI_API_KEY=your_gemini_key_here
# ELEVENLABS_API_KEY=your_elevenlabs_key_here
# OPENWEATHERMAP_API_KEY=your_weather_key_here
# NEWSAPI_API_KEY=your_news_key_here

# Optional API Keys
# SLACK_API_TOKEN=your_slack_token_here
# EMAIL_ADDRESS=your_email@gmail.com
# EMAIL_PASSWORD=your_app_password
# EMAIL_SMTP_SERVER=smtp.gmail.com
# EMAIL_SMTP_PORT=587

# TTS Configuration
# PIPER_EXECUTABLE_PATH=C:\\path\\to\\piper\\piper.exe
# WHISPER_MODEL_SIZE=base

# Wake Word Configuration
# CUSTOM_WAKE_WORD_PATH=hey-jarvis_en_windows_v3_0_0.ppn

# Web Agent Configuration
# WEB_AGENT_ENABLED=true
# WEB_AGENT_MODE=balanced
# WEB_AGENT_HEADLESS=true

# Performance Settings
# MAX_MEMORY_USAGE_MB=1024
# MAX_WORKER_THREADS=4
# SAMPLE_RATE=16000

# Feature Flags
# ENABLE_METRICS=true
# ENABLE_PREDICTIVE_SUGGESTIONS=true
# LOCAL_ONLY=false
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        print("Creating .env file...")
        with open(env_path, "w", encoding='utf-8') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("Please edit .env and add your API keys to enable all features.")
        return True
    else:
        print("ℹ️  .env file already exists.")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "cache", 
        "skills",
        "backups",
        "temp"
    ]
    
    created = []
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(exist_ok=True)
            created.append(directory)
    
    if created:
        print(f"✅ Created directories: {', '.join(created)}")
    else:
        print("ℹ️  All directories already exist.")

def check_python_version():
    """Check Python version compatibility"""
    print(f"Python version: {platform.python_version()}")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        return False
    elif sys.version_info < (3, 10):
        print("⚠️  Python 3.10+ recommended for best performance.")
    else:
        print("✅ Python version is compatible.")
    
    return True

def check_system_requirements():
    """Check system requirements"""
    print("\nChecking system requirements...")
    
    # Check OS
    print(f"Operating System: {platform.system()} {platform.release()}")
    if platform.system() != "Windows":
        print("⚠️  This script is optimized for Windows.")
    
    # Check architecture
    print(f"Architecture: {platform.machine()}")
    
    # Try to check memory
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"Total RAM: {memory_gb:.1f} GB")
        
        if memory_gb < 8:
            print("⚠️  Less than 8GB RAM may impact performance.")
        else:
            print("✅ Sufficient RAM available.")
            
    except ImportError:
        print("ℹ️  Install psutil for detailed system info: pip install psutil")
    
    return True

def install_requirements():
    """Check and install requirements"""
    print("\nChecking requirements...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Requirements installed successfully!")
            return True
        else:
            print("❌ Error installing requirements:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def setup_piper():
    """Help user setup PIPER TTS"""
    print("\nSetting up PIPER TTS...")
    
    # Check if PIPER is already installed
    piper_paths = [
        "C:\\Program Files\\piper\\piper.exe",
        "C:\\Users\\%USERNAME%\\AppData\\Local\\piper\\piper.exe",
        "piper\\piper.exe",
        "piper.exe",
    ]
    
    existing_piper = None
    for path in piper_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            existing_piper = expanded_path
            break
    
    if existing_piper:
        print(f"✅ PIPER found at: {existing_piper}")
        print(f"Add this to your .env file: PIPER_EXECUTABLE_PATH={existing_piper}")
        return True
    else:
        print("ℹ️  PIPER not found. You can:")
        print("   1. Download PIPER from: https://github.com/rhasspy/piper")
        print("   2. Install it and add the path to your .env file")
        print("   3. Use other TTS engines (gTTS, ElevenLabs)")
        return False

def check_api_keys():
    """Check if API keys are configured"""
    print("\nChecking API key configuration...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    required_keys = [
        "PICOVOICE_ACCESS_KEY",
        "GEMINI_API_KEY",
        "ELEVENLABS_API_KEY"
    ]
    
    missing_keys = []
    for key in required_keys:
        if f"{key}=" not in content or f"{key}=your_" in content:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"⚠️  Missing or placeholder API keys: {', '.join(missing_keys)}")
        print("\nTo get API keys:")
        print("• Picovoice: https://picovoice.ai/ (for wake word)")
        print("• Google AI Studio: https://makersuite.google.com/ (for Gemini)")
        print("• ElevenLabs: https://elevenlabs.io/ (for TTS)")
        return False
    else:
        print("✅ API keys appear to be configured.")
        return True

def create_startup_script():
    """Create a startup script for easy launching"""
    if sys.platform.startswith('win'):
        batch_content = """@echo off
echo Starting Jarvis AI Assistant...
python main.py
pause
"""
        with open("start_jarvis.bat", "w") as f:
            f.write(batch_content)
        print("✅ Created start_jarvis.bat for easy launching.")
    
    # Also create a Python launcher
    launcher_content = """#!/usr/bin/env python3
import subprocess
import sys

try:
    subprocess.run([sys.executable, "main.py"])
except KeyboardInterrupt:
    print("\\nShutting down Jarvis...")
"""
    
    with open("start_jarvis.py", "w") as f:
        f.write(launcher_content)
    print("✅ Created start_jarvis.py launcher.")

def main():
    """Main setup function"""
    print("=" * 60)
    print("Jarvis AI Assistant - Windows Setup Fix")
    print("=" * 60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Check system requirements
    if not check_system_requirements():
        success = False
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Setup PIPER
    setup_piper()
    
    # Check API keys
    if not check_api_keys():
        print("\n⚠️  Please configure your API keys in the .env file")
        print("The assistant will work in limited mode without API keys.")
    
    # Create startup scripts
    create_startup_script()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file and add your API keys")
        print("2. Run: python main.py")
        print("3. Or use: start_jarvis.bat (Windows)")
    else:
        print("❌ Setup completed with warnings.")
        print("Please check the issues above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()