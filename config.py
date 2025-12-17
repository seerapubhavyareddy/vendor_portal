# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:db_admin@vendor-portal-db.cszf6hop4o2t.us-east-2.rds.amazonaws.com:5432/mannbiome")

# JWT Authentication settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS settings
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
CORS_ORIGINS = [FRONTEND_URL]
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "")
if CORS_ORIGINS_STR:
    CORS_ORIGINS.extend(CORS_ORIGINS_STR.split(","))

# Server settings
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Application settings
APP_NAME = "MannBiome API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "API for the MannBiome platform with OAuth authentication"

# AWS S3 settings for document uploads
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "clinical-trial-documents-mannbiome")
S3_PRESIGNED_URL_EXPIRATION = int(os.getenv("S3_PRESIGNED_URL_EXPIRATION", "604800"))  # 7 days in seconds