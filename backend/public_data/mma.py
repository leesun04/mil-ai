import httpx #인터넷 요청 도구
import xmltodict #XML을 dict로 바꿔주는 라이브러리
from core.config import settings 

RECRUIT_URL = "https://apis.data.go.kr/1300000/MJBGJWJeopSuHH4" #모집병 군지원 접수현황 조회 

async def get_recruit_status(service_type: str | None = None) -> dict:
    """모집병 접수현황 조회. service_type(육군/해군/공군/해병대) 주면 그 군만 필터."""
    params = {
        "serviceKey": settings.MMA_API_KEY, #인증키
        "pageNo": 1,
        "numOfRows": 100,
    }
    data = await _get("/list", params) #인터넷 호출
    return _clean_recruit(data, service_type) # 병무청 XML(dict) → 필요한 것만 추려서 정리

async def _get(path: str, params: dict) -> dict:
    """공통 GET 호출 → XML을 dict로 변환해서 반환."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{RECRUIT_URL}{path}", params=params) #서버로 호출
        resp.raise_for_status() #HTTP 오류 발생 시 예외 발생
        return xmltodict.parse(resp.text) # xmltodict는 XML을 딕셔너리로 바꿔주는 라이브러리

def _clean_recruit(data: dict, service_type: str | None) -> dict:
    """병무청 XML(dict) → 필요한 것만 추려서 정리."""
    body = data.get("response", {}).get("body", {})
    items = body.get("items", {}).get("item", [])
    
    if isinstance(items, dict): # item이 하나면 dict, 여러 개면 list
        items = [items]
    
    cleaned = []
    for it in items:
        gun = it.get("gunGbnm") # 군구분명 (육군/해군/공군/해병대)
        if service_type and gun != service_type: #원하는 군이 아니면 스킵
            continue 
        cleaned.append({ #필요ㅏㄴ 것들만 고르기
            "군": gun,
            "특기": it.get("gsteukgiNm"),
            "모집구분": it.get("mojipGbnm"),
            "선발인원": it.get("seonbalPcnt"),
            "접수인원": it.get("jeopsuPcnt"),
            "경쟁률": it.get("rate"),
            "모집연도": it.get("mojipYy"),
            "모집차수": it.get("mojipTms"),
        })
    return {
        "service_type": service_type,
        "총건수": body.get("totalCount"),
        "items": cleaned,
    }
    
if __name__ == "__main__":
    import asyncio

    async def _test():
        result = await get_recruit_status("육군")   # 해군만 필터해서 받기
        print("=== 총건수 ===", result["총건수"])
        print("=== 정리된 개수 ===", len(result["items"]))
        print("=== 앞 3개 ===")
        for item in result["items"][:]:
            print(item)

    asyncio.run(_test())