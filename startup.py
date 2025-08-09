"""
Azure Web App startup script.
This file is used by Azure Web Apps to start the application.
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from main import app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Azure sets this)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
