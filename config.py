import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # Base directory of the project
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Flask Settings
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "soc-default-secret-key")
    CLIENT_PORT = int(os.environ.get("CLIENT_PORT", 5001))
    DIRECTOR_PORT = int(os.environ.get("DIRECTOR_PORT", 5005))
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    
    # Database Settings
    DB_NAME = os.path.abspath(os.path.join(BASE_DIR, "soc.db"))
    PARENT_DB_NAME = os.path.abspath(os.path.join(BASE_DIR, "parent.db"))
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    # AI Engine Settings
    USE_AI = os.environ.get("USE_AI", "True").lower() == "true"
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL")
    OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/generate")
    
    # Multi-Tenant / Director Settings
    CLIENT_NAME = os.environ.get("CLIENT_NAME", "Standalone-SOC")
    PARENT_SERVER_URL = os.environ.get("PARENT_SERVER_URL")
    CLIENT_PUBLIC_URL = os.environ.get("CLIENT_PUBLIC_URL")
    
    # Ingestion Settings
    INGEST_URL = os.environ.get("INGEST_URL", f"http://127.0.0.1:{CLIENT_PORT}/api/v2/ingest")
    
    @staticmethod
    def print_config():
        """Debug helper to show loaded config (masking sensitive keys)."""
        print(f"--- SOC CONFIGURATION ---")
        print(f"Client Name: {Config.CLIENT_NAME}")
        print(f"DB Path: {Config.DB_NAME}")
        print(f"Gemini Key: {'[SET]' if Config.GEMINI_API_KEY else '[NOT SET]'}")
        print(f"Parent URL: {Config.PARENT_SERVER_URL or 'Standalone Mode'}")
        print(f"-------------------------")

if __name__ == "__main__":
    Config.print_config()
