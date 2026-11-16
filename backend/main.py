"""
SmartKhet 2.0 — Server Runner
==============================
Command line runner for uvicorn.
Usage:
    python main.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

