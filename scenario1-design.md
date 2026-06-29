# mil-ai 시나리오 1 — 입영 시뮬레이터 MVP 설계 문서

> 작성 범위: 시나리오 1 (입영 시뮬레이터) MVP / 백엔드 기준
> 상위 문서: [handover.md](handover.md)

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 프로젝트 | mil-ai — AI 병역 의사결정 코파일럿 |
| 대회 | 2026 병무청·방위사업청·질병관리청 합동 공공데이터·AI 활용 경진대회 |
| 핵심 가치 | **코드 계산**(연기기한) + **병무청 공공데이터**(서류·특기·기관·업체) + **AI 법령 해석** → 개인 맞춤 의사결정 지원 |
| 차별점 | "정보 제공 챗봇"이 아니라 "의사결정 지원 코파일럿" |
| 팀 | 백엔드(나) / RAG·LLM(친구) |
| 데이터 특성 | 병무청 오픈 API는 **2025-09 동결(정적)** → 적재+캐시 방식 |

---

## 2. 시스템 구조도

```
┌──────────────┐
│  프론트엔드   │  입력 위저드 + 결과 대시보드
└──────┬───────┘
       │ ① EnlistRequest (POST /api/simulate/enlist)
       ▼
┌─────────────────────────────────────────────┐
│            내 백엔드 (FastAPI)                │
│  ┌────────────┐ ┌─────────────┐ ┌──────────┐ │
│  │ 계산 엔진   │ │ 공공데이터    │ │ context  │ │
│  │ (기한·일정) │ │ 캐시+필터     │ │ _text    │ │
│  └────────────┘ └──────▲──────┘ │ 빌더     │ │
│                        │         └──────────┘ │
└────────────────────────┼─────────────────────┘
       │ ② EnlistResponse │ 시작 시 1회 적재
       │ {deadline, ...,  ▼
       │  context_text}  ┌──────────────────┐
       │                 │  병무청 오픈 API   │  #4·#10·#15·#12·#6
       ▼                 └──────────────────┘
┌──────────────┐
│  친구 RAG/LLM │  context_text → 법령 검색(ChromaDB) → Qwen2.5 답변
└──────┬───────┘
       │ ③ 최종 답변
       ▼
┌──────────────┐
│  프론트엔드   │  결과 = 기한(②) + 공공데이터(②) + AI답변(③)
└──────────────┘
```

**API 경계 2개 (혼동 주의)**
- 경계 1: 프론트 ↔ 내 백엔드 → `EnlistRequest`/`EnlistResponse`
- 경계 2: 내 백엔드 ↔ 병무청 오픈 API → 내부 적재 (별도 데이터)

---

## 3. 프로그램 구조도 (백엔드)

```
backend/
├── main.py                 # FastAPI 앱, 라우터 등록, 시작 시 캐시 적재
├── requirements.txt
├── core/
│   ├── config.py           # .env (API 키 등)
│   └── dependencies.py     # 서비스 싱글톤 주입
├── api/
│   └── simulate.py         # 시나리오 1 라우터 (POST /enlist, GET 데이터)
├── schemas/
│   └── simulate.py         # 요청/응답 + 공공데이터 모델
├── services/
│   └── simulate.py         # 계산 + 필터 + context_text 조립
├── public_data/
│   └── mma.py              # 병무청 API 클라이언트 (적재 + XML 파싱)
└── data/
    └── raw/                # 공공데이터 시드 JSON (폴백/캐시)
```

**책임 분리**
| 파일 | 책임 (명사 vs 동사) |
|------|---------------------|
| `schemas/` | 데이터 모양 (명사) |
| `services/` | 계산·필터·조립 (동사) |
| `public_data/mma.py` | 병무청 호출·파싱 |
| `api/` | 라우팅만 (얇게) |

---

## 4. 전체 기능 표

