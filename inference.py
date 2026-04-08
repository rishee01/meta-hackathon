import os
import asyncio
import requests
from openai import OpenAI

ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_client():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY environment variable must be set")
    return OpenAI(api_key=OPENAI_API_KEY, base_url=API_BASE_URL)

def reset_env(task_level="easy"):
    response = requests.post(f"{ENV_BASE_URL}/reset", json={"task_level": task_level})
    response.raise_for_status()
    return response.json()

def step_env(action):
    response = requests.post(f"{ENV_BASE_URL}/step", json={"action": action})
    response.raise_for_status()
    return response.json()

def get_prompt(observation, task_level):
    if task_level == "easy":
        return f"Classify this email as 'spam' or 'not_spam'. Consider if it's promotional, unsolicited, or contains suspicious links.\n\nEmail:\n{observation['email_content']}\n\nRespond with only 'spam' or 'not_spam'."
    elif task_level == "medium":
        return f"Classify the priority of this email as 'high', 'medium', or 'low'. High for urgent/time-sensitive, medium for important but not immediate, low for casual.\n\nEmail:\n{observation['email_content']}\n\nRespond with only 'high', 'medium', or 'low'."
    elif task_level == "hard":
        thread = "\n".join(observation.get('thread_history', []))
        return f"Write a professional email reply to this message. Address all points raised, be polite, and provide appropriate response. Do not be generic.\n\nEmail:\n{observation['email_content']}\n\nThread history:\n{thread}\n\nWrite the full reply email."

async def run_inference(task_level="easy"):
    print("[START]")
    obs_data = reset_env(task_level)
    total_score = 0.0
    steps = 0
    while True:
        observation = obs_data["observation"]
        prompt = get_prompt(observation, task_level)
        response = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500 if task_level == "hard" else 50
        )
        action_text = response.choices[0].message.content.strip()
        if task_level in ["easy", "medium"]:
            action = {"classification": action_text, "reply": ""}
        else:
            action = {"classification": "", "reply": action_text}
        step_data = step_env(action)
        reward = step_data["reward"]["score"]
        total_score += reward
        steps += 1
        print(f"[STEP] Task: {task_level}, Step: {steps}, Score: {reward:.3f}")
        if step_data["done"]:
            break
        obs_data = step_data
    avg_score = total_score / steps if steps > 0 else 0.0
    print(f"[END] Average Score: {avg_score:.3f}")
    return avg_score

if __name__ == "__main__":
    # Run for each task level
    scores = []
    for level in ["easy", "medium", "hard"]:
        score = asyncio.run(run_inference(level))
        scores.append(score)
    overall = sum(scores) / len(scores)
    print(f"Overall Score: {overall:.3f}")