from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str
    PINECONE_ENVIRONMENT: str
    COHERE_API_KEY: str
    POSTGRES_URI: str
    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_ENDPOINT: str
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str
    ANTHROPIC_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
