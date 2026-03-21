"""News endpoint stub (placeholder for future implementation)."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/news")
async def read_items():
    return {"message": "Endpoint works!"}