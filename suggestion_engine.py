from datetime import datetime
from typing import List, Optional
from memory_manager import MemoryManager
from predictive_model import PredictiveModel
import logging

logger = logging.getLogger("AI_Assistant.SuggestionEngine")

class SuggestionEngine:
    
    """Generates proactive suggestions using a hybrid of ML and rule-based logic."""
    def __init__(self, memory_manager: MemoryManager, predictor: PredictiveModel):
        self.memory_manager = memory_manager
        self.predictor = predictor
        # Initial training on startup
        logger.info("Performing initial training of predictive model...")
        self.predictor.train(self.memory_manager.export_training_data())

    def generate_suggestions(self) -> List[str]:
        """Generates a list of proactive, context-aware suggestions for the user."""
        suggestions = []
        now = datetime.now()
        hour, wday = now.hour, now.weekday()

        # --- Step 1: Get a prediction from the auto-retrained model ---
        predicted_command = self.predictor.predict(now.hour, now.weekday())
        if predicted_command:
            suggestions.append(f"Based on your routine, should I run the command '{predicted_command}'?")

        # --- Step 2: Fallback to rule-based suggestions ---
        try:
            # Frequent commands (only if no ML prediction was made and is different)
            frequent = self.memory_manager.get_frequent_commands()
            if frequent and frequent[0][0] != predicted_command:
                most_common_cmd = frequent[0][0]
                suggestions.append(f"You often ask me to '{most_common_cmd}'. Would you like to do that now?")

            # Time-based suggestions
            if 7 <= now.hour < 10:
                suggestions.append("Good morning! How about checking today's weather or news?")
           
            if 8 <= hour < 10 and wday < 5:
                suggestions.append("Good morning! Open VS Code and Chrome?")
            if 13 <= hour < 14:
                suggestions.append("Time for a break – play some lo-fi?")
            if 17 <= hour < 19:
                apps = self.memory_manager.get_frequent_commands(3)
            if apps:
                suggestions.append(f"Wrap-up? Close {', '.join(a[0] for a in apps)}?")
            
            # Upcoming reminders
            upcoming_reminders = self.memory_manager.get_reminders(time_window_hours=1)
            for reminder in upcoming_reminders:
                suggestions.append(f"Just a heads-up, you have a reminder coming up for: {reminder['text']}.")

        except Exception as e:
            logger.error(f"Failed to generate rule-based suggestions: {e}")

        return suggestions[:3] # Return the best 3 suggestions
