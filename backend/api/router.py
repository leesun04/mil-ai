from fastapi import APIRouter
from api import simulate, reservist, postpone

router = APIRouter()

router.include_router(simulate.router, prefix="/simulate", tags=["입영 시뮬레이터"])
#router.include_router(reservist.router, prefix="/reservist", tags=["예비군 가이드"])
#router.include_router(postpone.router, prefix="/postpone", tags=["당일 긴급 연기"])