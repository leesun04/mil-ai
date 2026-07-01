# backend/schemas/simulate.py
# ── 입영 시뮬레이터 스키마

from pydantic import BaseModel  
from typing import Optional      


# ============================================================
# 요청 모델 (프론트 → 내 백엔드)
# ============================================================
class EnlistRequest(BaseModel):
    # 0단계 — 출생연도 (연기 기한 계산의 기준. 무조건 필요 → 필수)
    birth_year:          int

    # 1단계 — 신분 (현역/보충역(4급)/해당없음 …). 분기의 출발점 → 필수
    identity:            str
    identity_custom:     Optional[str] = None   # "기타" 고르면 직접 입력 → 없을 수도 있으니 Optional
    # 1단계 (학생일 때만 채워짐 → 학생 아니면 비니까 Optional)
    academic_status:     Optional[str] = None   # 재학 | 휴학 | 졸업 | 비진학
    grade:               Optional[str] = None   # 학년
    total_semester:      Optional[int] = None   # 총 이수 학기 수

    # 2단계 — 신체검사 (받았는지 여부는 항상 답하니 필수)
    physical_checked:    bool
    physical_grade:      Optional[str] = None   # 아직 안 받았으면 등급이 없으니 Optional

    # 3단계 — 희망 복무유형 + 드롭다운 선택
    service_type:        Optional[str] = None   # "공군" 등 (미정일 수 있어 Optional)
    service_type_custom: Optional[str] = None   # 목록에 없으면 직접 입력
    specialty:           Optional[str] = None   # 드롭다운(공군→직군)에서 고른 값. 없으면 "없음"

    # 4단계 — 학업 계획 (단수 선택)
    edu_plan:            Optional[str] = None   # 대학원 | 교환학생 | 없음 …
    edu_plan_custom:     Optional[str] = None

    # 5단계 — 해외 체류 계획 (단수 선택)
    abroad_plan:         Optional[str] = None   # 교환학생 | 어학연수 | 없음 …
    abroad_plan_custom:  Optional[str] = None

    # 6단계 — 추가 정보 (복수 선택 + 자유텍스트)
    #   [왜 list] 여기만 여러 개 고를 수 있어서 리스트.
    #   [왜 중요] custom 자유텍스트는 코드가 못 거르는 특수사정 → LLM이 법령으로 검토할 핵심
    extra_info:          list[str] = []
    extra_info_custom:   Optional[str] = None

    # phase 2 (지금은 안 씀 — 나중에 거주지/자격증 매칭용으로 확장)
    residence_sgg:       Optional[str] = None        # 거주지 시군구 → 공공데이터 #15
    licenses:            Optional[list[str]] = None  # 보유 자격/전공 → 공공데이터 #10


# ============================================================
# 응답 "부품" 모델
#
# [왜 있나] EnlistResponse 안에 list 로 여러 건 반복해서 들어가는 작은 조각들.
#          공공데이터(병무청 오픈API) 1건 = 이 클래스 1개.
#          주석 () 안 = 병무청 API의 실제 XML 필드명 (파싱해서 매핑할 때 참고).
# ============================================================

class Document(BaseModel):            # #4 모집병 구비서류 1건 (서류 체크리스트 카드용)
    name:     str          # 제출서류명     (jcseoryuNm)
    required: bool         # 필수 여부       (psjechulYn == "Y")


class Specialty(BaseModel):           # #10 지원가능 특기 1건 (드롭다운/특기 카드용)
    name:          str                    # 특기명    (gsteukgiNm)
    branch:        str                    # 군        (gtcdNm1)
    qualification: Optional[str] = None   # 자격/전공  (gtcdNm2) — 없을 수 있어 Optional


class SocialInstitution(BaseModel):   # #15 사회복무 복무기관 1건 (4급/보충역일 때만)
    name:               str                    # 기관명        (bokmuGgm)
    address:            str                    # 주소          (drmJuso)
    phone:              Optional[str] = None   # 전화          (jeonhwaNo)
    office:             Optional[str] = None   # 관할지방청     (gtcdNm)
    restricted_disease: Optional[str] = None   # 선발제한질병   (sbjhjilbyeong)


class Company(BaseModel):             # #6 전문연구/산업기능 지정업체 1건 (해당 복무유형일 때)
    name:          str                    # 업체명    (eopcheNm)
    address:       Optional[str] = None   # 주소     (eopcheAddr)
    selected_year: Optional[str] = None   # 선정년도  (seonjeongYy)
    assigned:      Optional[int] = None   # 배정인원  (baejeongPcnt)
    # 업종코드(eopjongGbcd)는 매핑표가 복잡해 phase 2로 보류


# ============================================================
# 메인 응답 모델 (내 백엔드 → 프론트) — 챗봇 "첫 분석" 화면
#
# [왜 있나] 폼 제출 후 첫 결과. 계산값 + 공공데이터 부품 + RAG용 텍스트를 담는다.
# ============================================================
class EnlistResponse(BaseModel):
    deadline:            str                        # 최대 연기 기한 (배지에 크게 표시)
    expected_enlist:     Optional[str] = None       # 예상 입영 시기 (모르면 None)

    documents:           list[Document]             # #4 서류 체크리스트 카드
    specialties:         list[Specialty]            # #10 특기 카드
    social_institutions: Optional[list[SocialInstitution]] = None  # #15 (4급일 때만 채움)
    companies:           Optional[list[Company]] = None            # #6  (전문/산업일 때만)

    context_text:        str                        # 병역법 RAG(친구/Gemini)에 넘길 "재료" 텍스트
    session_id:          str                        # ★챗봇 핵심: 후속 대화를 이어가려면
                                                     #  이 세션 ID로 프로필을 기억·재주입한다


# ============================================================
# 후속 대화 모델 (챗봇 2번째 턴부터)
#
# [왜 있나] 첫 분석 뒤 사용자가 자유롭게 묻는 질문/답변.
#          입력 폼 전체를 다시 안 보내고, session_id로 "그 사람"을 식별해
#          저장된 프로필 + 병역법으로 답한다.
# ============================================================
class FollowupRequest(BaseModel):
    session_id: str          # 어느 대화(어느 사용자 프로필)인지 식별
    message:    str          # "석사 도중 입영하면 학교는 어떻게 돼요?"

class FollowupResponse(BaseModel):
    answer: str              # LLM 답변 (자유 텍스트 → 채팅 버블에 그대로 표시)
