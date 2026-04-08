from typing import Dict, Any, List
import re

def grade_easy(action: str, correct: str) -> float:
    """Grade spam classification. Exact match for clear cases, partial for ambiguous."""
    action_clean = action.lower().strip()
    correct_clean = correct.lower().strip()
    if action_clean == correct_clean:
        return 1.0
    # No partial credit for binary classification to maintain determinism
    return 0.0

def grade_medium(action: str, correct: str) -> float:
    """Grade priority classification with partial credit for close matches."""
    action_clean = action.lower().strip()
    correct_clean = correct.lower().strip()
    if action_clean == correct_clean:
        return 1.0
    # Partial credit for adjacent priorities
    priorities = ["low", "medium", "high"]
    if action_clean in priorities and correct_clean in priorities:
        diff = abs(priorities.index(action_clean) - priorities.index(correct_clean))
        if diff == 1:
            return 0.5
    return 0.0

def grade_hard(reply: str, expected_keywords: List[str], tone: str, thread_context: List[str] = None) -> Dict[str, float]:
    """Advanced grading for reply quality. Returns component scores."""
    reply_lower = reply.lower()
    words = reply.split()
    
    # Keyword coverage (0-1): How many expected keywords are addressed
    keyword_score = 0.0
    if expected_keywords:
        found = sum(1 for kw in expected_keywords if kw.lower() in reply_lower)
        keyword_score = found / len(expected_keywords)
    
    # Intent satisfaction (0-1): Addresses main points
    intent_score = 0.0
    if "apology" in expected_keywords and ("sorry" in reply_lower or "apologize" in reply_lower):
        intent_score += 0.3
    if "refund" in expected_keywords and ("refund" in reply_lower or "return" in reply_lower):
        intent_score += 0.3
    if "schedule" in expected_keywords and ("schedule" in reply_lower or "call" in reply_lower):
        intent_score += 0.4
    intent_score = min(intent_score, 1.0)
    
    # Tone correctness (0-1)
    tone_score = 0.0
    if tone == "professional":
        if any(word in reply_lower for word in ["thank you", "please", "regards", "sincerely", "dear"]):
            tone_score = 0.8
        if "!" not in reply or reply.count("!") <= 1:
            tone_score += 0.2
    elif tone == "urgent":
        if any(word in reply_lower for word in ["immediately", "urgent", "asap", "now", "critical"]):
            tone_score = 0.8
        if "!" in reply:
            tone_score += 0.2
    elif tone == "casual":
        if len(words) < 50 and not any(word in reply_lower for word in ["regards", "sincerely"]):
            tone_score = 0.8
        if any(word in reply_lower for word in ["hey", "hi", "thanks"]):
            tone_score += 0.2
    else:
        tone_score = 0.5  # Neutral
    
    # Length quality (0-1): Penalize too short or too long
    length_score = 1.0
    if len(words) < 10:
        length_score = 0.3
    elif len(words) < 20:
        length_score = 0.7
    elif len(words) > 150:
        length_score = 0.6
    elif len(words) > 200:
        length_score = 0.4
    
    # Context awareness (0-1): References thread if present
    context_score = 1.0
    if thread_context:
        thread_text = " ".join(thread_context).lower()
        # Check if reply references previous messages
        if any(word in reply_lower for word in ["regarding", "following", "as discussed", "previously"]):
            context_score = 1.0
        elif any(word for word in thread_text.split() if word in reply_lower):
            context_score = 0.8
        else:
            context_score = 0.5
    
    # Anti-cheating: Penalize generic responses
    generic_penalty = 0.0
    generic_phrases = ["i don't know", "please provide more information", "let me check", "i will get back to you"]
    if any(phrase in reply_lower for phrase in generic_phrases):
        generic_penalty = 0.3
    
    # Coherence: Basic check for sentence structure
    coherence_score = 1.0
    if not reply.strip().endswith((".", "!", "?")):
        coherence_score = 0.8
    if len(set(words)) < len(words) * 0.4:  # Too repetitive
        coherence_score = 0.6
    
    # Weighted final score
    weights = {
        "keyword": 0.25,
        "intent": 0.25,
        "tone": 0.2,
        "length": 0.1,
        "context": 0.1,
        "coherence": 0.1
    }
    
    final_score = (
        keyword_score * weights["keyword"] +
        intent_score * weights["intent"] +
        tone_score * weights["tone"] +
        length_score * weights["length"] +
        context_score * weights["context"] +
        coherence_score * weights["coherence"]
    ) - generic_penalty
    
    final_score = max(0.0, min(1.0, final_score))
    
    return {
        "overall": final_score,
        "keyword_coverage": keyword_score,
        "intent_satisfaction": intent_score,
        "tone_correctness": tone_score,
        "length_quality": length_score,
        "context_awareness": context_score,
        "coherence": coherence_score
    }

def get_grader(task_level: str):
    if task_level == "easy":
        return grade_easy
    elif task_level == "medium":
        return grade_medium
    elif task_level == "hard":
        return grade_hard
    return lambda *args: 0.0