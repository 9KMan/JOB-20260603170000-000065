"""Main application entry point."""

from fastapi import FastAPI

from src.routes import router

app = FastAPI()
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Build Worker API"}