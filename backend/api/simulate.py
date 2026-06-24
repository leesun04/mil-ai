from fastapi import APIRouter
from schemas.simulate import EnlistRequest, EnlistResponse, ServiceTypeRequest, ServiceTypeResponse
from services.simulate import SimulateService

router = APIRouter(prefix="/simulate", tags=["simulate"])

@router.get("/")
async def run_simulation():
    return {"message": "시뮬레이터 가동"}

@router.post("/enlist", response_model=EnlistResponse)
async def enlist_simulation(request: EnlistRequest):
    print("시뮬레이터 동작 로직")
