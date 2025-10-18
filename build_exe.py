# build_exe.py - Build standalone executable for Windows
import PyInstaller.__main__
import sys
from pathlib import Path
import shutil

def build():
    """Build Jarvis as a standalone executable"""
    
    print("🔨 Building Jarvis Assistant...")
    print("📊 Target: MSI Thin 15 B13UC (16GB RAM, RTX 3050)")
    
    # Project root
    root = Path(__file__).parent
    
    # Icon (create if doesn't exist)
    icon_path = root / "assets" / "jarvis.ico"
    if not icon_path.exists():
        print("⚠️  No icon found, using default")
        icon_arg = []
    else:
        icon_arg = [f"--icon={icon_path}"]
    
    # Data files to include
    data_files = [
        (root / "custom_apps.json", "."),
        (root / ".env", "."),
        (root / "venv/Lib/site-packages/openwakeword/resources", "openwakeword/resources"),
    ]
    
    datas = []
    for src, dst in data_files:
        if src.exists():
            datas.extend(["--add-data", f"{src};{dst}"])
    
    # Hidden imports (for dynamic imports)
    hidden_imports = [
        "pyttsx3.drivers",
        "pyttsx3.drivers.sapi5",
        "win32com.client",
        "win32gui",
        "win32con",
        "win32process",
        "psutil",
        "spacy",
        "whisper",
        "torch",
        "playwright",
        "elevenlabs",
        "gtts",
        "openwakeword",
        "webrtcvad",
        "sklearn",
        "pandas",
        "numpy",
    ]
    
    hidden_args = []
    for imp in hidden_imports:
        hidden_args.extend(["--hidden-import", imp])
    
    # PyInstaller arguments
    args = [
        "main_standalone.py",
        "--name=Jarvis",
        "--onefile",
        "--windowed",  # No console window
        "--clean",
        *icon_arg,
        *datas,
        *hidden_args,
        "--optimize=2",
        "--noupx",  # Disable UPX (better compatibility)
        "--noconfirm",
        # GPU optimization
        "--exclude-module=matplotlib",
        "--exclude-module=IPython",
    ]
    
    print("\n📦 PyInstaller arguments:")
    for arg in args:
        print(f"  {arg}")
    
    print("\n🔄 Building... (this may take 5-10 minutes)")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ Build complete!")
        print(f"📁 Executable: {root / 'dist' / 'Jarvis.exe'}")
        print("\n📝 Next steps:")
        print("1. Copy the .env file to the same folder as Jarvis.exe")
        print("2. Create a custom_apps.json if needed")
        print("3. Run Jarvis.exe to start your assistant!")
        print("\n💡 Tip: Right-click Jarvis.exe > Create Shortcut")
        print("   Then move shortcut to:")
        print("   C:\\Users\\YourName\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        print("   for auto-start on boot!")
        
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()