from dotenv import load_dotenv
load_dotenv()
# dBretreivalWithNewMetrics.py
from database import get_db, engine, SessionLocal, Base, metadata
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, MetaData, inspect, text, select, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, List
import os
from datetime import timedelta
from jose import JWTError, jwt
from patient_management import router as patient_router
from employee_management import router as employee_router
from config import CORS_ORIGINS as cors_origins




# Get CORS origins from environment
# cors_origins_env = os.getenv("CORS_ORIGINS", "")
# cors_origins = cors_origins_env.split(",") if cors_origins_env else []

print(f"🔧 Initial CORS Origins from env: {cors_origins}")



# Add default origins if empty, and always include all local dev ports for React/Vite
if not cors_origins:
    cors_origins = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://3b6akxpfpr.us-east-2.awsapprunner.com"
    ]

# Print for debugging
print(f"🔧 CORS Origins: {cors_origins}")

# cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
# print(f"🔍 Raw CORS_ORIGINS env: {cors_origins_env}")
# cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
# print(f"🔍 Parsed CORS origins: {cors_origins}")

# Import from auth.py
from auth import (
    Token,
    User,
    TokenData,
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
    get_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
    ALGORITHM,
    SECRET_KEY
)


app = FastAPI()

# Debug endpoint to print the actual JWT secret key being used
@app.get("/debug-secret")
def debug_secret():
    from config import JWT_SECRET_KEY
    return {"JWT_SECRET_KEY": JWT_SECRET_KEY}

# Enable CORS to allow JavaScript from your frontend to access the API

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include patient management router
app.include_router(patient_router)
# Include employee management router
app.include_router(employee_router)

# Include vendor clinical trial router (ADD THIS)
from vendor_clinical_api import router as clinical_router
app.include_router(clinical_router)


