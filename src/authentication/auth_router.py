from fastapi import HTTPException, FastAPI
from pathlib import Path
from dotenv import load_dotenv
import os
#from src.authentication.auth_schema import auth_credentials

app = FastAPI(title="My API", description="Authentication API")#, version="1.0.0")

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
db = os.getenv("DATABASE_URL")

class authentication:
   def authenticate_user(self, username: str, password: str) -> bool:
        # Implement your authentication logic here
        if username == "admin" and password == "password":
            return True
        return False