import os
import json
import zipfile
import io
from pathlib import Path
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq

app = FastAPI()

# Calculate absolute path of the root directory
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Mount Static Files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

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
async def read_root():
    # List of candidate paths for index.html
    possible_paths = [
        TEMPLATES_DIR / "index.html",
        BASE_DIR / "index.html",
        Path("templates/index.html"),
        Path("index.html")
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

    # Fallback HTML UI if index.html is missing
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WebCraft AI</title>
        <style>
            body { font-family: system-ui, sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
            .card { background: #1e293b; padding: 2rem; border-radius: 12px; width: 90%; max-width: 600px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            h1 { margin-top: 0; color: #38bdf8; }
            textarea { width: 100%; height: 100px; background: #0f172a; color: white; border: 1px solid #334155; border-radius: 8px; padding: 10px; margin: 10px 0; box-sizing: border-box; }
            button { background: #0284c7; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; }
            button:hover { background: #0369a1; }
            #output { margin-top: 20px; background: #0f172a; padding: 10px; border-radius: 8px; display: none; }
            iframe { width: 100%; height: 300px; border: none; background: white; margin-top: 10px; border-radius: 6px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 WebCraft AI</h1>
            <p>Describe the website you want to build:</p>
            <textarea id="prompt" placeholder="e.g., A portfolio website for a game developer with dark mode..."></textarea>
            <button onclick="generate()">Generate Website</button>
            <div id="output">
                <h3>Result:</h3>
                <iframe id="preview"></iframe>
            </div>
        </div>
        <script>
            async function generate() {
                const prompt = document.getElementById('prompt').value;
                if(!prompt) return alert('Please enter a description');
                const btn = document.querySelector('button');
                btn.innerText = 'Generating...';
                btn.disabled = true;
                
                const formData = new FormData();
                formData.append('prompt', prompt);
                
                try {
                    const res = await fetch('/generate', { method: 'POST', body: formData });
                    const data = await res.json();
                    if(data.success) {
                        document.getElementById('output').style.display = 'block';
                        const doc = `<html><head><style>${data.css}</style></head><body>${data.html}<script>${data.js}<\/script></body></html>`;
                        document.getElementById('preview').srcdoc = doc;
                    } else {
                        alert('Error: ' + data.error);
                    }
                } catch(e) {
                    alert('Request failed: ' + e);
                }
                btn.innerText = 'Generate Website';
                btn.disabled = false;
            }
        </script>
    </body>
    </html>
    """

@app.post("/generate")
async def generate_site(prompt: str = Form(...)):
    if not client:
        return JSONResponse(status_code=500, content={"success": False, "error": "GROQ_API_KEY is missing in Railway Variables."})

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
