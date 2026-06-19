from fastapi import APIRouter
from schemas.simulate import EnlistRequest, EnlistResponse, ServiceTypeRequest, ServiceTypeResponse, DeadlineResponse

router = APIRouter(prefix="/simulate", tags=["simulate"])

@router.get("/")
async def run_simulation():
    return {"message": "시뮬레이터 가동"}

@router.post("/enlist", response_model=EnlistResponse)
async def enlist_simulation(request: EnlistRequest):
    print("이거 이제 개발할거임")