# =============================================
# app.py
# FastAPI Entrypoint
# - Initializes database
# - Loads DSA engine (AVL + HashTable + Trie)
# - Ensures DB <-> DSA synchronization
# - Registers role-based routes
# - Acts as the thinnest possible server layer
# =============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from db import init_db, SessionLocal
from core.engine import DSAEngine
from core.loader import load_books_from_db
from services.fine_scheduler import start_scheduler, stop_scheduler

from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.librarian import router as librarian_router
from routes.member import router as member_router


# -------------------------------------------------
# 1) Create FastAPI App
# -------------------------------------------------
app = FastAPI(
    title="HIGH-LEVEL DSA LIBRARY SYSTEM",
    description="DSA-driven Library Management System (AVL, Hash, Trie)",
    version="1.0.0"
)


# -------------------------------------------------
# 2) CORS (allow frontend at localhost:3000 or 5173)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# -------------------------------------------------
# 3) Global DSA Engine (AVL + Hash + Trie)
# -------------------------------------------------
dsa_engine = DSAEngine()


# -------------------------------------------------
# 4) App startup hook
# -------------------------------------------------
@app.on_event("startup")
def startup_event():
    """
    At server startup:
    - Initialize DB
    - Load BOOK DATA from DB into DSA structures
    - Start fine scheduler
    """

    print("[INFO] Initializing MySQL connection...")
    init_db()

    print("[INFO] Loading database into DSA structures...")
    db = SessionLocal()
    try:
        load_books_from_db(db)
    finally:
        db.close()

    print("[INFO] Starting fine update scheduler...")
    start_scheduler()

    print("[INFO] System Ready (AVL + Trie + HashTable + Scheduler active)")


# -------------------------------------------------
# 4b) App shutdown hook
# -------------------------------------------------
@app.on_event("shutdown")
def shutdown_event():
    """At server shutdown, stop the scheduler"""
    print("[INFO] Shutting down scheduler...")
    stop_scheduler()


# -------------------------------------------------
# 5) API ROUTES (Role-Based + Auth)
# -------------------------------------------------
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(librarian_router)
app.include_router(member_router)


# -------------------------------------------------
# 6) Root endpoint
# -------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "Online",
        "message": "High-Level DSA Library System",
        "DSA": "AVL + HASH + TRIE active"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