| 코드 | 기능 | 세부 | 데이터원 | 담당 | MVP |
|------|------|------|----------|------|-----|
| F1 | 상황 입력 | 위저드 7스텝 + 거주지/자격증 | — | 프론트 | ✅ |
| F2 | 연기기한 계산 | 만28세 / 대학원 만30세 | 코드 | 백엔드 | ✅ |
| F3 | 일정 추정 | 졸업예정·예상입영일 | 코드 | 백엔드 | 🔶 |
| F4 | 현역 안내 | 필요서류(#4)+지원가능 특기(#10) | #4·#10 | 백엔드 | ✅(서류)/🔶(특기) |
| F5 | 사회복무 안내 | 복무기관(#15)+소집계획(#12) | #15·#12 | 백엔드 | 🔶 |
| F6 | 전문연구/산업기능 안내 | 지정업체(#6) | #6 | 백엔드 | 🔶 |
| F7 | context_text 빌더 | 정보+계산+데이터+지시문 | 코드 | 백엔드 | ✅ |
| F8 | AI 답변 | 법령 근거 안내 | RAG | 친구 | ✅ |
| F9 | 공공데이터 캐시 | 시작 시 적재·파싱·폴백 | API | 백엔드 | ✅ |

> ✅ MVP 핵심 / 🔶 여유되면 / 복무유형 분기(F4·F5·F6)는 `service_type`에 따라 택1

---

## 5. UI 설계

### 5.1 화면 흐름
```
랜딩 → [시작] → 입력 위저드(7스텝, 조건분기) → [결과보기]
   → 백엔드 처리(F2~F7) → 친구 RAG(F8) → 결과 대시보드
```

### 5.2 화면별 와이어프레임

**① 랜딩**
```
┌─────────────────────────────────────┐
│        🪖  mil-ai                    │
│   AI 병역 의사결정 코파일럿            │
│  "상황만 입력하면 법령·공공데이터로     │
│   맞춤 병역 계획을 알려드려요"         │
│  ┌────────────────────────────────┐ │
│  │ ① 입영 시뮬레이터   [시작하기 →]│ │
│  │ ② 예비군 가이드      (준비중)   │ │
│  │ ③ 긴급 연기 판단     (준비중)   │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**② 입력 위저드 (한 화면 한 질문)**
```
┌─ 입영 시뮬레이터 ─────────  ●●●○○○○ 3/7 ─┐
│   Q. 희망하는 복무 유형은?                 │
│   ( )육군  ( )해군  ( )공군  ( )해병대     │
│   ( )사회복무  ( )전문연구  ( )미정        │
│   ( )기타 → [________________]            │
│            [← 이전]      [다음 →]         │
└───────────────────────────────────────────┘
```
- 조건 분기: 신분=학생일 때만 학적/학년, 신체검사=했음일 때만 등급
- 기타 패턴: 모든 선택지에 "기타 → 직접입력"(`_custom`)
- 진행률 바 상시 표시

**③ 결과 대시보드 (핵심)**
```
┌─ 내 병역 시뮬레이션 결과 ───────────────────┐
│ ┌─────────────────────────────────────────┐ │
│ │ 📅 최대 입영 연기 기한                    │ │ ← F2
│ │     2029-12-31  (만 28세 기준)           │ │
│ │     예상 입영일  2027-09 경               │ │ ← F3
│ └─────────────────────────────────────────┘ │
│ ─ 타임라인 ───────────────────────────────  │ ← F3🔶
│  현재 ●──졸업'27 ●──기한'29 ●──전역'31      │
│ ─ 📋 복무 준비  [공공데이터] ─────────────  │ ← F4~F6
│  필요 서류(#4)        지원가능 특기(#10)     │
│  • 주민등록등본 [필수] • 보병                │
│  • 병역증명서  [필수]  • 통신 …             │
│ ─ 🤖 AI 코파일럿 ─────────────────────────  │ ← F8
│  "휴학 중이면 병역법 제60조에 따라 재학생     │
│   입영연기를 매 학기 갱신… 석사 진학 시       │
│   만 30세까지 연기 가능"  [근거: 병역법 60조]│
└─────────────────────────────────────────────┘
```

### 5.3 화면 ↔ 데이터 매핑
| 화면 요소 | 출처 | 담당 |
|-----------|------|------|
| 연기 기한 / 예상 입영일 | 코드 계산 | 백엔드 |
| 필요 서류 [필수/선택] | #4 | 백엔드 |
| 지원가능 특기 | #10 | 백엔드 |
| 사회복무 기관 (4급) | #15·#12 | 백엔드 |
| 지정업체 (전문연구/산업기능) | #6 | 백엔드 |
| AI 답변 + 법령 근거 | context_text → RAG | 친구 |

---

## 6. API 명세서

### 6.1 백엔드 엔드포인트

| Method | Path | 요청 | 응답 | 기능 | MVP |
|--------|------|------|------|------|-----|
| POST | `/api/simulate/enlist` | `EnlistRequest` | `EnlistResponse` | 메인 시뮬레이션 (F1~F7) | ✅ |
| GET | `/api/simulate/documents?service_type=` | 쿼리 | `DocumentsResponse` | 필요서류 단독(#4) | 🔶 |
| GET | `/api/simulate/specialties?service_type=` | 쿼리 | `SpecialtiesResponse` | 지원가능 특기(#10) | 🔶 |
| GET | `/api/simulate/social/institutions?sgg=` | 쿼리 | `SocialInstitutionsResponse` | 복무기관(#15) | 🔶 |
| GET | `/api/simulate/agencies` | — | `AgenciesResponse` | 지정업체(#6) | 🔶 |
| GET | `/health` | — | `{status}` | 헬스체크 | ✅ |

### 6.2 스키마

**요청**
```python
class EnlistRequest(BaseModel):
    birth_year:          int
    identity:            str
    identity_custom:     Optional[str]
    academic_status:     Optional[str]
    grade:               Optional[str]
    total_semester:      Optional[int]
    physical_checked:    bool
    physical_grade:      Optional[str]
    service_type:        Optional[str]
    service_type_custom: Optional[str]
    edu_plan:            Optional[str]
    edu_plan_custom:     Optional[str]
    abroad_plan:         Optional[str]
    abroad_plan_custom:  Optional[str]
    extra_info:          list[str]
    extra_info_custom:   Optional[str]
    residence_sgg:       Optional[str] = None   # (phase 2) 거주지 시군구 → #15, MVP 미사용
    licenses:            Optional[list[str]] = None  # (phase 2) 자격/전공 → #10, MVP 미사용
```

**응답 부품 (공공데이터 모델)**
```python
class Document(BaseModel):           # #4
    name:     str          # jcseoryuNm 제출서류명
    required: bool         # psjechulYn == "Y"

class Specialty(BaseModel):          # #10
    name:          str             # gsteukgiNm 특기명
    branch:        str             # gtcdNm1    군
    qualification: Optional[str]   # gtcdNm2    자격/전공

class SocialInstitution(BaseModel):  # #15
    name:               str             # bokmuGgm   기관명
    address:            str             # drmJuso    도로명주소
    phone:              Optional[str]   # jeonhwaNo
    office:             Optional[str]   # gtcdNm     관할지방청
    restricted_disease: Optional[str]   # sbjhjilbyeong 선발제한질병

class Company(BaseModel):            # #6
    name:          str             # eopcheNm   업체명
    address:       Optional[str]   # eopcheAddr
    selected_year: Optional[str]   # seonjeongYy 선정년도
    assigned:      Optional[int]   # baejeongPcnt 배정인원
    # industry(eopjongGbcd) 생략 — 업종코드 매핑표 보류 (phase 2)
```

**메인 응답**
```python
class EnlistResponse(BaseModel):
    deadline:            str
    expected_enlist:     Optional[str]
    documents:           list[Document]                    # #4
    specialties:         list[Specialty]                   # #10
    social_institutions: Optional[list[SocialInstitution]] # #15 (4급)
    companies:           Optional[list[Company]]           # #6 (전문연구/산업기능)
    context_text:        str
```

**GET 응답 (부품 재사용)**
```python
class DocumentsResponse(BaseModel):
    service_type: str
    documents:    list[Document]

class SpecialtiesResponse(BaseModel):
    service_type: str
    specialties:  list[Specialty]

class SocialInstitutionsResponse(BaseModel):
    region:       Optional[str]
    institutions: list[SocialInstitution]

class AgenciesResponse(BaseModel):
    companies:    list[Company]
```

---

## 7. 사용 오픈 API (병무청) 정리

### 7.1 채택 API 목록

| API | 데이터셋 ID | 용도 | 트리거 |
|-----|------------|------|--------|
| 모집병 구비서류 | 3066489 | 군/특기별 필요서류 | 현역 선택 |
| 모집병 군별·특기별 지원가능 | 3066750 | 자격/전공→지원가능 특기 | 현역 선택 |
| 사회복무 복무기관 | 3066757 | 거주지 사회복무 기관 | 4급/사회복무 |
| 사회복무 년도별 소집계획 | 3066753 | 연도별 계획인원 | 4급/사회복무 |
| 전문연구/산업기능 지정업체 | 3066759 | 지정업체 목록 | 전문연구/산업기능 |

> 공통: host `apis.data.go.kr/1300000`, 인증 `serviceKey`, **응답 XML**, 필터 파라미터 없음(`numOfRows`/`pageNo`만), **2025-09 동결**.

### 7.2 API별 필드 매핑 (병무청 → 내 모델 → UI)

**#4 모집병 구비서류** — `/gbSeoryu/list`
| 병무청 필드 | 의미 | → 모델 | UI |
|-------------|------|--------|-----|
| `gunGbnm` | 군 | (필터키) | — |
| `gsteukgiNm` | 특기 | (필터키) | — |
| `jcseoryuNm` | 서류명 | `Document.name` | 서류 목록 |
| `psjechulYn` | 필수여부 | `Document.required` | 필수/선택 배지 |

**#10 군별·특기별 지원가능** — `/mjbJiWon/list`
| `gtcdNm1` | 군 | `Specialty.branch` | — |
| `gsteukgiNm` | 특기명 | `Specialty.name` | 특기 목록 |
| `gtcdNm2` | 자격/전공 | `Specialty.qualification` | 매칭 표시 |
| `gubun` | 자격/면허/전공 구분 | (매칭 로직) | — |

**#15 사회복무 복무기관** — `/bmggJeongBo/list`
| `bokmuGgm` | 기관명 | `SocialInstitution.name` | 기관 카드 |
| `drmJuso` | 주소 | `.address` | 위치 |
| `jeonhwaNo` | 전화 | `.phone` | 연락처 |
| `gtcdNm` | 관할지방청 | `.office` | — |
| `bjdsggjusoCd` | 시군구코드 | (거주지 필터키) | — |
| `sbjhjilbyeong` | 선발제한질병 | `.restricted_disease` | 주의 안내 |

**#12 사회복무 소집계획** — `/sHBMGyeHeok/list`
| `shbmsojipDt` | 소집년도 | (필터키) | — |
| `jhgyehoekPcnt` | 계획인원 | (안내 텍스트) | 계획 규모 |
| `bmgigwanCd` | 복무기관코드 | (#15와 조인키) | — |
| `bmbunyaNm` | 복무분야 | (안내) | 분야 |

**#6 전문연구/산업기능 지정업체** — `/jjEopChe/list2/getjjEopChe`
| `eopcheNm` | 업체명 | `Company.name` | 업체 카드 |
| `eopcheAddr` | 주소 | `.address` | 위치 |
| `eopjongGbcd` | 업종코드 | `.industry`(매핑) | 업종 |
| `seonjeongYy` | 선정년도 | `.selected_year` | — |
| `baejeongPcnt` | 배정인원 | `.assigned` | 규모 |

### 7.3 캐싱 전략 (시드 JSON 중심)

```
[개발 시 1회]  load_all() 라이브 적재 → XML 파싱 → data/raw/*.json 저장 (시드 생성)

[앱 시작 시]   data/raw/*.json 시드 로드 → 메모리 캐시(list[dict])
               (시드 없으면 load_all() 라이브로 폴백)

[요청마다]     service에서 캐시를 service_type로 코드 필터 (병무청 재호출 없음)
```
- 데이터가 **동결**이라 시드로 둬도 손해 0 + 데모 중 API 다운 위험 제거
- 라이브 적재 코드(`load_all`)는 "병무청에서 받아오는 법" 시연용으로 보존

### 7.4 MMAClient 메서드

| 메서드 | 병무청 엔드포인트 | API |
|--------|------------------|-----|
| `load_documents()` | `/1300000/gbSeoryu/list` | #4 |
| `load_specialties()` | `/1300000/mjbJiWon/list` | #10 |
| `load_social_institutions()` | `/1300000/bmggJeongBo/list` | #15 |
| `load_social_plan()` | `/1300000/sHBMGyeHeok/list` | #12 |
| `load_companies()` | `/1300000/jjEopChe/list2/getjjEopChe` | #6 |
| `load_all()` | (위 5개) | 시작 시 |

---

## 8. 데이터 흐름 (End-to-End)

```
1. 프론트 위저드 → EnlistRequest (JSON)
2. POST /api/simulate/enlist
3. service.run(req):
   a. deadline 계산 (birth_year + 28/30)
   b. 졸업·입영 추정
   c. service_type 분기 → 캐시 필터
        현역      → documents(#4) + specialties(#10)
        4급/사회  → social_institutions(#15) + 소집계획(#12)
        전문/산업 → companies(#6)
   d. context_text 조립 (사용자정보 + 계산결과 + 공공데이터 + 지시문)
4. EnlistResponse 반환 (구조화 데이터 + context_text)
5. 친구 RAG: context_text → 법령 검색 → Qwen2.5 답변
6. 프론트 결과 대시보드: 기한 + 서류/특기 + AI 답변
```

---

## 9. MVP 범위

> **확정 데모 라인:** `현역 선택 → 📅기한 계산 + 📋#4 필요서류(+군별 특기목록) + 🤖AI 법령 답변`
> 사회복무(#15·#12)·지정업체(#6)는 "있다" 수준으로 단순화. 위저드는 기존 7스텝 그대로(신규 입력 0).

| | 항목 |
|---|---|
| ✅ 핵심 | 입력 위저드 · 기한 계산 · #4 서류 · context_text · AI 답변 · 결과 화면 |
| 🔶 여유 | #10 특기 · #15·#12 사회복무 · #6 지정업체 · 타임라인 · GET 데이터 엔드포인트 |
| ❌ 제외 | 시나리오 2·3 · 후속 질문 챗 · 로그인/저장 · #18 경쟁률 · 다국어 |

---

## 부록: 확정된 결정 사항 (2026-06)

데모/MVP 원칙: **"현역 한 줄을 확실하게, 나머지는 단순하게."**

1. **거주지(`residence_sgg`) — MVP 미사용.** 필드는 optional로만 유지(위저드 스텝 추가 X). 사회복무 기관은 지방청 단위/대표 예시로 안내. → phase 2.
2. **자격증(`licenses`) — MVP 미사용.** #10 특기는 **군 필터만**으로 "지원가능 특기 목록" 노출(자격증↔특기 문자매칭은 데모 위험으로 제외). → phase 2.
3. **캐싱 — 시드 JSON 중심.** 개발 때 `load_all()`로 1회 라이브 적재 → `data/raw/*.json` 저장 → 런타임은 시드 로드. 라이브 코드는 시연용 보존. (동결 데이터라 시드 손해 0 + 데모 안정)
4. **업종코드(`eopjongGbcd`) — 무시.** #6 `Company.industry` 필드 생략. 업체명·주소·배정인원만 노출.
