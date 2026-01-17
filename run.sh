#!/bin/bash
# Run the FastAPI server using the current python environment
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
