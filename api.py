import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# We will update these script imports in a moment
from advanced_vision import analyze_clothing_model
from stylist import match_outfit

load_dotenv()

app = FastAPI(title="StylAI Server")

# Allow Vite frontend to talk to our backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Supabase
url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_KEY", "")
supabase = create_client(url, key)

class UserSyncRequest(BaseModel):
    email: str
    auth_id: str

@app.post("/users/sync")
def sync_user(req: UserSyncRequest):
    res = supabase.table("users").select("*").eq("username", req.email).execute()
    if res.data:
        return {"user_id": res.data[0]["user_id"]}
    else:
        new_user = {
            "username": req.email,
            "skin_undertone": "Neutral",
            "body_shape": "Rectangle",
            "style_preference": "Casual"
        }
        insert_res = supabase.table("users").insert(new_user).execute()
        return {"user_id": insert_res.data[0]["user_id"]}

@app.get("/")
def read_root():
    return {"message": "StylAI Backend is running!"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    return res.data[0]

@app.get("/wardrobe/{user_id}")
def get_wardrobe(user_id: int):
    res = supabase.table("garments").select("*").eq("user_id", user_id).execute()
    return res.data

@app.post("/upload")
async def upload_garment(user_id: int = Form(...), file: UploadFile = File(...)):
    """Uploads an image, runs AI vision, saves to Supabase Storage, and adds to DB."""
    # 1. Save file locally temporarily for the AI to read
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
        
    # 2. Run AI Vision
    try:
        ai_data = analyze_clothing_model(temp_path)
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"AI Vision Error: {str(e)}")
        
    # 3. Upload image to Supabase Storage
    import uuid
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    
    with open(temp_path, "rb") as f:
        # We store it in 'garments' bucket under the user ID with a uniquely generated name
        storage_path = f"user_{user_id}/{unique_filename}"
        supabase.storage.from_("garments").upload(storage_path, f)
        
    # Get public URL
    image_url = supabase.storage.from_("garments").get_public_url(storage_path)
    
    # Clean up local file
    os.remove(temp_path)
    
    # 4. Save to Database
    new_garment = {
        "user_id": user_id,
        "category": ai_data["category"],
        "sub_category": ai_data["sub_category"],
        "primary_color": f"{ai_data['color']} | {ai_data['hex_code']}",
        "color_temperature": ai_data["temperature"],
        "fit": ai_data["fit"],
        "image_url": image_url,
        "formality_level": 3 # Hardcoded default for MVP
    }
    
    res = supabase.table("garments").insert(new_garment).execute()
    return {"message": "Garment analyzed and saved!", "data": res.data[0]}

@app.get("/style/{user_id}")
def generate_style(user_id: int, occasion: str = "Casual", city: str = "New York"):
    """Fetches user data and generates an outfit using Generative AI."""
    # 1. Fetch User Data
    user_res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not user_res.data:
         raise HTTPException(status_code=404, detail="User not found")
    user = user_res.data[0]
    
    # 2. Fetch Wardrobe Data
    ward_res = supabase.table("garments").select("*").eq("user_id", user_id).execute()
    wardrobe = ward_res.data
    
    if not wardrobe:
        raise HTTPException(status_code=400, detail="Wardrobe is empty")
        
    # 3. Run Matching Algorithm (Gemini)
    outfit = match_outfit(user, wardrobe, occasion, city)
    if not outfit:
         raise HTTPException(status_code=400, detail="Gemini could not find a suitable outfit combination.")
         
    return {"outfit": outfit}

class TryOnRequest(BaseModel):
    prompt: str

@app.post("/try-on")
def virtual_try_on(req: TryOnRequest):
    """Generates an image of a model wearing the outfit using Replicate."""
    import replicate
    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        raise HTTPException(status_code=500, detail="Replicate API token missing")
        
    try:
        output = replicate.run(
            "bytedance/sdxl-lightning-4step:5599ed30703defd1d160a25a63321b4dec97101d98b4674bcc56e41f62f35637",
            input={
                "prompt": f"A highly realistic fashion editorial full body portrait of a person wearing {req.prompt}. Studio lighting, Vogue magazine style, highly detailed.",
                "width": 768,
                "height": 1024,
                "num_inference_steps": 4,
                "guidance_scale": 0,
            }
        )
        return {"image_url": output[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/garments/{garment_id}")
def delete_garment(garment_id: int):
    """Removes a garment from the Supabase database."""
    res = supabase.table("garments").delete().eq("garment_id", garment_id).execute()
    if not res.data:
         raise HTTPException(status_code=404, detail="Garment not found")
    return {"message": "Garment deleted"}
