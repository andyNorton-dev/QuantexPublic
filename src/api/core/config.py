from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).parent.parent

class Server(BaseModel):
    host: str = '0.0.0.0'
    port: int = 5000

class TaskType(BaseModel):
    Game: str = 'game'
    Daily: str = 'daily'
    Task: str = 'task'

class AuthJwt(BaseModel):
    keys_dir: Path = BASE_DIR / 'auth' / 'certs'
    private_key_path: Path = keys_dir / 'jwt-private.pem'
    public_key_path: Path = keys_dir / 'jwt-public.pem'
    algorithm: str = 'RS256'
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

class S3Config(BaseModel):
    bucket: str
    region: str = 'ru-central1'
    access_key: str
    secret_key: str
    endpoint: str = 'https://storage.yandexcloud.net'

class Settings(BaseSettings):
    task_type: TaskType = TaskType()
    database_url: str
    bot_token: str
    server: Server = Server()
    auth_jwt: AuthJwt = AuthJwt()
    s3: Optional[S3Config] = None

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        env_nested_delimiter = '__'

settings = Settings()