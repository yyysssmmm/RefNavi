# 📁 파일: backend/chains/rag_chain.py

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from langchain.schema import Generation, LLMResult
from dotenv import load_dotenv
from typing import List
import os

load_dotenv()

# ✅ 1. 벡터 DB 및 임베딩 로드
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb = Chroma(
    collection_name="refnavi_abstracts",
    embedding_function=embedding
)

# ✅ 2. Retriever 구성
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# ✅ 3. 테스트용 Mock LLM 정의
class MockLLM(LLM):

    def _call(self, prompt: str, stop: List[str] = None) -> str:
        return "This is a mock response for testing."

    def _generate(self, prompts, **kwargs):
        return LLMResult(generations=[[Generation(text="This is a mock response for testing.")]])

    @property
    def _llm_type(self):
        return "mock-llm"

llm = MockLLM()

# ✅ 4. RetrievalQA 체인 생성
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# ✅ 5. 테스트 실행
if __name__ == "__main__":
    query = "What is the contribution of the Transformer paper?"
    result = qa_chain.invoke(query)

    print("\n📢 답변:\n", result['result'])
    print("\n📚 참고한 문서들:")
    for doc in result['source_documents']:
        print("-", doc.metadata.get("title"))
