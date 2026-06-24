from schemas.simulate import EnlistRequest, EnlistResponse, ServiceTypeRequest, ServiceTypeResponse

class SimulateService:
    async def simulate_enlist(self, request: EnlistRequest) -> EnlistResponse:
        """
        입영 시뮬레이션 메인 함수.
        [흐름] 입력(EnlistRequest) → 연기기한 계산 → context_text 조립 → 응답(EnlistResponse)
        라우터의 POST /enlist 가 이걸 호출한다.
        """
        deadline = self._calc_deadline(request)
        
        return EnlistResponse(deadline=deadline, context_text="시뮬레이터에서 LLM에 넘길 텍스트")
    
    def _resolve(self, value: Optional[str], custom: Optional[str]) -> Optional[str]:
        """
        '기타' 처리 헬퍼.
        사용자가 '기타'를 골랐으면 직접 입력값(custom)을 쓰고,
        아니면 고른 값(value)을 그대로 돌려준다.
        예) value="기타", custom="복수전공"  → "복수전공"
            value="석사", custom=None       → "석사"
        """
        if value == "기타" and custom:
            return custom
        return value
    
    #==연기 기한 결정 로직==
    def _calc_deadline(self, req: EnlistRequest) -> str:
        """
        최대 입영 연기 기한 계산 (백엔드의 핵심 '결정적 계산').
        규칙: 대학원(석사/박사) 진학이면 만 30세, 아니면 만 28세 되는 해 12/31.
        예) 2000년생, 대학원X → "2028-12-31"
            2000년생, 석사   → "2030-12-31"
        ※ 28/30은 임시값. 병역법 원문(학위·학교별 기준)으로 반드시 검증해 고칠 것.
        """
        if req.edu_plan in ("석사", "박사"):
            limit_age = 30
        else:
            limit_age = 28
        deadline_year = req.birth_year + limit_age
        return f"{deadline_year}-12-31"