from fastapi import FastAPI, APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import httpx
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# LinkedIn OAuth Configuration
LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
FRONTEND_URL = "https://cf80c52e-5751-499f-940c-f2a1ff6b2f54.preview.emergentagent.com"
BACKEND_URL = "https://cf80c52e-5751-499f-940c-f2a1ff6b2f54.preview.emergentagent.com"
REDIRECT_URI = f"{BACKEND_URL}/api/auth/linkedin/callback"

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class LinkedInProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    first_name: str
    last_name: str
    headline: Optional[str] = None
    email: Optional[str] = None
    profile_picture: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    skills: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ResumeTemplate(BaseModel):
    id: str
    name: str
    description: str
    preview_image: str
    style: str

# LinkedIn OAuth Routes
@api_router.get("/auth/linkedin")
async def login_linkedin():
    """Initiate LinkedIn OAuth flow"""
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={LINKEDIN_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=openid profile email"
    )
    return {"auth_url": auth_url}

@api_router.get("/auth/linkedin/callback")
async def linkedin_callback(code: str, state: Optional[str] = None):
    """Handle LinkedIn OAuth callback"""
    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": LINKEDIN_CLIENT_ID,
                    "client_secret": LINKEDIN_CLIENT_SECRET,
                    "redirect_uri": REDIRECT_URI
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            token_data = token_response.json()
            access_token = token_data["access_token"]
            
            # Get basic profile information
            profile_response = await client.get(
                "https://api.linkedin.com/v2/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if profile_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get profile data")
            
            profile_data = profile_response.json()
            
            # Get email address
            email_response = await client.get(
                "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            email_data = None
            if email_response.status_code == 200:
                email_result = email_response.json()
                if "elements" in email_result and len(email_result["elements"]) > 0:
                    email_data = email_result["elements"][0]["handle~"]["emailAddress"]
            
            # Process and save profile data
            linkedin_profile = LinkedInProfile(
                user_id=str(profile_data.get("id", "")),
                first_name=profile_data.get("localizedFirstName", ""),
                last_name=profile_data.get("localizedLastName", ""),
                headline=profile_data.get("localizedHeadline", ""),
                email=email_data,
                profile_picture=profile_data.get("profilePicture", {}).get("displayImage", ""),
            )
            
            # Save to database
            await db.linkedin_profiles.insert_one(linkedin_profile.dict())
            
            # Redirect back to frontend with success
            redirect_url = f"{FRONTEND_URL}/?success=true&user_id={linkedin_profile.user_id}"
            return RedirectResponse(url=redirect_url)
            
    except Exception as e:
        logger.error(f"LinkedIn callback error: {str(e)}")
        redirect_url = f"{FRONTEND_URL}/?error=true"
        return RedirectResponse(url=redirect_url)

@api_router.get("/profile/{user_id}", response_model=LinkedInProfile)
async def get_profile(user_id: str):
    """Get LinkedIn profile data by user ID"""
    profile = await db.linkedin_profiles.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Convert MongoDB ObjectId to string to make it JSON serializable
    if "_id" in profile:
        profile["_id"] = str(profile["_id"])
        
    return LinkedInProfile(**profile)

@api_router.get("/templates", response_model=List[ResumeTemplate])
async def get_templates():
    """Get available resume templates"""
    templates = [
        {
            "id": "modern",
            "name": "Modern Professional",
            "description": "Clean, modern design perfect for tech and creative industries",
            "preview_image": "https://images.pexels.com/photos/270238/pexels-photo-270238.png",
            "style": "modern"
        },
        {
            "id": "classic",
            "name": "Classic Executive",
            "description": "Traditional format ideal for corporate and executive positions",
            "preview_image": "https://images.pexels.com/photos/5922215/pexels-photo-5922215.jpeg",
            "style": "classic"
        },
        {
            "id": "elegant",
            "name": "Elegant Minimalist",
            "description": "Sophisticated design with subtle elegance for all industries",
            "preview_image": "https://images.pexels.com/photos/8534381/pexels-photo-8534381.jpeg",
            "style": "elegant"
        }
    ]
    return templates

@api_router.post("/generate-resume")
async def generate_resume(user_id: str, template_id: str):
    """Generate resume using LinkedIn profile data and selected template"""
    profile = await db.linkedin_profiles.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Convert MongoDB ObjectId to string to make it JSON serializable
    if "_id" in profile:
        profile["_id"] = str(profile["_id"])
    
    # Create resume data
    resume_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "template_id": template_id,
        "profile": profile,
        "generated_at": datetime.utcnow()
    }
    
    # Save resume
    result = await db.resumes.insert_one(resume_data)
    resume_data["_id"] = str(result.inserted_id)
    
    return {"message": "Resume generated successfully", "resume_id": resume_data["id"], "data": resume_data}

# Original routes
@api_router.get("/")
async def root():
    return {"message": "Resume Builder API with LinkedIn Integration"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/test-create-profile", status_code=201)
async def test_create_profile(profile: LinkedInProfile):
    """Test endpoint to create a LinkedIn profile for testing purposes"""
    await db.linkedin_profiles.insert_one(profile.dict())
    return {"message": "Test profile created successfully", "user_id": profile.user_id}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
