import os
import json
import zipfile
import io
from pathlib import Path
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from groq import Groq

app = FastAPI()

# Calculate absolute path of the repository root
BASE_DIR = Path(__file__).resolve().parent

# Set absolute path for templates & static directory
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Mount Static Files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount Jinja2 Templates safely
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """
You are an expert AI web developer.
The user will provide a description of a website.
Generate functional, modern HTML, CSS, and JavaScript.

You MUST respond ONLY with a raw JSON object with this EXACT structure (no markdown formatting, no ```json tags):
{
  "html": "...only the body content or layout without html/head tags...",
  "css": "...all styling including responsive styles...",
  "js": "...all interactive javascript code..."
}
"""

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Fallback check in case Jinja2 misses the path
    index_path = TEMPLATES_DIR / "index.html"
    if index_path.exists():
        return templates.TemplateResponse("index.html", {"request": request})
    
    # Direct file read if TemplateResponse fails
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/generate")
async def generate_site(prompt: str = Form(...)):
    if not client:
        return JSONResponse(status_code=500, content={"success": False, "error": "GROQ_API_KEY is missing in Railway variables."})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return {
            "success": True,
            "html": data.get("html", ""),
            "css": data.get("css", ""),
            "js": data.get("js", "")
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/download")
async def download_zip(html: str = Form(...), css: str = Form(...), js: str = Form(...)):
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    {html}
    <script src="app.js"></script>
</body>
</html>"""

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("index.html", full_html)
        zip_file.writestr("style.css", css)
        zip_file.writestr("app.js", js)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=website.zip"}
    )
