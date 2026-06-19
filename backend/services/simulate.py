from schemas.simulate import EnlistRequest, EnlistResponse, ServiceTypeRequest, ServiceTypeResponse

class SimulateService:
    async def simulate_enlist(self, request: EnlistRequest) -> EnlistResponse:
        print("이거 이제 개발할거임")