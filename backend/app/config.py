from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parents[2] / '.env'), extra='ignore')
    database_url: str = 'postgresql://paper:paper@localhost:5432/paper'
    siliconflow_api_key: str = ''
    api_base_url: str = 'https://api.siliconflow.cn/v1'
    embedding_model: str = 'BAAI/bge-m3'
    rerank_model: str = 'BAAI/bge-reranker-v2-m3'
    llm_model: str = 'deepseek-ai/DeepSeek-V3'
    relevance_threshold: float = 0.35
    pdf_dir: Path = Path(__file__).resolve().parents[2] / 'data/pdfs'
settings = Settings()
