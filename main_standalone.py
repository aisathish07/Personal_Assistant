# main_standalone.py - FIXED: Unicode and NoneType errors resolved
import threading
import queue
import logging
import asyncio
import sys
import os
from pathlib import Path

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

# Setup logging with UTF-8 encoding to fix emoji display on Windows
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Force UTF-8 for Windows console
if sys.platform == 'win32':
    try:
        import io
        # Wrap stdout/stderr to handle Unicode properly
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception as e:
        print(f"Warning: Could not set UTF-8 encoding: {e}")

# File handler with UTF-8 encoding
file_handler = logging.FileHandler(log_dir / "assistant.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger("AI_Assistant.Main")


class AssistantApp:
    """Main application controller - Complete standalone version"""
    
    def __init__(self):
        self.input_queue = queue.Queue()
        self.mode = "widget"  # widget or full
        self.widget: FloatingWidget = None
        self.full_gui: AssistantGUI = None
        self.system_tray: SystemTray = None
        self.assistant_thread: threading.Thread = None
        self.running = False
        
        # Components (will be initialized in assistant thread)
        self.processor = None
        self.tts_engine = None
        self.detector = None
        
    def start(self):
        """Start the assistant"""
        logger.info("[START] Jarvis Assistant starting for MSI Thin 15 B13UC...")
        logger.info("[SYSTEM] 16GB RAM, RTX 3050 4GB")
        
        # Check first run
        if should_run_wizard():
            logger.info("First run detected - showing setup wizard")
            wizard = FirstRunWizard()
            wizard.run()
            
            # Check if wizard completed
            if not Path(".env").exists():
                logger.error("Setup wizard incomplete - exiting")
                return
        
        # Start with floating widget
        self.show_widget()
    
    def show_widget(self):
        """Show floating widget mode"""
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
                daemon=False
            )
            self.assistant_thread.start()
        
        # Run widget (blocking)
        try:
            self.widget.run()
        except KeyboardInterrupt:
            self.shutdown()
    
    def show_full_gui(self):
        """Switch to full GUI mode"""
        if self.widget:
            self.widget.destroy()
            self.widget = None
        
        self.mode = "full"
        self.full_gui = AssistantGUI(self.input_queue)
        
        # Update processor GUI reference
        if self.processor:
            self.processor.gui = self.full_gui
        
        try:
            self.full_gui.run()
        except KeyboardInterrupt:
            self.shutdown()
    
    def show_widget_from_tray(self):
        """Show widget from system tray"""
        if not self.widget:
            threading.Thread(target=self.show_widget, daemon=True).start()
    
    def hide_widget(self):
        """Hide widget (minimize to tray)"""
        if self.widget:
            self.widget.destroy()
            self.widget = None
            logger.info("Widget hidden - available in system tray")
    
    def trigger_voice_command(self):
        """Trigger voice command from system tray"""
        self.input_queue.put(("WAKE_WORD_DETECTED", "manual"))
    
    def open_settings(self):
        """Open settings dialog"""
        try:
            dialog = SettingsDialog()
            dialog.show()
        except Exception as e:
            logger.error(f"Failed to open settings: {e}")
    
    def open_stats(self):
        """Open statistics dashboard"""
        try:
            from stats_dashboard import StatsDashboard
            dashboard = StatsDashboard()
            threading.Thread(target=dashboard.run, daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to open stats: {e}")
    
    def handle_widget_command(self, event_type: str, data):
        """Handle commands from floating widget"""
        if event_type == "OPEN_CHAT":
            # Switch to full GUI
            threading.Thread(target=self.show_full_gui, daemon=True).start()
        elif event_type == "OPEN_SETTINGS":
            self.open_settings()
        elif event_type == "SHOW_STATS":
            self.open_stats()
        else:
            # Forward to assistant
            self.input_queue.put((event_type, data))
    
    def run_assistant_thread(self):
        """Run the main assistant logic"""
        asyncio.run(self.assistant_logic())
    
    async def assistant_logic(self):
        """Main assistant logic loop"""
        loop = asyncio.get_running_loop()
        
        try:
            # Initialize components
            logger.info("[INIT] Initializing components...")
            predictor = PredictiveModel()
            memory = MemoryManager(predictor)
            self.tts_engine = TextToSpeech()
            self.tts_engine.start(loop)
            
            # FIXED: Wrap app scanner in try-catch
            try:
                apps = AppManager(memory)
                logger.info(f"[APPS] Found {len(apps.apps)} applications")
            except Exception as e:
                logger.error(f"[APPS] Error scanning apps: {e}")
                # Create empty app manager
                apps = None
            
            # Get current GUI reference
            current_gui = self.widget if self.mode == "widget" else self.full_gui
            
            # Create processor (even if apps is None)
            self.processor = CommandProcessor(
                gui=current_gui,
                app_manager=apps if apps else self._create_fallback_app_manager(memory),
                memory_manager=memory,
                tts_engine=self.tts_engine,
                predictor=predictor
            )
            self.processor.set_event_loop(loop)
            
            # Start wake word detector
            self.detector = WakeWordDetector(self.input_queue, self.tts_engine)
            detector_task = asyncio.create_task(self.detector.run())
            
            # STT
            stt = SpeechToText(
                Config.WHISPER_MODEL_SIZE,
                current_gui
            )
            
            # Load models in background
            asyncio.create_task(self.preload_models(stt, apps))
            
            logger.info("[READY] Jarvis is ready! Say 'Hey Jarvis' or click the orb")
            
            # Update system tray
            if self.system_tray:
                self.system_tray.notify(
                    "Jarvis Ready",
                    "Your personal assistant is now active!",
                    duration=3
                )
            
            # Main event loop
            while self.running:
                try:
                    event_type, data = await asyncio.wait_for(
                        loop.run_in_executor(None, self.input_queue.get),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                if event_type == "EXIT":
                    break
                
                # Update states
                if self.widget:
                    self.widget.set_state("thinking")
                if self.system_tray:
                    self.system_tray.update_icon("thinking")
                
                command_text = None
                
                if event_type == "WAKE_WORD_DETECTED":
                    if self.widget:
                        self.widget.set_state("listening")
                    if self.system_tray:
                        self.system_tray.update_icon("listening")
                    
                    command_text = await asyncio.to_thread(stt.listen_and_transcribe)
                    
                elif event_type == "TEXT_COMMAND":
                    command_text = data
                    
                elif event_type == "SUGGESTION_ACCEPT":
                    command_text = self.processor.handle_suggestion_accept(data)
                    
                elif event_type == "SUGGESTION_DISMISS":
                    self.processor.handle_suggestion_dismiss(data)
                    continue
                
                if command_text:
                    if self.widget:
                        self.widget.set_state("thinking")
                    if self.system_tray:
                        self.system_tray.update_icon("thinking")
                    
                    result = await self.processor.execute(command_text)
                    
                    if result == "exit":
                        self.running = False
                        break
                
                # Back to idle
                if self.widget:
                    self.widget.set_state("idle")
                if self.system_tray:
                    self.system_tray.update_icon("idle")
            
            # Cleanup
            logger.info("[SHUTDOWN] Shutting down...")
            self.detector.stop()
            await detector_task
            await self.processor.close()
            self.tts_engine.close()
            
        except Exception as e:
            logger.critical("[ERROR] Critical error: %s", e, exc_info=True)
            if self.system_tray:
                self.system_tray.notify(
                    "Jarvis Error",
                    f"Critical error occurred: {str(e)[:50]}",
                    duration=5
                )
        finally:
            self.running = False
            logger.info("[STOPPED] Assistant stopped")
    
    def _create_fallback_app_manager(self, memory):
        """Create a minimal fallback app manager"""
        class FallbackAppManager:
            def __init__(self):
                self.apps = {}
            def find_best_match(self, query):
                return None
        return FallbackAppManager()
    
    async def preload_models(self, stt: SpeechToText, apps: AppManager):
        """Preload models in background"""
        try:
            logger.info("[MODELS] Loading models...")
            
            # Show loading state
            if self.widget:
                self.widget.set_state("thinking")
            
            # Load in parallel
            tasks = [asyncio.to_thread(stt.load_model)]
            if apps:
                tasks.append(asyncio.to_thread(lambda: apps.apps))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info("[MODELS] Models loaded successfully")
            
            # Back to idle
            if self.widget:
                self.widget.set_state("idle")
                
        except Exception as e:
            logger.error(f"[MODELS] Error loading models: {e}")
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("[EXIT] Goodbye!")
        self.running = False
        self.input_queue.put(("EXIT", None))
        
        # Stop system tray
        if self.system_tray:
            self.system_tray.stop()
        
        # Destroy widgets
        if self.widget:
            self.widget.destroy()
        if self.full_gui:
            try:
                self.full_gui.root.quit()
            except:
                pass
        
        # Wait for thread
        if self.assistant_thread and self.assistant_thread.is_alive():
            self.assistant_thread.join(timeout=5)
        
        sys.exit(0)


def main():
    """Entry point"""
    # Print banner (ASCII art, no emojis)
    print("""
========================================
        JARVIS AI ASSISTANT
     Your Personal Computing Buddy
                                        
  Optimized for MSI Thin 15 B13UC      
  16GB RAM | RTX 3050 4GB | Windows 11 
========================================
    """)
    
    try:
        app = AssistantApp()
        app.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical("Fatal error: %s", e, exc_info=True)
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()