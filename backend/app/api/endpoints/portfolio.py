from fastapi import APIRouter

router = APIRouter()

@router.get("/portfolio")
async def read_items():
    return {"message": "Endpoint works!"}