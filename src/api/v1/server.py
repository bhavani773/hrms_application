from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.models.base import Base, engine
from src.api.v1.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Server starting...")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")
    
    # Seed basic data if database is empty
    try:
        from src.scripts.seed_data import seed_basic_data
        seed_basic_data()
    except Exception as e:
        print(f"Data seeding failed: {e}")
    
    yield
    
    # Shutdown
    print("Application shutdown")

app = FastAPI(
    title="Agentic HR Documents Compliance",
    description="AI-powered HR document compliance system using Blackboard Pattern",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Agentic HR Documents Compliance System", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}