from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess
import json
import os
import shutil

router = APIRouter()


class YouTubeURL(BaseModel):
    url: str


class YouTubeDownload(BaseModel):
    url: str
    quality: str


class LoginRequest(BaseModel):
    username: str = ""
    email: str = ""
    password: str = ""


class RegisterRequest(BaseModel):
    username: str = ""
    email: str = ""
    password: str = ""


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Auto Dub System is running"}


async def _start_pipeline(file_location: str):
    """Helper to start the Celery pipeline for a given file."""
    from celery import chain
    from app.tasks.stage1_tasks import (
        task_audio_separator,
        task_diarization,
        task_overlap_split,
        task_segment,
        task_chunk
    )
    from app.tasks.stage2_tasks import process_stage2

    # Flatten the chain for better reliability
    workflow = chain(
        task_audio_separator.s(file_location),
        task_diarization.s(),
        task_overlap_split.s(),
        task_segment.s(),
        task_chunk.s(file_location),
        process_stage2.s()
    )
    task = workflow.apply_async()
    return task


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    source_lang: str = Form("auto"),
    target_lang: str = Form("English"),
    gender: str = Form("Male"),
    recover_bg: str = Form("false"),  # Accept as string from FormData
):
    # Convert recover_bg string to bool
    recover_bg_bool = recover_bg.lower() in ("true", "1", "yes")

    # Save file to disk
    os.makedirs("data/uploads", exist_ok=True)
    file_location = f"data/uploads/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        task = await _start_pipeline(file_location)
        return {
            "filename": file.filename,
            "task_id": task.id,
            "status": "processing_started",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "gender": gender,
            "recover_bg": recover_bg_bool,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


@router.post("/dub_video")
async def dub_video(
    file: UploadFile = File(None),
    youtube_video_path: str = Form(None),
    source_lang: str = Form("auto"),
    target_lang: str = Form("English"),
    gender: str = Form("Male"),
    recover_bg: str = Form("false"),
):
    """Alias / extended endpoint that also supports youtube_video_path."""
    recover_bg_bool = recover_bg.lower() in ("true", "1", "yes")
    os.makedirs("data/uploads", exist_ok=True)

    if file is not None:
        file_location = f"data/uploads/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    elif youtube_video_path:
        if not os.path.exists(youtube_video_path):
            raise HTTPException(status_code=400, detail=f"YouTube video path not found: {youtube_video_path}")
        file_location = youtube_video_path
    else:
        raise HTTPException(status_code=422, detail="Either 'file' or 'youtube_video_path' must be provided.")

    try:
        task = await _start_pipeline(file_location)
        return {
            "filename": os.path.basename(file_location),
            "task_id": task.id,
            "status": "processing_started",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "gender": gender,
            "recover_bg": recover_bg_bool,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    try:
        from app.tasks.celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        response = {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        }
        if result.status == "FAILURE":
            response["error"] = str(result.result)
        return response
    except Exception as e:
        return {"task_id": task_id, "status": "UNKNOWN", "error": str(e)}


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    return await get_task_status(task_id)


@router.post("/youtube/info")
async def youtube_info(data: YouTubeURL):
    if not data.url or not data.url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    # Check if yt-dlp is available
    if not shutil.which("yt-dlp"):
        raise HTTPException(
            status_code=500,
            detail="yt-dlp is not installed. Run: pip install yt-dlp"
        )

    try:
        cmd = ["yt-dlp", "-j", "--no-playlist", data.url]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"yt-dlp error: {result.stderr.strip() or 'Unknown error'}"
            )
        info = json.loads(result.stdout)

        formats = [
            {"quality": "1080p", "available": True},
            {"quality": "720p", "available": True},
            {"quality": "480p", "available": True},
            {"quality": "360p", "available": True},
        ]

        return {
            "status": "success",
            "data": {
                "title": info.get("title", "Unknown Title"),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", "Unknown"),
                "formats": formats,
            },
        }
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Request timed out fetching video info")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse video info response")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch YouTube info: {str(e)}")


@router.post("/youtube/download")
async def youtube_download(data: YouTubeDownload):
    if not shutil.which("yt-dlp"):
        raise HTTPException(
            status_code=500,
            detail="yt-dlp is not installed. Run: pip install yt-dlp"
        )
    try:
        os.makedirs("data/uploads", exist_ok=True)
        output_tmpl = "data/uploads/%(title)s_%(id)s.%(ext)s"

        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", output_tmpl,
            data.url,
        ]

        # Get filename first
        result = subprocess.run(
            cmd + ["--get-filename"], capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=f"yt-dlp error: {result.stderr.strip()}")
        filename_abs = result.stdout.strip()

        # Run actual download
        dl_result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if dl_result.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Download failed: {dl_result.stderr.strip()}")

        if not os.path.exists(filename_abs):
            raise HTTPException(status_code=500, detail="Download completed but file not found")

        filename = os.path.basename(filename_abs)
        size_bytes = os.path.getsize(filename_abs)
        size_mb = f"{(size_bytes / (1024 * 1024)):.2f} MB"

        return {
            "status": "success",
            "file_path": filename_abs,
            "filename": filename,
            "size": size_mb,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"YouTube download failed: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str):
    from fastapi.responses import FileResponse

    # Search in outputs first, then uploads
    for folder in ["data/outputs", "data/uploads"]:
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="File not found")


@router.post("/api/users/login")
async def login_stub(data: LoginRequest):
    """Stub login endpoint — replace with real auth when ready."""
    if not data.username and not data.email:
        raise HTTPException(status_code=422, detail="username or email is required")
    return {
        "status": "success",
        "token": "stub_token_" + (data.username or data.email),
        "username": data.username or data.email,
        "message": "Login successful (stub)",
    }


@router.post("/api/users/register")
async def register_stub(data: RegisterRequest):
    """Stub register endpoint — replace with real auth when ready."""
    if not data.username:
        raise HTTPException(status_code=422, detail="username is required")
    return {
        "status": "success",
        "token": "stub_token_" + data.username,
        "username": data.username,
        "message": "Registration successful (stub)",
    }
