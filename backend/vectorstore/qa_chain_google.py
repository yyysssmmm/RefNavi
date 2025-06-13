import os
import sys
from typing import List, Tuple, Union

# ✅ tokenizer warning 제거
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ✅ RefNavi 루트 경로 추가 (상대 경로 문제 방지용)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# ✅ LangChain 최신 모듈
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# ✅ .env 파일 명시적으로 로딩
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path)

# ✅ API Key 로딩
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY가 .env에서 불러와지지 않았습니다!")

# ✅ 설정
VECTOR_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ✅ 전역 embedding + vector DB 인스턴스
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# ✅ 대화 히스토리 메모리
memory = ConversationBufferMemory(
    memory_key='chat_history',
    return_messages=True,
    output_key='answer'
)

SYSTEM_PROMPT = """You are a helpful research assistant. 
Answer questions based on the retrieved documents if available. 
If no documents are retrieved, answer using your general knowledge."""

def run_qa_chain(
    query: str,
    k: int = 3,
    VECTOR_DB_DIR: str = "chroma_db",
    return_sources: bool = False,
) -> Union[str, Tuple[str, List[Document]]]:
    print(f"\n🔍 질의: '{query}' → 유사 문서 검색 중...")

    # ✅ Gemini LLM 인스턴스 생성
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash",
        temperature=0,
        google_api_key=GOOGLE_API_KEY,
        system_prompt = SYSTEM_PROMPT
    )

    db = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

    # ✅ RAG QA 체인 생성
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=db.as_retriever(search_kwargs={"k": k}),
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"output_key": "answer"} 
    )

    result = qa_chain.invoke({"question": query})
    answer = result["answer"]
    sources: List[Document] = result.get("source_documents", [])

    # ✅ 참조 문서 출력
    if sources:
        print("\n📚 참조 문서:")
        for i, doc in enumerate(sources, 1):
            print(f"\n--- Source {i} ---")
            print(f"제목: {doc.metadata.get('title')}")
            print(f"구분: {doc.metadata.get('source')}")
            print(f"연도: {doc.metadata.get('year')}")
            print(f"저자: {doc.metadata.get('authors')}")
            print(f"요약: {doc.page_content[:300]}...")
    else:
        print("\n📚 참조 문서가 없습니다.")

    return (answer, sources) if return_sources else (answer, [])