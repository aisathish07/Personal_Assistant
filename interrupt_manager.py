import threading
import logging
from pynput import keyboard
from tts import TextToSpeech
from typing import Optional

logger = logging.getLogger("AI_Assistant.Interrupt")

class InterruptManager:
    """Listens for a global hotkey to interrupt speech (FIXED)."""
    def __init__(self, tts_engine: TextToSpeech):
        self.tts_engine = tts_engine
        self.listener: Optional[keyboard.Listener] = None
        
        try:
            def on_activate():
                self.on_activate()
            
            self.hotkey = keyboard.HotKey(
                keyboard.HotKey.parse('<ctrl>+<space>'),
                on_activate
            )
            # FIXED: Use daemon=False to ensure clean shutdown
            self.listener_thread = threading.Thread(
                target=self._run_listener,
                daemon=False
            )
            self.listener_thread.start()
            logger.info("Hotkey interrupt manager started. Press Ctrl+Space to interrupt.")
        except Exception as e:
            logger.error("Failed to initialize interrupt manager: %s", e)
            self.hotkey = None

    def _run_listener(self) -> None:
        """Run the keyboard listener (FIXED: safer exception handling)."""
        try:
            self.listener = keyboard.Listener(
                on_press=self.for_press,
                on_release=self.for_release
            )
            self.listener.start()
            self.listener.join()
        except Exception as e:
            logger.error("Listener thread error: %s", e)

    def on_activate(self) -> None:
        """Handle hotkey activation (FIXED: error handling)."""
        logger.info("Hotkey interrupt activated!")
        try:
            if self.tts_engine:
                self.tts_engine.stop()
        except Exception as e:
            logger.error("Error stopping TTS: %s", e)

    def for_press(self, key) -> None:
        """Handle key press (FIXED: better error handling)."""
        try:
            if self.hotkey:
                self.hotkey.press(self.listener.canonical(key))
        except AttributeError:
            pass  # Ignore special keys without canonical representation
        except Exception as e:
            logger.debug("Key press handling error: %s", e)

    def for_release(self, key) -> None:
        """Handle key release (FIXED: better error handling)."""
        try:
            if self.hotkey:
                self.hotkey.release(self.listener.canonical(key))
        except AttributeError:
            pass  # Ignore special keys without canonical representation
        except Exception as e:
            logger.debug("Key release handling error: %s", e)

    def stop(self) -> None:
        """Stop the interrupt manager (FIXED: graceful shutdown)."""
        try:
            if self.listener:
                self.listener.stop()
                logger.info("Interrupt manager stopped.")
        except Exception as e:
            logger.error("Error stopping interrupt manager: %s", e)