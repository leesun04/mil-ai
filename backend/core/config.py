#환경변수(.env) 로딩
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env 에서 자동으로 읽어오는거임
    MMA_API_KEY: str #이거 내 공공 데이터 API 인증 키
    chatbot_url : str

    model_config = SettingsConfigDict(
        env_file=".env",            # .env 파일에서 읽어오기
        env_file_encoding="utf-8", #utf-8 인코딩이라는데 필요하다네 이거
    )

# 앱 전체에서 공유할 설정 객체 하나 (import 해서 settings.MMA_API_KEY 로 사용)
settings = Settings()


