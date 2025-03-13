from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_status():
    return {"status": "Server is running"}

@router.post("/alert")
def trigger_alert():
    return {"alert": "Alert triggered"}
