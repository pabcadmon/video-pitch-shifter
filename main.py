from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, FileResponse
from threading import Thread
from tempfile import mktemp
from pitchShifterForAPI import process_video
import uuid
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates_directory = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_directory)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logger.info("Root endpoint accessed")
    return templates.TemplateResponse("index.html", {"request": request})

processed_files = {}

@app.post("/process/")
async def process_video_endpoint(file: UploadFile, shift: float = Form(...)):
    logger.info("Processing data...")

    video_path = mktemp(suffix=".mp4")
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    output_path = mktemp(suffix=".mp4")

    video_id = str(uuid.uuid4())

    result = process_video(video_path, output_path, shift)
    processed_files[video_id] = output_path

    return {"status": result["status"], "download_url": f"/download/{video_id}"}

@app.get("/download/{video_id}")
async def download_processed_video(video_id: str):
    if video_id not in processed_files:
        return JSONResponse({"status": "error", "message": "Video not found"}, status_code=404)

    return FileResponse(processed_files[video_id], media_type="video/mp4", filename=f"{video_id}.mp4")
