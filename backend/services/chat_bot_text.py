# backend/test.py
# 친구 챗봇 한 번에 호출 → 결과 print
# 실행:  python test.py

import httpx

def get_env(key, path=".env"):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise KeyError(f"{key} 가 .env 에 없음")

URL = get_env("CHATBOT_URL")

facts = {
    "birth_year": 2001, "current_age": 25,
    "identity": "현역", "physical_grade": "1급",
    "academic_status": "휴학", "grade": "3학년",
    "service_type": "공군", "specialty": "정보보호병",
    "edu_plan": "대학원", "abroad_plan": "없음",
}
QUESTION = "나 언제까지 입영 연기 가능해?"
SESSION = "test_001"

# facts + question + sessionId 를 한 방에
r = httpx.post(
    URL,
    json={"facts": facts, "question": QUESTION, "sessionId": SESSION},
    timeout=60,        # LLM 느림 → 넉넉히
)

print("HTTP", r.status_code)
print("─" * 50)
print("Q:", QUESTION)
print("─" * 50)
print("A:", r.json().get("output", "(output 없음)"))