from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routers import auth, products, scans

app = FastAPI(title="LegalMetriX API")

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# CORS Configuration
raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "https://legal-metrology-dist-three.vercel.app,http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8000,http://localhost:8080,*"
)
allowed_origins = [o.strip().rstrip('/') for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(scans.router)

@app.on_event("startup")
def startup_event():
    from app.database import SessionLocal, Base, engine
    from app.models import User
    from app.auth import get_password_hash
    import app.models
    
    # Auto-create tables for local development database
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed the officer test user if not exists
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "officer@test.com").first()
        if not user:
            default_user = User(
                name="Test Officer",
                email="officer@test.com",
                password_hash=get_password_hash("password123"),
                role="officer"
            )
            db.add(default_user)
            db.commit()
    finally:
        db.close()

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the LegalMetriX API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "LegalMetriX API"
    }
