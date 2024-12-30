from langchain_openai import ChatOpenAI
from langchain_core.prompts import load_prompt


class QueryRouter:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
        self.router_prompt = load_prompt("prompts/router.yaml", encoding="utf-8")

    def route(self, query: str) -> str:
        chain = self.router_prompt | self.llm
        response = chain.invoke({"question": query})
        return response.content.lower().strip()
