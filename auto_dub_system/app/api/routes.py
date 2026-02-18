from fastapi import APIRouter, File, UploadFile, Form
# from app.api.schemas import UploadResponse, StatusResponse

router = APIRouter()

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    source_lang: str = Form("auto"),
    target_lang: str = Form("English"),
    gender: str = Form("Male"),
    recover_bg: bool = Form(False)
):    # Save file to disk
    file_location = f"data/uploads/{file.filename}"
    import os
    os.makedirs("data/uploads", exist_ok=True)
    with open(file_location, "wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)
        
    # Build pipeline
    # Stage 1 (Chain) -> Stage 2 (Task -> Chord) -> Stage 3 (Chord Callback) -> Stage 4 (Task)
    
    from celery import chain
    from app.tasks.stage1_tasks import get_stage1_chain
    from app.tasks.stage2_tasks import process_stage2
    from app.tasks.stage4_tasks import process_stage4

    workflow = chain(
        get_stage1_chain(file_location),
        process_stage2.s(),
        process_stage4.s()
    )
    
    task = workflow.apply_async()
    
    return {"filename": file.filename, "task_id": task.id, "status": "processing_started"}

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    from app.tasks.stage1_tasks import celery_app
    result = celery_app.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }
    # result.result might be an exception if status is FAILURE
    if result.status == "FAILURE":
        response["error"] = str(result.result)
    return response

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    return await get_task_status(task_id)

@router.get("/download/{task_id}")
async def download_result(task_id: str):
    # Retrieve result... stub for now
     return {"task_id": task_id, "download_url": "http://example.com/file.mp4"}
