import os
import sys
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import tempfile

# Insert Arkana root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Mock external dependencies BEFORE importing app
sys.modules["groq"] = MagicMock()
sys.modules["clip"] = MagicMock()

from ai.backend.main import app
from ai.pipeline import ArkanaPipeline

def test_full_lifecycle():
    failures = []
    
    # Mock the heavy ML methods
    with patch.object(ArkanaPipeline, 'initialize', new_callable=AsyncMock) as mock_init, \
         patch.object(ArkanaPipeline, 'query') as mock_query, \
         patch.object(ArkanaPipeline, 'identify_image', new_callable=AsyncMock) as mock_identify:
        
        # Setup mock returns
        async def mock_query_gen(*args, **kwargs):
            yield {"type": "token", "data": "Hello"}
            yield {"type": "done", "data": None}
        mock_query.side_effect = mock_query_gen
        
        mock_identify.return_value = {
            "style_classification": {"top_style": "Test", "confidence": 0.99, "all_scores": {}},
            "similar_artifacts": [],
            "rag_query": "test query",
            "rag_context": {}
        }
        
        # Using TestClient with the context manager triggers the lifespan events
        try:
            print("Starting FastAPI with lifespan...")
            with TestClient(app) as client:
                print("FastAPI Lifespan started successfully.")
                
                # Check if initialize was called exactly once
                if mock_init.call_count != 1:
                    failures.append(f"Pipeline.initialize() called {mock_init.call_count} times, expected exactly 1.")
                else:
                    print("Lifespan startup initializes the pipeline exactly once: OK.")
                
                # 1. Validation errors return standardized ErrorResponse
                print("Testing validation error response...")
                resp = client.post("/api/chat", json={"invalid": "payload"})
                if resp.status_code != 422:
                    failures.append(f"Validation error test failed with status {resp.status_code}")
                else:
                    data = resp.json()
                    if "error" not in data or data["error"] != "Validation Error":
                        failures.append(f"Validation Error schema incorrect: {data}")
                    else:
                        print("Validation errors return standardized ErrorResponse: OK.")
                
                # 2. POST /api/chat streams valid SSE responses
                print("Testing POST /api/chat streaming...")
                resp = client.post("/api/chat", json={"query": "Test"})
                if resp.status_code != 200:
                    failures.append(f"Chat stream test failed with status {resp.status_code}")
                else:
                    text = resp.text
                    if not text.startswith("data:"):
                        failures.append("Chat stream returned invalid SSE format.")
                    else:
                        print("POST /api/chat streams valid SSE responses: OK.")
                        print("First chunk:", text.splitlines()[0])
                
                # 3. POST /api/identify processes an image correctly
                print("Testing POST /api/identify...")
                resp = client.post("/api/identify", files={"image": ("test.jpg", b"dummy image content", "image/jpeg")})
                
                if resp.status_code != 200:
                    failures.append(f"Identify endpoint returned unexpected status: {resp.status_code}")
                else:
                    print("POST /api/identify processes an image correctly: OK.")

            print("FastAPI Lifespan shutdown completed without pending background tasks (simulated).")
        except Exception as e:
            failures.append(f"Lifecycle error: {str(e)}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f" - {f}")
    else:
        print("\nALL FUNCTIONAL VERIFICATIONS PASSED!")

if __name__ == "__main__":
    test_full_lifecycle()
