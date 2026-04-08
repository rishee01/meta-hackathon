import asyncio
from typing import Any, Dict, List, Optional
from .models import Observation, Action, Reward
from .tasks import get_task_config
from .graders import get_grader

class EmailTriageEnvironment:
    def __init__(self, task_level: str = "easy"):
        self.task_level = task_level
        self.task_config = get_task_config(task_level)
        self.grader = get_grader(task_level)
        self.emails = self._load_emails()
        self.current_email_idx = 0
        self.processed: set[int] = set()
        self.state_data: Dict[str, Any] = {}
        self.previous_actions: List[str] = []
        self.episode_rewards: List[float] = []
        self.thread_memory: Dict[str, List[str]] = {}  # Track threads across episodes

    def _load_emails(self) -> List[Dict[str, Any]]:
        # Highly realistic emails with noise, typos, threads, adversarial cases
        return [
            {
                "content": "Subject: Congrats! U won FREE iPhone 15!\n\nHey there,\n\nYou've been selected for our lucky draw. Click http://bit.ly/free-iphone to claim your prize NOW! No strings attached.\n\nBest,\nPrize Team",
                "spam": "spam",
                "priority": "low",
                "reply_keywords": [],
                "tone": "",
                "thread": [],
                "thread_id": None
            },
            {
                "content": "Subject: Team Meeting Tomorrow 10 AM\n\nHi everyone,\n\nReminder: Our weekly sync is at 10 AM tomorrow in Conference Room A. Agenda attached.\n\nPlease confirm attendance.\n\nRegards,\nSarah Johnson\nProject Manager",
                "spam": "not_spam",
                "priority": "high",
                "reply_keywords": ["confirm", "attendance", "agenda"],
                "tone": "professional",
                "thread": [],
                "thread_id": "meeting_001"
            },
            {
                "content": "Subject: Re: Team Meeting Tomorrow 10 AM\n\nThanks Sarah,\n\nI'll be there. Can you send the updated budget figures?\n\nBest,\nMike",
                "spam": "not_spam",
                "priority": "medium",
                "reply_keywords": ["budget", "figures", "updated"],
                "tone": "professional",
                "thread": ["Original: Team Meeting Tomorrow 10 AM - Agenda attached"],
                "thread_id": "meeting_001"
            },
            {
                "content": "Subject: URGENT: Server Down - Action Required\n\nThe production server crashed at 3:45 PM. All services affected. IT team investigating.\n\nPlease hold all deployments until further notice.\n\n- DevOps Alert",
                "spam": "not_spam",
                "priority": "high",
                "reply_keywords": ["acknowledged", "monitoring", "update"],
                "tone": "urgent",
                "thread": [],
                "thread_id": "incident_001"
            },
            {
                "content": "Subject: Lunch?\n\nhey mike, wanna grab lunch today? around noon?\n\nalex",
                "spam": "not_spam",
                "priority": "low",
                "reply_keywords": ["sure", "noon", "where"],
                "tone": "casual",
                "thread": [],
                "thread_id": None
            },
            # Ambiguous spam: Amazon promotion (legitimate but spammy)
            {
                "content": "Subject: Your Amazon Order #123-4567890-1234567\n\nHello,\n\nYour package has shipped! Track it here: amazon.com/track\n\nAs a Prime member, you qualify for 30% off your next purchase. Limited time offer.\n\nHappy shopping,\nAmazon Customer Service",
                "spam": "not_spam",  # Legitimate, but promotional
                "priority": "low",
                "reply_keywords": [],
                "tone": "",
                "thread": [],
                "thread_id": None
            },
            # Phishing attempt
            {
                "content": "Subject: Account Security Alert\n\nDear Customer,\n\nYour account has been locked due to suspicious activity. Verify your identity immediately at: secure-bank-login.com\n\nFailure to verify within 24 hours will result in permanent suspension.\n\nBank Security Team",
                "spam": "spam",
                "priority": "low",
                "reply_keywords": [],
                "tone": "",
                "thread": [],
                "thread_id": None
            },
            # Medium priority: Follow-up
            {
                "content": "Subject: Follow-up on Q3 Budget Proposal\n\nHi Team,\n\nFollowing up on the budget discussion from last week. Please review the attached proposal and provide feedback by Friday EOD.\n\nLet me know if you need any clarifications.\n\nBest regards,\nFinance Dept",
                "spam": "not_spam",
                "priority": "medium",
                "reply_keywords": ["reviewed", "feedback", "clarifications"],
                "tone": "professional",
                "thread": [],
                "thread_id": "budget_q3"
            },
            # Thread continuation
            {
                "content": "Subject: Re: Re: Follow-up on Q3 Budget Proposal\n\nThanks for the proposal. I have some concerns about the marketing budget allocation. Can we discuss this in tomorrow's meeting?\n\nOn Thu, Finance Dept wrote:\n> Please review... by Friday EOD",
                "spam": "not_spam",
                "priority": "high",
                "reply_keywords": ["meeting", "tomorrow", "concerns", "marketing", "budget"],
                "tone": "professional",
                "thread": ["Original: Q3 Budget Proposal - attached", "Previous: Thanks for the proposal..."],
                "thread_id": "budget_q3"
            },
            # Hard: Complex complaint
            {
                "content": "Subject: Complaint: Poor Customer Service Experience\n\nDear Support Team,\n\nI am extremely disappointed with my recent interaction with your company. The product I received was damaged upon arrival, and when I contacted support, I was put on hold for 45 minutes only to be told 'we can't help you.'\n\nI demand a full refund and a written apology. Additionally, please explain how this happened and what measures you'll take to prevent it.\n\nI expect a response within 24 hours.\n\nSincerely,\nFrustrated Customer",
                "spam": "not_spam",
                "priority": "high",
                "reply_keywords": ["apology", "refund", "investigation", "prevent", "response", "24 hours"],
                "tone": "professional",
                "thread": [],
                "thread_id": "complaint_001"
            },
            # Ambiguous priority: Doctor appointment
            {
                "content": "Subject: Doctor's Appointment Reminder\n\nHi,\n\nJust a reminder that you have a doctor's appointment tomorrow at 2 PM. Please arrive 15 minutes early.\n\nIf you need to reschedule, call us at least 24 hours in advance.\n\nBest,\nMedical Clinic",
                "spam": "not_spam",
                "priority": "medium",  # Important but not urgent
                "reply_keywords": ["noted", "appointment", "reschedule"],
                "tone": "professional",
                "thread": [],
                "thread_id": None
            },
            # Spam: Newsletter
            {
                "content": "Subject: Tech Newsletter - AI Breakthroughs\n\nThis Week's Highlights:\n- New AI model achieves 99% accuracy\n- Startup raises $50M for ML platform\n- Career tips for data scientists\n\nUnsubscribe: newsletter.com/unsub\n\nTechNews Daily",
                "spam": "spam",  # Unsolicited newsletter
                "priority": "low",
                "reply_keywords": [],
                "tone": "",
                "thread": [],
                "thread_id": None
            },
            # High priority: Security breach
            {
                "content": "Subject: SECURITY ALERT: Data Breach Detected\n\nURGENT: Our database has been compromised. All passwords must be changed immediately. Do not use work accounts until reset.\n\nIT Security will send reset instructions shortly.\n\nStay vigilant,\nSecurity Team",
                "spam": "not_spam",
                "priority": "high",
                "reply_keywords": ["password", "changed", "reset", "instructions"],
                "tone": "urgent",
                "thread": [],
                "thread_id": "security_breach"
            },
            # Medium: Project update request
            {
                "content": "Subject: Project Alpha Status Update\n\nHello Team,\n\nCan everyone please provide a quick status update on their tasks for Project Alpha? We need this by end of day to prepare for the stakeholder meeting.\n\nThanks in advance,\nProject Lead",
                "spam": "not_spam",
                "priority": "medium",
                "reply_keywords": ["status", "update", "tasks", "stakeholder", "meeting"],
                "tone": "professional",
                "thread": [],
                "thread_id": "project_alpha"
            },
            # Hard: Multi-part request with thread
            {
                "content": "Subject: Re: Project Alpha Status Update\n\nThanks for the updates everyone. John, your API integration is behind schedule. Can you provide an ETA and any blockers?\n\nAlso, Sarah, the design mockups look great but need some tweaks for mobile. Let's hop on a call tomorrow.\n\nOn Fri, Project Lead wrote:\n> Can everyone provide status updates...",
                "spam": "not_spam",
                "priority": "high",
                "reply_keywords": ["eta", "blockers", "api", "integration", "call", "tomorrow", "mockups", "mobile", "tweaks"],
                "tone": "professional",
                "thread": ["Original: Project Alpha Status Update", "John: My tasks are 80% complete", "Sarah: Mockups attached"],
                "thread_id": "project_alpha"
            }
        ]

    async def reset(self) -> Observation:
        self.current_email_idx = 0
        self.processed = set()
        self.state_data = {}
        self.previous_actions = []
        self.episode_rewards = []
        # Maintain thread memory across episodes
        return self._get_observation()

    async def step(self, action: Action) -> tuple[Optional[Observation], Reward, bool]:
        if self.current_email_idx >= len(self.emails):
            return None, Reward(score=0.0, feedback="Episode complete"), True
            
        email = self.emails[self.current_email_idx]
        
        # Calculate component scores
        components = {}
        
        if self.task_level == "easy":
            classification_score = self.grader(action.classification or "", email["spam"])
            components = {"classification_score": classification_score}
            final_score = classification_score
            
        elif self.task_level == "medium":
            priority_score = self.grader(action.classification or "", email["priority"])
            components = {"priority_score": priority_score}
            final_score = priority_score
            
        elif self.task_level == "hard":
            reply_components = self.grader(action.reply or "", email["reply_keywords"], email["tone"], email["thread"])
            components = reply_components
            final_score = reply_components["overall"]
        
        # Penalties
        penalty = 0.0
        
        # Repeated actions penalty
        if action.classification and action.classification in self.previous_actions[-3:]:
            penalty += 0.1
        if action.reply and action.reply in self.previous_actions[-3:]:
            penalty += 0.1
            
        # Urgent email ignored (for hard task)
        if self.task_level == "hard" and email["priority"] == "high":
            if len((action.reply or "").split()) < 20:
                penalty += 0.2
                
        # Irrelevant or hallucinated content
        if self.task_level == "hard" and action.reply:
            reply_lower = action.reply.lower()
            if "bitcoin" in reply_lower or "crypto" in reply_lower:  # Hallucinated
                penalty += 0.3
                
        # Looping behavior
        if len(self.previous_actions) >= 5 and all(act == self.previous_actions[-1] for act in self.previous_actions[-3:]):
            penalty += 0.2
            
        final_score = max(0.0, final_score - penalty)
        self.episode_rewards.append(final_score)
        
        # Feedback
        feedback_parts = [f"Task: {self.task_level}"]
        if components:
            feedback_parts.extend([f"{k}: {v:.2f}" for k, v in components.items() if k != "overall"])
        if penalty > 0:
            feedback_parts.append(f"Penalty: -{penalty:.2f}")
        feedback_parts.append(f"Final Score: {final_score:.2f}")
        feedback = " | ".join(feedback_parts)
        
        reward = Reward(score=final_score, feedback=feedback, components=components)
        
        # Update state
        self.processed.add(self.current_email_idx)
        action_str = action.classification or action.reply or ""
        self.previous_actions.append(action_str)
        
        # Update thread memory
        if email["thread_id"]:
            if email["thread_id"] not in self.thread_memory:
                self.thread_memory[email["thread_id"]] = []
            self.thread_memory[email["thread_id"]].append(action_str)
        
        self.current_email_idx += 1
        done = self.current_email_idx >= len(self.emails)
        next_obs = self._get_observation() if not done else None
        
        return next_obs, reward, done

    async def state(self) -> Dict[str, Any]:
        return {
            "current_email_idx": self.current_email_idx,
            "processed": list(self.processed),
            "state_data": self.state_data,
            "previous_actions": self.previous_actions[-10:],  # Last 10
            "episode_rewards": self.episode_rewards[-10:],
            "thread_memory": {k: v[-5:] for k, v in self.thread_memory.items()},  # Last 5 per thread
            "task_level": self.task_level
        }

    def _get_observation(self) -> Observation:
        if self.current_email_idx >= len(self.emails):
            raise ValueError("No more emails")
        email = self.emails[self.current_email_idx]
        
        # Include thread context from memory
        thread_history = email["thread"].copy()
        if email["thread_id"] and email["thread_id"] in self.thread_memory:
            thread_history.extend(self.thread_memory[email["thread_id"]])
            
        return Observation(
            email_content=email["content"],
            thread_history=thread_history,
            current_task=self.task_level
        )