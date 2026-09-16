import os
import zipfile
import io
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai

app = FastAPI(title="WebCraft AI Agent", description="Generates websites from natural language prompts")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configure Gemini API
# Pass GEMINI_API_KEY as an environment variable in Railway
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are WebCraft AI, an expert web design and coding agent.
When a user describes a website, you must generate a full, standalone, production-ready website consisting of HTML, CSS, and JS.

Return ONLY a raw JSON object with the following structure (no markdown fences, no extra text):
{
  "html": "<!DOCTYPE html>...",
  "css": "/* CSS Styles */...",
  "js": "// JavaScript code..."
}

Design Guidelines:
- Modern, visually polished, responsive design.
- Clean typography, CSS variables, sleek dark/light mode accents.
- Responsive layout using CSS Grid or Flexbox.
- Functional interactive components where applicable (e.g. navigation toggle, smooth scrolling, modal triggers, dynamic effects).
"""

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_website(prompt: str = Form(...)):
    if not GEMINI_API_KEY:
        return JSONResponse(
            status_code=400,
            content={"error": "GEMINI_API_KEY environment variable is not set. Please set it in your Railway settings."}
        )
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nUser Request: {prompt}",
            generation_config={"response_mime_type": "application/json"}
        )
        
        import json
        data = json.loads(response.text)
        return JSONResponse(content={
            "success": True,
            "html": data.get("html", ""),
            "css": data.get("css", ""),
            "js": data.get("js", "")
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/download")
async def download_zip(html: str = Form(...), css: str = Form(...), js: str = Form(...)):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("index.html", html)
        zip_file.writestr("css/style.css", css)
        zip_file.writestr("js/script.js", js)
        
        # Add a helpful README
        readme_content = """# Your Generated Website

This website was built using WebCraft AI Agent.

## Folder Structure:
- index.html (Main Page)
- css/style.css (Styles)
- js/script.js (Interactivity)

## Hosting Options:
1. GitHub Pages: Push to GitHub and enable Pages under Settings > Pages.
2. Netlify: Drag & drop this folder into https://app.netlify.com/drop
3. Vercel: Import your GitHub repo to Vercel for instant deployment.
"""
        zip_file.writestr("README.md", readme_content)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=generated_website.zip"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
