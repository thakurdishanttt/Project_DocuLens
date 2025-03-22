import os
import sys
import uvicorn

def main():
    # Add the project root to Python path
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, project_root)

    # Import the app after setting up the path
    from app.main import app

    # Run the application
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=8001, 
        reload=True
    )

if __name__ == "__main__":
    main()
