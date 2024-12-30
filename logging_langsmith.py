import os


def langsmith(project_name=None):
    result = os.getenv("LANGCHAIN_API_KEY")
    if result is None or result.strip() == "":
        print("LangChain API Key가 설정되지 않았습니다.")
        return
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = project_name
    print(f"LangSmith 추적 시작\n[프로젝트명]\n{project_name}")
