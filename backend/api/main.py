import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "retrieval"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "guardrails"))
sys.path.append(os.path.dirname(__file__))

from finbot import ask_finbot

app = FastAPI(title="FinBot API", version="1.0.0")

# Allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Demo users (in production this would be a database) ───────────────────────
DEMO_USERS = {
    "alice":   {"password": "alice123",   "role": "employee",    "name": "Alice Johnson"},
    "bob":     {"password": "bob123",     "role": "finance",     "name": "Bob Smith"},
    "charlie": {"password": "charlie123", "role": "engineering", "name": "Charlie Brown"},
    "diana":   {"password": "diana123",   "role": "marketing",   "name": "Diana Prince"},
    "eve":     {"password": "eve123",     "role": "c_level",     "name": "Eve Wilson"},
}

ROLE_COLLECTIONS = {
    "employee":    ["general"],
    "finance":     ["finance", "general"],
    "engineering": ["engineering", "general"],
    "marketing":   ["marketing", "general"],
    "c_level":     ["general", "finance", "engineering", "marketing"],
}

# ── Request/Response models ────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    query:      str
    username:   str
    role:       str
    session_id: str

# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "FinBot API is running"}

@app.post("/login")
def login(request: LoginRequest):
    user = DEMO_USERS.get(request.username.lower())
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {
        "success":     True,
        "username":    request.username,
        "name":        user["name"],
        "role":        user["role"],
        "collections": ROLE_COLLECTIONS[user["role"]],
    }

@app.post("/chat")
def chat(request: ChatRequest):
    result = ask_finbot(
        query      = request.query,
        user_role  = request.role,
        session_id = request.session_id,
    )
    return {
        "success":        result["success"],
        "response":       result.get("response"),
        "message":        result.get("message"),
        "route":          result.get("route"),
        "guardrail_type": result.get("guardrail_type"),
        "warning":        result.get("warning"),
        "stage":          result.get("stage"),
        "chunks":         [
            {
                "source_document": c["source_document"],
                "page_number":     c["page_number"],
                "section_title":   c["section_title"],
                "score":           c["score"],
            }
            for c in result.get("chunks", [])
        ],
    }

@app.get("/users")
def get_users():
    return [
        {
            "username":    username,
            "name":        user["name"],
            "role":        user["role"],
            "collections": ROLE_COLLECTIONS[user["role"]],
        }
        for username, user in DEMO_USERS.items()
    ]
