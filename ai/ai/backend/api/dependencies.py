from fastapi import Request
from ai.pipeline import ArkanaPipeline

def get_pipeline(request: Request) -> ArkanaPipeline:
    """
    Dependency to retrieve the warmed-up pipeline from the FastAPI application state.
    """
    return request.app.state.pipeline
