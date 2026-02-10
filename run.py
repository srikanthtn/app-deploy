import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure the project root is in sys.path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Run Uvicorn
    # format: package.module:app_instance
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