# Complete the OAuth setup with our get_db function
def get_current_user_with_db(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger("auth-debug")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    logger.info(f"🔑 Token received: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"✅ JWT decoded payload: {payload}")
        username: str = payload.get("sub")
        if username is None:
            logger.warning("❌ JWT payload missing 'sub' (username)")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.error(f"❌ JWTError: {e}")
        raise credentials_exception
    
    user = get_user(db, username=username)
    if user is None:
        logger.warning(f"❌ No user found in DB for username: {username}")
        raise credentials_exception
    logger.info(f"✅ User found in DB: {user.username}, role: {user.role}, disabled: {getattr(user, 'disabled', None)}")
    return user

def get_current_active_user(current_user: User = Depends(get_current_user_with_db)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role-based authorization
def get_current_vendor(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Vendor role required."
        )
    return current_user

def get_current_patient(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Patient role required."
        )
    return current_user
# Add a test endpoint to verify CORS configuration
@app.get("/test-cors")
def test_cors_config():
    return {
        "message": "CORS test endpoint", 
        "cors_origins": cors_origins,
    }

# OAuth login endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "user_id": user.user_id},  # ✅ ADD user_id!
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {
        "message": "MannBiome API is running", 
        "status": "ok",
        "docs": "Go to /docs for API documentation"
    }

# Get current user info endpoint
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Get user info - protected by vendor role
@app.get("/vendor/me", response_model=User)
async def read_vendor_me(current_user: User = Depends(get_current_vendor)):
    return current_user

# Get user info - protected by patient role
@app.get("/patient/me", response_model=User)
async def read_patient_me(current_user: User = Depends(get_current_patient)):
    return current_user

# Add simple endpoint to check if token is valid
@app.get("/validate-token")
async def validate_token(current_user: User = Depends(get_current_active_user)):
    return {"valid": True, "user_id": current_user.user_id, "username": current_user.username, "role": current_user.role}

# Protect the products endpoint to require authentication
@app.get("/api/products")
def get_all_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Retrieve all products from the product table ordered by product_id
    """
    try:
        query = text("""
            SELECT 
                product_id,
                vendor_id,
                name,
                regular_price,
                sale_price,
                discount_percentage,
                impressions,
                description,
                image_path,
                created_at,
                updated_at,
                clinical_status_id
            FROM public.product
            ORDER BY product_id ASC
        """)
        
        result = db.execute(query).fetchall()
        
        # Format the data
        products = []
        for row in result:
            # Convert to dictionary
            product = dict(row._mapping)
            
            # Format dates to readable strings
            if product['created_at']:
                product['created_at'] = product['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if product['updated_at']:
                product['updated_at'] = product['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Ensure numeric fields are properly formatted
            if product['regular_price']:
                product['regular_price'] = float(product['regular_price'])
            if product['sale_price']:
                product['sale_price'] = float(product['sale_price'])
            
            products.append(product)
            
        return {
            "success": True,
            "total_products": len(products),
            "products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Continue with your existing endpoints, but add authentication as needed...
# For example, protect dashboard metrics endpoint
@app.get("/api/dashboard-metrics")
def get_dashboard_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        # Total Impressions
        total_impressions_query = text("SELECT SUM(impressions) AS total_impressions FROM public.product")
        total_impressions_result = db.execute(total_impressions_query).fetchone()
        total_impressions = total_impressions_result[0] if total_impressions_result[0] else 0
        
        # Engagement Rate
        engagement_rate_query = text("""
            SELECT 
                (COUNT(CASE WHEN engagement_type = 'click' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(CASE WHEN engagement_type = 'view' THEN 1 END), 0)) AS engagement_rate
            FROM public.engagements
        """)
        engagement_rate_result = db.execute(engagement_rate_query).fetchone()
        engagement_rate = round(engagement_rate_result[0], 1) if engagement_rate_result[0] else 0.0
        
        # Customer Reach
        customer_reach_query = text("""
            SELECT COUNT(DISTINCT customer_id) AS customer_reach
            FROM public.visit
            WHERE customer_id IS NOT NULL
        """)
        customer_reach_result = db.execute(customer_reach_query).fetchone()
        customer_reach = customer_reach_result[0] if customer_reach_result[0] else 0
        
        return {
            "total_impressions": total_impressions,
            "engagement_rate": engagement_rate,
            "customer_reach": customer_reach
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Individual endpoints for each metric
@app.get("/api/total-impressions")
def get_total_impressions(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        query = text("SELECT SUM(impressions) AS total_impressions FROM public.product")
        result = db.execute(query).fetchone()
        total_impressions = result[0] if result[0] else 0
        return {"total_impressions": total_impressions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/engagement-rate")
def get_engagement_rate(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        query = text("""
            SELECT 
                (COUNT(CASE WHEN engagement_type = 'click' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(CASE WHEN engagement_type = 'view' THEN 1 END), 0)) AS engagement_rate
            FROM public.engagements
        """)
        result = db.execute(query).fetchone()
        engagement_rate = round(result[0], 1) if result[0] else 0.0
        return {"engagement_rate": engagement_rate}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Add endpoints for customer insights metrics
@app.get("/api/customer-insights")
def get_customer_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        # Total Customers
        total_customers_query = text("SELECT COUNT(*) AS total_customers FROM public.user_account where role ='patient'")
        total_customers_result = db.execute(total_customers_query).fetchone()
        total_customers = total_customers_result[0] if total_customers_result[0] else 0
        
        # New Customers (last 30 days)
        new_customers_query = text("""
            SELECT COUNT(*) AS new_customers 
            FROM public.user_account 
            WHERE role ='patient' and created_at >= CURRENT_DATE - INTERVAL '10 days'
        """)
        new_customers_result = db.execute(new_customers_query).fetchone()
        new_customers = new_customers_result[0] if new_customers_result[0] else 0
        
        # Avg. Health Index (placeholder calculation)
        # In a real system, this would be calculated from health assessment data
        avg_health_index = 3.8
        
        # Retention Rate
        retention_rate_query = text("""
            SELECT 
                (COUNT(CASE WHEN status = 'active' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0)) AS retention_rate
            FROM public.user_account
        """)
        retention_rate_result = db.execute(retention_rate_query).fetchone()
        retention_rate = round(retention_rate_result[0], 1) if retention_rate_result[0] else 0.0
        
        return {
            "total_customers": total_customers,
            "new_customers": new_customers,
            "avg_health_index": avg_health_index,
            "retention_rate": retention_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Individual endpoints for each customer metric
@app.get("/api/total-customers")
def get_total_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        query = text("SELECT COUNT(*) AS total_customers FROM public.user_account")
        result = db.execute(query).fetchone()
        total_customers = result[0] if result[0] else 0
        return {"total_customers": total_customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/new-customers")
def get_new_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        query = text("""
            SELECT COUNT(*) AS new_customers 
            FROM public.user_account 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """)
        result = db.execute(query).fetchone()
        new_customers = result[0] if result[0] else 0
        return {"new_customers": new_customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/avg-health-index")
def get_avg_health_index(current_user: User = Depends(get_current_active_user)):
    # Placeholder for avg health index calculation
    # In a real system, this would query from a health assessment table
    return {"avg_health_index": 3.8}

@app.get("/api/retention-rate")
def get_retention_rate(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        query = text("""
            SELECT 
                (COUNT(CASE WHEN status = 'active' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0)) AS retention_rate
            FROM public.user_account
        """)
        result = db.execute(query).fetchone()
        retention_rate = round(result[0], 1) if result[0] else 0.0
        return {"retention_rate": retention_rate}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/customer-reach")
def get_customer_reach(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        query = text("""
            SELECT COUNT(DISTINCT user_id) AS customer_reach
            FROM public.engagements
            WHERE user_id IS NOT NULL
        """)
        result = db.execute(query).fetchone()
        customer_reach = result[0] if result[0] else 0
        return {"customer_reach": customer_reach}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Serve the HTML file
@app.get("/dics")
async def serve_dashboard():
    html_path = os.path.join(
        r"C:/Users/Bhavya Reddy Seerapu/Desktop/MicrobiomeProject/frontEndPrototypeCode/ProjectVendor",
        "Dashboard.html"
    )
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        # Return a helpful error message if the file doesn't exist
        return HTMLResponse(
            content=f"Error: HTML file not found at {html_path}. Please check the file path.",
            status_code=404
        )

# Add these endpoints to your dBretreivalWithNewMetrics.py file
@app.get("/api/recent-customers")
def get_recent_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        # Adjusted query based on your actual database schema
        query = text("""
            SELECT 
    ua.user_id AS customer_id,
    CONCAT(ua.first_name, ' ', ua.last_name) AS full_name,
    ua.created_at AS signup_date,
    ua.age,
    -- Get the health index from the most recent visit
    (SELECT v.health_index 
     FROM visit v 
     WHERE v.customer_id = ua.user_id 
     ORDER BY v.visit_id DESC 
     LIMIT 1) AS overall_health_index,
    -- Count visits from the visits table
    (SELECT COUNT(*) 
     FROM visit v 
     WHERE v.customer_id = ua.user_id) AS visit_count,
    ua.status,
    -- Health status based on most recent health index
    CASE
        WHEN (SELECT v.health_index 
              FROM visit v 
              WHERE v.customer_id = ua.user_id 
              ORDER BY v.visit_id DESC 
              LIMIT 1) >= 3.5 THEN 'healthy'
        WHEN (SELECT v.health_index 
              FROM visit v 
              WHERE v.customer_id = ua.user_id 
              ORDER BY v.visit_id DESC 
              LIMIT 1) >= 2.5 THEN 'warning'
        ELSE 'critical'
    END AS health_status
FROM 
    public.user_account ua
WHERE
    ua.role = 'patient'
ORDER BY 
    ua.created_at DESC
LIMIT 10;
        """)
        
        result = db.execute(query).fetchall()
        
        # Format the data
        customers = []
        for row in result:
            # Convert to dictionary
            customer = dict(row._mapping)
            
            # Format the signup date to a readable string
            if customer['signup_date']:
                customer['signup_date'] = customer['signup_date'].strftime('%d %b %Y')
            
            # Format the health index to one decimal place
            if customer['overall_health_index']:
                customer['overall_health_index'] = round(float(customer['overall_health_index']), 1)
            
            customers.append(customer)
            
        return {"customers": customers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/customer/{customer_id}/visits")
def get_customer_visits(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        # Using engagements as a proxy for visits since your database doesn't have a visits table
        query = text("""
            SELECT 
                e.engagement_id AS visit_id,
                e.created_at AS visit_date,
                COALESCE(3.5, 0) AS health_index_value,
                CASE
                    WHEN COALESCE(3.5, 0) >= 3.5 THEN 'healthy'
                    WHEN COALESCE(3.5, 0) >= 2.5 THEN 'warning'
                    ELSE 'critical'
                END AS health_status,
                e.engagement_type
            FROM 
                public.engagements e
            WHERE 
                e.user_id = :customer_id
            ORDER BY 
                e.created_at DESC
        """)
        
        result = db.execute(query, {"customer_id": customer_id}).fetchall()
        
        # Format the data
        visits = []
        for row in result:
            # Convert to dictionary
            visit = dict(row._mapping)
            
            # Format the visit date to a readable string
            if visit['visit_date']:
                visit['visit_date'] = visit['visit_date'].strftime('%d %b %Y')
            
            # Format the health index to one decimal place
            if visit['health_index_value']:
                visit['health_index_value'] = round(float(visit['health_index_value']), 1)
            
            visits.append(visit)
            
        return {"visits": visits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Optional: Add an endpoint to get a specific product by ID
@app.get("/api/products/{product_id}")
def get_product_by_id(product_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Retrieve a specific product by product_id
    """
    try:
        query = text("""
            SELECT 
                product_id,
                vendor_id,
                name,
                regular_price,
                sale_price,
                discount_percentage,
                impressions,
                description,
                image_path,
                created_at,
                updated_at,
                clinical_status_id
            FROM public.product
            WHERE product_id = :product_id
        """)
        
        result = db.execute(query, {"product_id": product_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found")
        
        # Convert to dictionary
        product = dict(result._mapping)
        
        # Format dates to readable strings
        if product['created_at']:
            product['created_at'] = product['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if product['updated_at']:
            product['updated_at'] = product['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Ensure numeric fields are properly formatted
        if product['regular_price']:
            product['regular_price'] = float(product['regular_price'])
        if product['sale_price']:
            product['sale_price'] = float(product['sale_price'])
        
        return {
            "success": True,
            "product": product
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Optional: Add pagination support for the products endpoint
@app.get("/api/products/paginated")
def get_products_paginated(
    limit: Optional[int] = 100, 
    offset: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve products with pagination support
    """
    try:
        # Get total count first
        count_query = text("SELECT COUNT(*) FROM public.product")
        total_count = db.execute(count_query).scalar()
        
        # Get paginated products
        query = text("""
            SELECT 
                product_id,
                vendor_id,
                name,
                regular_price,
                sale_price,
                discount_percentage,
                impressions,
                description,
                image_path,
                created_at,
                updated_at,
                clinical_status_id
            FROM public.product
            ORDER BY product_id ASC
            LIMIT :limit OFFSET :offset
        """)
        
        result = db.execute(query, {"limit": limit, "offset": offset}).fetchall()
        
        # Format the data
        products = []
        for row in result:
            # Convert to dictionary
            product = dict(row._mapping)
            
            # Format dates to readable strings
            if product['created_at']:
                product['created_at'] = product['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if product['updated_at']:
                product['updated_at'] = product['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Ensure numeric fields are properly formatted
            if product['regular_price']:
                product['regular_price'] = float(product['regular_price'])
            if product['sale_price']:
                product['sale_price'] = float(product['sale_price'])
            
            products.append(product)
            
        return {
            "success": True,
            "total_count": total_count,
            "current_count": len(products),
            "limit": limit,
            "offset": offset,
            "products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
# Add this to your dBretreivalWithNewMetrics.py file

from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Pydantic models for request validation
class ProfessionalData(BaseModel):
    license_number: str
    specialty: Optional[str] = None
    organization: Optional[str] = None

class UserRegistration(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: str
    status: str = "active"
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    professional_data: Optional[ProfessionalData] = None

class IdentityVerification(BaseModel):
    username: str
    email: str

class PasswordReset(BaseModel):
    username: str
    email: str
    new_password: str

@app.post("/register")
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """
    Register a new user in the system - FIXED VERSION
    """
    try:
        # Check if email already exists
        check_query = text("SELECT user_id FROM public.user_account WHERE email = :email")
        existing_user = db.execute(check_query, {"email": user_data.email}).fetchone()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username exists
        check_username_query = text("SELECT user_id FROM public.user_account WHERE username = :username")
        existing_username = db.execute(check_username_query, {"username": user_data.username}).fetchone()
        
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash the password - ONLY store hashed password
        password_hash = get_password_hash(user_data.password)
        
        # Get current timestamp for created_at
        now = datetime.now()
        
        # FIXED: Only store hashed password, remove plain text password storage
        insert_query = text("""
            INSERT INTO public.user_account (
                username,
                password_hash,
                email,
                first_name,
                last_name,
                role,
                created_at,
                status,
                age,
                gender,
                phone
            ) VALUES (
                :username,
                :password_hash,
                :email,
                :first_name,
                :last_name,
                :role,
                :created_at,
                :status,
                :age,
                :gender,
                :phone
            ) RETURNING user_id
        """)
        
        # Prepare the parameters - REMOVED plain text password
        params = {
            "username": user_data.username,
            "password_hash": password_hash,  # Only store hashed password
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "role": user_data.role,
            "created_at": now,
            "status": user_data.status,
            "age": user_data.age,
            "gender": user_data.gender,
            "phone": user_data.phone
        }
        
        # Log the query for debugging (without password)
        safe_params = {k: v for k, v in params.items() if k != 'password_hash'}
        logger.info(f"Creating user with params: {safe_params}")
        
        # Execute the query
        try:
            result = db.execute(insert_query, params)
            user_id = result.fetchone()[0]
            db.commit()
            logger.info(f"✅ User created successfully with ID: {user_id}")
        except Exception as insert_error:
            logger.error(f"❌ Error executing insert query: {str(insert_error)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to insert user: {str(insert_error)}"
            )

        # If user is a vendor, create vendor record automatically
        vendor_id = None
        if user_data.role == 'vendor':
            try:
                # Generate next vendor_id
                max_vendor_query = text("""
                    SELECT vendor_id FROM public.vendor 
                    ORDER BY vendor_id DESC LIMIT 1
                """)
                max_vendor = db.execute(max_vendor_query).fetchone()
                
                if max_vendor and max_vendor[0]:
                    # Extract number from V001, V002, etc.
                    last_num = int(max_vendor[0][1:])
                    vendor_id = f"V{str(last_num + 1).zfill(3)}"
                else:
                    vendor_id = "V001"
                
                logger.info(f"Creating vendor with ID: {vendor_id}")
                
                # Create vendor record with basic info
                company_name = f"{user_data.first_name} {user_data.last_name} Vendor"
                contact_info = f"Email: {user_data.email}"
                if user_data.phone:
                    contact_info += f"\nPhone: {user_data.phone}"
                
                insert_vendor_query = text("""
                    INSERT INTO public.vendor (
                        vendor_id,
                        user_id,
                        company_name,
                        contact_info,
                        products_offered,
                        status,
                        created_at,
                        updated_at
                    ) VALUES (
                        :vendor_id,
                        :user_id,
                        :company_name,
                        :contact_info,
                        :products_offered,
                        :status,
                        :created_at,
                        :updated_at
                    )
                """)
                
                vendor_params = {
                    "vendor_id": vendor_id,
                    "user_id": user_id,
                    "company_name": company_name,
                    "contact_info": contact_info,
                    "products_offered": "To be updated",
                    "status": "active",
                    "created_at": now,
                    "updated_at": now
                }
                
                db.execute(insert_vendor_query, vendor_params)
                db.commit()
                logger.info(f"✅ Vendor created successfully with ID: {vendor_id}")
                
            except Exception as vendor_error:
                logger.error(f"❌ Error creating vendor: {str(vendor_error)}")
                # Rollback and clean up user if vendor creation fails
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create vendor record: {str(vendor_error)}"
                )
        
        # If user is a doctor or HCP, store professional data
        if user_data.professional_data and (user_data.role == 'doctor' or user_data.role == 'hcp'):
            try:
                # Check if the professional_data table exists
                check_table_query = text("SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'professional_data'")
                table_exists = db.execute(check_table_query).fetchone() is not None
                
                if not table_exists:
                    # Create the professional_data table if it doesn't exist
                    create_table_query = text("""
                        CREATE TABLE public.professional_data (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES public.user_account(user_id),
                            license_number VARCHAR(100) NOT NULL,
                            specialty VARCHAR(100),
                            organization VARCHAR(200),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    db.execute(create_table_query)
                    logger.info("Created new professional_data table")
                
                # Insert the professional data
                insert_prof_query = text("""
                    INSERT INTO public.professional_data (
                        user_id,
                        license_number,
                        specialty,
                        organization,
                        created_at
                    ) VALUES (
                        :user_id,
                        :license_number,
                        :specialty,
                        :organization,
                        :created_at
                    )
                """)
                
                prof_params = {
                    "user_id": user_id,
                    "license_number": user_data.professional_data.license_number,
                    "specialty": user_data.professional_data.specialty,
                    "organization": user_data.professional_data.organization,
                    "created_at": now
                }
                
                db.execute(insert_prof_query, prof_params)
                db.commit()
                logger.info("Added professional data for user")
                
            except Exception as prof_error:
                # Log the error but don't fail the registration
                logger.warning(f"Error storing professional data: {str(prof_error)}")
        
        # Prepare response with vendor_id if applicable
        response_data = {
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id,
            "username": user_data.username,
            "status": user_data.status,
            "role": user_data.role
        }
        
        if vendor_id:
            response_data["vendor_id"] = vendor_id
        
        return response_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )
    
@app.post("/verify-identity")
async def verify_identity(data: IdentityVerification, db: Session = Depends(get_db)):
    """
    Verify if username and email match in database
    """
    try:
        query = text("""
            SELECT user_id 
            FROM public.user_account 
            WHERE username = :username AND email = :email
        """)
        
        result = db.execute(query, {
            "username": data.username,
            "email": data.email
        }).fetchone()
        
        if result:
            return {"verified": True, "message": "Identity verified"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Username and email do not match"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying identity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify identity"
        )
    
@app.get("/api/admin/vendors")
async def get_all_vendors(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch all active vendors for admin dropdown selection."""
    try:
        # Verify user is a vendor/admin
        if current_user.role != 'vendor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only vendors/admins can access vendor list"
            )
        
        query = text("""
            SELECT 
                v.vendor_id,
                v.company_name,
                v.contact_info,
                v.status,
                u.email,
                u.first_name,
                u.last_name
            FROM public.vendor v
            JOIN public.user_account u ON v.user_id = u.user_id
            WHERE v.status = 'active'
            ORDER BY v.vendor_id
        """)
        
        result = db.execute(query).fetchall()
        
        vendors = []
        for row in result:
            vendors.append({
                "vendor_id": row[0],
                "company_name": row[1],
                "contact_info": row[2],
                "status": row[3],
                "email": row[4],
                "first_name": row[5],
                "last_name": row[6],
                "display_name": f"{row[1]} ({row[0]})"  # e.g., "Biohm Labs Vendor (V006)"
            })
        
        return {"vendors": vendors}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching vendors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vendors: {str(e)}"
        )

    # Endpoint 2: Reset password
@app.post("/reset-password")
async def reset_password(data: PasswordReset, db: Session = Depends(get_db)):
    """Reset user password after identity verification"""
    try:
        # DEBUG: Log password info
        password_str = data.new_password
        password_length_chars = len(password_str)
        password_length_bytes = len(password_str.encode('utf-8'))
        
        logger.info(f"Password length in characters: {password_length_chars}")
        logger.info(f"Password length in bytes: {password_length_bytes}")
        
        # Validate password length (bcrypt limit is 72 BYTES, not characters)
        if password_length_bytes > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password is too long ({password_length_bytes} bytes). Maximum is 72 bytes."
            )
        
        # Verify username and email match
        verify_query = text("""
            SELECT user_id 
            FROM public.user_account 
            WHERE username = :username AND email = :email
        """)
        
        user = db.execute(verify_query, {
            "username": data.username,
            "email": data.email
        }).fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Username and email do not match"
            )
        
        # Hash the new password
        logger.info("Attempting to hash password...")
        new_password_hash = get_password_hash(password_str)
        logger.info("Password hashed successfully")
        
        # Update password
        update_query = text("""
            UPDATE public.user_account 
            SET password_hash = :password_hash 
            WHERE username = :username AND email = :email
        """)
        
        db.execute(update_query, {
            "password_hash": new_password_hash,
            "username": data.username,
            "email": data.email
        })
        
        db.commit()
        
        logger.info(f"Password reset successful for user: {data.username}")
        
        return {"success": True, "message": "Password reset successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)