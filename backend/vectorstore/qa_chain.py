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
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# ✅ 사용자 정의 모듈
from dotenv import load_dotenv

# ✅ .env 파일 명시적으로 로딩
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY가 .env에서 불러와지지 않았습니다!")

# ✅ 설정
VECTOR_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ✅ 전역 embedding + vector DB 인스턴스
try:
    print("🧠 HuggingFace 임베딩 모델 로딩 중...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
except Exception as e:
    print(f"⚠️ HuggingFace 모델 로딩 실패: {str(e)}")
    print("🔄 로컬 임베딩 모드로 전환...")
    # 로컬 임베딩 모드 설정
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./models"
    os.environ["TRANSFORMERS_CACHE"] = "./models"
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            cache_folder="./models",
            model_kwargs={'device': 'cpu'}
        )
    except Exception as e:
        print(f"❌ 로컬 임베딩 모드도 실패: {str(e)}")
        raise RuntimeError("임베딩 모델을 로드할 수 없습니다. 인터넷 연결을 확인해주세요.")

# ✅ QA 프롬프트 템플릿
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

def run_qa_chain(
    query: str,
    k: int = 3,
    VECTOR_DB_DIR = "chroma_db",
    return_sources: bool = False,

) -> Union[str, Tuple[str, List[Document]]]:
    print(f"\n🔍 질의: '{query}' → 유사 문서 검색 중...")

    llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)
    db = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": k}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    result = qa_chain.invoke({"query": query})
    answer = result["result"]
    sources: List[Document] = result["source_documents"]

    print("\n📌 답변:")
    print(answer)
    print("\n📚 참조 문서:")
    for i, doc in enumerate(sources, 1):
        print(f"\n--- Source {i} ---")
        print(f"제목: {doc.metadata.get('title')}")
        print(f"구분: {doc.metadata.get('source')}")
        print(f"연도: {doc.metadata.get('year')}")
        print(f"저자: {doc.metadata.get('authors')}")
        print(f"요약: {doc.page_content[:300]}...")

    return (answer, sources) if return_sources else answer

# ✅ 단독 실행용
if __name__ == "__main__":
    run_qa_chain("What is the contribution of the Transformer paper?", k=5)
