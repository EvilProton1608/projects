import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the secret key
SECRET_KEY = os.getenv('SECRET_KEY', 'default_fallback_value')

