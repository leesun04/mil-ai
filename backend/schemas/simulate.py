#시물레이터 시그마
from pydantic import BaseModel
from typing import Optional
from enum import Enum


# ============================================================
# POST /enlist  — 입영 시뮬레이션
# ============================================================
class EnlistRequest(BaseModel): #사용자가 API한테 보내는 요청을 정의, 즉 프론트에서 이 형태로 api를 호출해ㅑ함
    #0단계  출생연도
    birth_year: int

    #==============================
    #1단계 기본 정보 
    identity: str #학생 | 취업자 | 취준자 | 기타
    identity_custom: Optional[str] #기타인 경우 상세 정보

    #1단계에서 학교 상태
    academic_status: Optional[str] #재학 | 휴학 | 졸업 | 없음
    grade: Optional[str] #학년
    toral_semester: Optional[int] #총 학기 수
    
    #==============================
    #2단계 신체검사
    physical_checked: bool #신체검사 여부
    physical_grade: Optional[str] #신체등급

    #==============================
    #3단계 희망 복무 유형
    service_type: Optional[str] #희망 복무 유형 "육군" | "공군" | ... | "미정"
    service_type_custom: Optional[str] #기타/직접 입력 받고싶으면 선택

    #==============================
    #4단계 학업 계획
    edu_plan: Optional[str] # "석사" | "편입" | "기타" 등 하나
    edu_plan_custom: Optional[str] #기타/직접 입력 받고싶으면 선택

    #==============================
    #5단계 해외 체류 계획
    abroad_plan: Optional[str] # "교환학생" | "어학연수" | "기타" 등 하나
    abroad_plan_custom: Optional[str] #기타/직접 입력 받고싶으면 선택

    #==============================
    #6단계 추가 정보
    extra_info: list[str] #자격증보유, 기타, 해당없음
    extra_info_custom: Optional[str] #기타/직접 입력 받고싶으면 선택

#==응답 모델==
class EnlistResponse(BaseModel): 
    """
    POST /enlist 응답 모델
    """
    deadline: Optional[str] #최대 입영 연기 기한    
    context_text: str #llm에 넘길 텍스트

# ============================================================
# POST /service-type  — 복무 유형별 안내
# ============================================================

#===요청===
class ServiceTypeRequest(BaseModel):
    service_type: str #희망 복무 유형 "육군" | "공군" | ... | "미정"   
    service_type_custom: Optional[str] #기타/직접 입력 받고싶으면 선택
    physical_grade: Optional[str] #신체등급

#===응답===
class ServiceTypeResponse(BaseModel):
    context_text: str #llm에 넘길 텍스트
