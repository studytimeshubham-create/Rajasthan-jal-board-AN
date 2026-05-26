import os
import firebase_admin
from firebase_admin import credentials

SERVICE_ACCOUNT_KEY_PATH = "serviceAccountKey.json"

_firebase_app = None

def get_firebase_app():
    """Initializes and returns the Firebase Admin app.
    Idempotent — returns existing app on repeat calls.
    """
    global _firebase_app
    if _firebase_app is None:
        # Search for serviceAccountKey.json in cwd, python_app, and parent dirs
        path = SERVICE_ACCOUNT_KEY_PATH
        if not os.path.exists(path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(script_dir, SERVICE_ACCOUNT_KEY_PATH)
            if not os.path.exists(path):
                parent_dir = os.path.dirname(script_dir)
                path = os.path.join(parent_dir, SERVICE_ACCOUNT_KEY_PATH)
                if not os.path.exists(path):
                    # Check default location
                    path = os.path.abspath(SERVICE_ACCOUNT_KEY_PATH)
        
        # If the file still doesn't exist, we don't crash immediately but wait until we actually try to load
        if not os.path.exists(path):
            raise FileNotFoundError(f"Service account key file not found. Please place serviceAccountKey.json at: {path}")
            
        cred = credentials.Certificate(path)
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app
