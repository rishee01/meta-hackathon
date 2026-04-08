from typing import Dict, Any

TASKS = {
    "easy": {
        "description": "Classify email as spam or not spam. Include tricky borderline cases like legitimate promotions or urgent-looking scams.",
        "action_type": "classification",
        "options": ["spam", "not_spam"]
    },
    "medium": {
        "description": "Classify email priority as high, medium, or low. Consider urgency, deadlines, and context.",
        "action_type": "classification",
        "options": ["high", "medium", "low"]
    },
    "hard": {
        "description": "Generate a high-quality professional reply that addresses all intents, matches tone, and respects thread context.",
        "action_type": "reply",
        "options": []  # Free text
    }
}

def get_task_config(task_level: str) -> Dict[str, Any]:
    return TASKS.get(task_level, TASKS["easy"])