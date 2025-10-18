# main_windows_compatible.py - Windows-compatible version with proper encoding and error handling
import io
import os
import sys
import locale
import threading
import queue
import logging
import asyncio
import signal
from pathlib import Path
import traceback

# Force UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    try:
        # Set console to UTF-8
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
        kernel32.SetConsoleCP(65001)        # UTF-8 input
        
        # Set stdout/stderr to UTF-8
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        
    except Exception as e:
        print(f"Warning: Could not set UTF-8 encoding: {e}")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from memory_manager import MemoryManager
from app_scanner import AppManager
from gui import AssistantGUI
from floating_widget import FloatingWidget
from system_tray import SystemTray
from wake_word import WakeWordDetector
from speech_to_text import SpeechToText
from command_processor import CommandProcessor
from tts import TextToSpeech
from predictive_model import PredictiveModel
from first_run_wizard import should_run_wizard, FirstRunWizard
from settings_dialog import SettingsDialog

# Setup logging with Windows compatibility
def setup_logging():
    """Setup comprehensive logging configuration with Windows support"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatter - use ASCII-safe characters on Windows
    if sys.platform.startswith('win'):
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Setup file handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_dir / "assistant.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Setup console handler with Windows compatibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger("AI_Assistant.Main")

# Setup logging
logger = setup_logging()

class AssistantApp:
    """Windows-compatible main application controller"""
    
    def __init__(self):
        self.input_queue = queue.Queue()
        self.mode = "widget"  # widget or full
        self.widget: FloatingWidget = None
        self.full_gui: AssistantGUI = None
        self.system_tray: SystemTray = None
        self.assistant_thread: threading.Thread = None
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Components (will be initialized in assistant thread)
        self.processor = None
        self.tts_engine = None
        self.detector = None
        self.memory_manager = None
        self.app_manager = None
        self.predictor = None
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
            
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            # Windows doesn't have SIGQUIT
            if hasattr(signal, 'SIGQUIT'):
                signal.signal(signal.SIGQUIT, signal_handler)
        except Exception as e:
            logger.warning(f"Could not setup signal handlers: {e}")
    
    def start(self):
        """Start the assistant with comprehensive error handling"""
        try:
            self._print_banner()
            logger.info("Starting Jarvis Assistant for MSI Thin 15 B13UC...")
            logger.info("System: 16GB RAM, RTX 3050 4GB")
            
            # Check system requirements
            self._check_system_requirements()
            
            # Check first run
            if should_run_wizard():
                logger.info("First run detected - showing setup wizard")
                wizard = FirstRunWizard()
                wizard.run()
                
                # Check if wizard completed
                if not Path(".env").exists():
                    logger.error("Setup wizard incomplete - exiting")
                    return False
            
            # Start with floating widget
            self.show_widget()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start assistant: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _check_system_requirements(self):
        """Check if system meets minimum requirements"""
        try:
            import psutil
            
            # Check RAM
            total_ram = psutil.virtual_memory().total / (1024**3)  # GB
            if total_ram < 8:
                logger.warning(f"Low RAM detected: {total_ram:.1f}GB. Recommended: 8GB+")
            else:
                logger.info(f"RAM check passed: {total_ram:.1f}GB")
                
            # Check CPU cores
            cpu_count = psutil.cpu_count()
            if cpu_count < 4:
                logger.warning(f"Low CPU cores: {cpu_count}. Recommended: 4+")
            else:
                logger.info(f"CPU check passed: {cpu_count} cores")
                
        except ImportError:
            logger.warning("Could not import psutil for system checks")
    
    def _print_banner(self):
        """Print application banner using ASCII art for Windows compatibility"""
        if sys.platform.startswith('win'):
            # Use ASCII-only banner for Windows
            banner = """
    ============================================
    |                                          |
    |         JARVIS AI ASSISTANT              |
    |      Your Personal Computing Buddy       |
    |                                          |
    |  Optimized for MSI Thin 15 B13UC        |
    |  16GB RAM | RTX 3050 4GB | Windows 11   |
    |                                          |
    ============================================
            """
        else:
            # Use Unicode banner for other systems
            banner = """
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║            JARVIS AI ASSISTANT                ║
    ║         Your Personal Computing Buddy         ║
    ║                                               ║
    ║  Optimized for MSI Thin 15 B13UC             ║
    ║  16GB RAM | RTX 3050 4GB | Windows 11        ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
            """
        
        # Log banner without emojis on Windows
        for line in banner.strip().split('\n'):
            logger.info(line)
    
    def show_widget(self):
        """Show floating widget mode with error handling"""
        try:
            self.mode = "widget"
            self.widget = FloatingWidget(
                command_callback=self.handle_widget_command,
                on_close=self.shutdown
            )
            
            # Start system tray
            if self.system_tray is None:
                self.system_tray = SystemTray(
                    on_show=self.show_widget_from_tray,
                    on_hide=self.hide_widget,
                    on_voice=self.trigger_voice_command,
                    on_settings=self.open_settings,
                    on_exit=self.shutdown
                )
                self.system_tray.start()
            
            # Start assistant thread if not running
            if not self.running:
                self.running = True
                self.assistant_thread = threading.Thread(
                    target=self.run_assistant_thread,
                    daemon=False,
                    name="AssistantMainThread"
                )
                self.assistant_thread.start()
                
        except Exception as e:
            logger.error(f"Failed to show widget: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def run_assistant_thread(self):
        """Run the main assistant thread with comprehensive error handling"""
        logger.info("Starting assistant thread...")
        
        try:
            # Initialize components with better error handling
            self._initialize_components()
            
            # Main loop
            while self.running and not self.shutdown_event.is_set():
                try:
                    # Process any pending commands
                    self._process_pending_commands()
                    
                    # Sleep briefly to prevent busy waiting
                    threading.Event().wait(0.1)
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    logger.error(traceback.format_exc())
                    threading.Event().wait(1)  # Wait longer on error
                    
        except Exception as e:
            logger.error(f"Critical error in assistant thread: {e}")
            logger.error(traceback.format_exc())
        finally:
            logger.info("Assistant thread stopped")
    
    def _initialize_components(self):
        """Initialize assistant components with proper error handling"""
        try:
            # Initialize memory manager
            self.memory_manager = MemoryManager()
            logger.info("Memory manager initialized")
            
            # Initialize app manager
            self.app_manager = AppManager(self.memory_manager)
            logger.info("App manager initialized")
            
            # Initialize TTS engine
            self.tts_engine = TextToSpeech()
            logger.info("TTS engine initialized")
            
            # Initialize command processor
            self.processor = CommandProcessor(
                gui=None,  # Will be set when GUI is created
                app_manager=self.app_manager,
                memory_manager=self.memory_manager,
                tts_engine=self.tts_engine,
                predictor=PredictiveModel()
            )
            logger.info("Command processor initialized")
            
            # Initialize wake word detector
            self.detector = WakeWordDetector(
                callback=self.handle_wake_word_detection
            )
            logger.info("Wake word detector initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _process_pending_commands(self):
        """Process any pending commands in the queue"""
        try:
            while not self.input_queue.empty():
                command = self.input_queue.get_nowait()
                if command:
                    self.handle_widget_command(command)
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error processing commands: {e}")
    
    def handle_widget_command(self, command: str):
        """Handle commands from the widget with error handling"""
        try:
            logger.info(f"Processing command: {command}")
            
            if self.processor:
                response = self.processor.process_command(command)
                if response:
                    logger.info(f"Command processed successfully")
                    # Update widget with response if available
                    if self.widget:
                        self.widget.update_response(response)
            else:
                logger.warning("Command processor not available")
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            logger.error(traceback.format_exc())
    
    def handle_wake_word_detection(self):
        """Handle wake word detection with error handling"""
        try:
            logger.info("Wake word detected")
            if self.widget:
                self.widget.show_voice_input()
        except Exception as e:
            logger.error(f"Error handling wake word detection: {e}")
    
    def shutdown(self):
        """Graceful shutdown with proper cleanup"""
        logger.info("Initiating graceful shutdown...")
        
        try:
            # Set shutdown event
            self.shutdown_event.set()
            self.running = False
            
            # Cleanup components in reverse order
            components_to_cleanup = [
                ("Wake word detector", self.detector),
                ("Command processor", self.processor),
                ("TTS engine", self.tts_engine),
                ("App manager", self.app_manager),
                ("Memory manager", self.memory_manager),
            ]
            
            for name, component in components_to_cleanup:
                try:
                    if hasattr(component, 'cleanup'):
                        component.cleanup()
                        logger.info(f"{name} cleaned up")
                    elif hasattr(component, 'close'):
                        component.close()
                        logger.info(f"{name} closed")
                except Exception as e:
                    logger.error(f"Error cleaning up {name}: {e}")
            
            # Cleanup GUI components
            if self.widget:
                try:
                    self.widget.destroy()
                    logger.info("Widget destroyed")
                except Exception as e:
                    logger.error(f"Error destroying widget: {e}")
            
            if self.system_tray:
                try:
                    self.system_tray.stop()
                    logger.info("System tray stopped")
                except Exception as e:
                    logger.error(f"Error stopping system tray: {e}")
            
            # Wait for assistant thread to finish
            if self.assistant_thread and self.assistant_thread.is_alive():
                logger.info("Waiting for assistant thread to finish...")
                self.assistant_thread.join(timeout=5)
                if self.assistant_thread.is_alive():
                    logger.warning("Assistant thread did not finish in time")
            
            logger.info("Shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            logger.error(traceback.format_exc())
    
    # Additional helper methods for better functionality
    def show_widget_from_tray(self):
        """Show widget from system tray"""
        if self.widget:
            self.widget.show()
    
    def hide_widget(self):
        """Hide widget"""
        if self.widget:
            self.widget.hide()
    
    def trigger_voice_command(self):
        """Trigger voice command"""
        if self.detector:
            self.detector.toggle_listening()
    
    def open_settings(self):
        """Open settings dialog"""
        try:
            settings = SettingsDialog()
            settings.show()
        except Exception as e:
            logger.error(f"Error opening settings: {e}")


def main():
    """Windows-compatible entry point with better error handling"""
    app = None
    try:
        # Check if we're running on Windows
        if sys.platform.startswith('win'):
            logger.info("Running on Windows - using compatible settings")
        
        app = AssistantApp()
        success = app.start()
        
        if not success:
            logger.error("Failed to start application")
            return 1
            
        # Keep main thread alive
        try:
            while app.running and not app.shutdown_event.is_set():
                threading.Event().wait(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            if app:
                app.shutdown()
                
    except Exception as e:
        logger.error(f"Critical error in main: {e}")
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())