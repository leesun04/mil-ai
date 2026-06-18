from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def run_simulation():
    return {"message": "시뮬레이터 가동"}

