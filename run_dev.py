#!/usr/bin/env python
"""
Development server runner for Halcytone Content Generator
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "halcytone_content_generator.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )