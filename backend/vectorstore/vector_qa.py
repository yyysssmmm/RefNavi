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
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# ✅ 사용자 정의 모듈
from dotenv import load_dotenv

# ✅ .env 파일 명시적으로 로딩
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY가 .env에서 불러와지지 않았습니다!")

# ✅ 설정
base_dir = os.path.join(os.path.dirname(__file__), "..")
VECTOR_DB_DIR = os.path.join(base_dir, "utils/metadata/chroma_db")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ✅ 전역 embedding + vector DB 인스턴스
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

def run_qa_chain(
    query: str,
    chat_history: List = [],
    k: int = 3,
    VECTOR_DB_DIR=VECTOR_DB_DIR,
    return_sources: bool = False,
) -> Union[str, Tuple[str, List[Document]]]:
    print(f"\n🔍 질의: '{query}' → 유사 문서 검색 중...")

    llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)
    db = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

    retrieved_docs = db.similarity_search(query, k=k)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    # ✅ system + history + human message 기반 prompt 구성
    qa_template = """
You are RefNavi, an academic assistant chatbot that helps users understand scientific papers using retrieved documents and your own knowledge.

Your goal is to answer the user's question as clearly and informatively as possible.

If the retrieved context contains useful information related to the user's question, use it to answer.

If the retrieved documents are **not relevant** or **not helpful**, you MUST say this first:

  "현재 구축된 벡터 DB에 사용자의 질문을 답하는데 도움이 되는 내용이 없습니다. 자체 지식으로 대답합니다."

Then, proceed to answer using your own general academic knowledge.

Maintain a polite and helpful tone in all responses.

---

검색된 문서 내용 (Context):
{context}

질문 (Question):
{question}

답변 (Answer):
"""

    system_prompt = SystemMessagePromptTemplate.from_template(qa_template)
    human_prompt = HumanMessagePromptTemplate.from_template("{question}")
    chat_prompt = ChatPromptTemplate.from_messages([
        system_prompt,
        *chat_history,
        human_prompt
    ])

    chain = chat_prompt | llm | StrOutputParser()
    inputs = {"context": context, "question": query}
    answer = chain.invoke(inputs)

    sources = retrieved_docs
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

    print(answer)
    return (answer, sources) if return_sources else (answer, [])

# ✅ 단독 실행용
if __name__ == "__main__":
    run_qa_chain("안녕")
    run_qa_chain("transformer 논문에 대해 설명해줘")
    run_qa_chain("그 논문에 대해 다시 설명해줘")
