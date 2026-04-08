from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from env.environment import EmailTriageEnvironment
from env.models import Action, Reward

app = FastAPI(title="Email Triage Automation OpenEnv")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

env = None
history = []
session_metrics = {}

class ResetRequest(BaseModel):
    task_level: str = "easy"

class StepRequest(BaseModel):
    action: Action

def reset_metrics(task_level: str) -> dict:
    return {
        "task_level": task_level,
        "steps": 0,
        "total_score": 0.0,
        "average_score": 0.0,
        "last_score": None,
        "last_feedback": None,
    }

@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.post("/reset")
async def reset(request: ResetRequest):
    global env, history, session_metrics
    env = EmailTriageEnvironment(task_level=request.task_level)
    history = []
    session_metrics = reset_metrics(request.task_level)
    obs = await env.reset()
    return {"observation": obs.dict(), "metrics": session_metrics}

@app.post("/step")
async def step(request: StepRequest):
    if env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    try:
        next_obs, reward, done = await env.step(request.action)
        entry = {
            "step": len(history) + 1,
            "task_level": env.task_level,
            "classification": request.action.classification,
            "reply": request.action.reply,
            "score": reward.score,
            "feedback": reward.feedback,
            "done": done,
        }
        history.append(entry)
        session_metrics["steps"] += 1
        session_metrics["total_score"] += reward.score
        session_metrics["last_score"] = reward.score
        session_metrics["last_feedback"] = reward.feedback
        session_metrics["average_score"] = session_metrics["total_score"] / session_metrics["steps"]

        response = {"reward": reward.dict(), "done": done, "metrics": session_metrics}
        if next_obs:
            response["observation"] = next_obs.dict()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
async def get_state():
    if env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    return await env.state()

@app.get("/dashboard")
async def get_dashboard():
    if env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    return {"metrics": session_metrics, "history": history, "state": await env.state()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)