from pydantic import BaseModel

class UploadResponse(BaseModel):
    task_id: str
    status: str

class StatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
