import serverless_wsgi
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the Flask app
from flask_app import app

def handler(event, context):
    # Log basic information for debugging
    print("Function invoked with path:", event.get("path", "unknown path"))
    
    # Handle the request using serverless_wsgi
    return serverless_wsgi.handle_request(app, event, context)