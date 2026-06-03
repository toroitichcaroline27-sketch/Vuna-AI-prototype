
import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google import genai
from google.genai import types

app = FastAPI()

# Make folder mapping bulletproof for Render
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

TODAYS_MARKET_DATA = """
SOKO LA LEO (03 June 2026):
- Maize: KSh 3,200 per 90kg bag in Kiambu (Hali: Kawaida)
- Tomato: KSh 4,800 per crate in Nairobi City Market (Hali: Bei imeshuka, bado kuna ushindani)
- Beans: KSh 12,500 per 90kg bag in Nakuru (Hali: Uhaba mkubwa)
- Kale (Sukuma Wiki): KSh 1,200 per bundle in Kisumu (Hali: Mvua imezidi, usafiri mgumu)
- Avocado: KSh 8,400 per crate in Meru (Hali: Soko thabiti, mahitaji ya nje ya nchi ni makubwa)
"""

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "result": None, "query": ""})

@app.post("/", response_class=HTMLResponse)
def query_market(request: Request, crop_query: str = Form(...)):
    if not crop_query.strip():
        return templates.TemplateResponse("index.html", {"request": request, "result": "Weka zao...", "query": crop_query})

    # Pull the API key securely from Render's environment vault
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        temperature=0.1,
        system_instruction=(
            f"You are the core AI backend gateway for the Vuna AI platform.\n"
            f"Context data to operate from:\n{TODAYS_MARKET_DATA}\n\n"
            f"CRITICAL COMPLIANCE RULES:\n"
            f"1. You must absolutely NOT generate introductory fluff or conversation.\n"
            f"2. If the crop requested is missing, reply EXACTLY with: 'Bei haijulikani — angalia KACE.co.ke'.\n"
            f"3. If found, respond entirely in simple Swahili using EXACTLY this structure:\n"
            f"HATARI: [LOW/MED/HIGH] │ SABABU: [Short Swahili reason] │ HATUA: [Short Swahili advice]"
        )
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"User Query: {crop_query}",
            config=config
        )
        result = response.text.strip()
    except Exception as e:
        result = f"Error: {str(e)}"

    return templates.TemplateResponse("index.html", {"request": request, "result": result, "query": crop_query})
