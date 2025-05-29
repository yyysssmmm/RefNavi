import os
from typing import List, Tuple, Union
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from .retriever import get_top_k_documents
from dotenv import load_dotenv

import sys

# RefNavi 루트 경로를 sys.path에 명시적으로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


# 🔐 .env 경로 명시적으로 지정하여 로드
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY가 .env에서 불러와지지 않았습니다!")

# ✅ 설정
VECTOR_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ✅ 프롬프트 템플릿 정의
QA_TEMPLATE = """
You are a research assistant. Based on the following documents, answer the user's query as accurately and concisely as possible.

Context:
{context}

Question: {question}
Answer:
"""

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=QA_TEMPLATE
)

def run_qa_chain(query: str, k: int = 3, return_sources: bool = False) -> Union[str, Tuple[str, List[Document]]]:
    # 🔁 벡터 DB 로드
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

    # 🔍 retriever 구성
    retriever = db.as_retriever(search_kwargs={"k": k})

    # 🤖 LLM + QA Chain 구성
    llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    result = qa_chain({"query": query})
    answer = result["result"]
    sources: List[Document] = result["source_documents"]

    print("\n📌 답변:")
    print(answer)
    print("\n📚 참조 문서:")
    for i, doc in enumerate(sources, 1):
        print(f"\n--- Source {i} ---")
        print(f"제목: {doc.metadata.get('title')}")
        print(f"연도: {doc.metadata.get('year')}")
        print(f"저자: {doc.metadata.get('authors')}")
        print(f"요약: {doc.page_content[:300]}...")

    if return_sources:
        return answer, sources
    return answer

# ✅ 테스트용 실행 코드
if __name__ == "__main__":
    test_query = "What is layer normalization and how does it differ from batch normalization?"
    run_qa_chain(test_query, k=3)