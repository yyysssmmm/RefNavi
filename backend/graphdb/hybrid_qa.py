import sys
import os

# 🔧 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# ✅ 기존 vector / graph QA 로직 import
from vectorstore.qa_chain import run_qa_chain  # VectorRAG 함수
from graphdb.graph_qa import chain as graph_chain  # GraphRAG 체인

base_dir = os.path.join(os.path.dirname(__file__), "../utils/metadata")
VECTOR_DB_DIR = os.path.join(base_dir, "chroma_db")

# ✅ 하이브리드 응답 생성 LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)

# ✅ 벡터/그래프 응답 통합 프롬프트
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a scientific assistant who integrates and refines two candidate answers to a user question using clear and concise language.\n\n"
     "You are given two answers to the same question:\n\n"
     ">>> Answer A (from Vector DB):\n{vector_answer}\n\n"
     ">>> Answer B (from Graph DB):\n{graph_answer}\n\n"
     "Your task is to:\n"
     "1. Carefully analyze both answers.\n"
     "2. Write a single, polished and informative answer to the user that:\n"
     "   - prioritizes the most accurate and relevant information,\n"
     "   - avoids repetition or conflicting information,\n"
     "   - avoids directly stitching the two answers together awkwardly,\n"
     "   - reads naturally as a unified answer.\n"
     "3. If both answers are useful, integrate them. If only one is good, use that one. If neither is helpful, say that.\n\n"
     "📌 At the end of your response, write on a separate line which answer contributed most:\n"
     "   - [Mainly from Vector DB], [Mainly from Graph DB], or [Combined equally]\n"
     "   - Do not say 'Both' unless both provided distinct and meaningful content."
    )
])


# ✅ Graph QA 실패 대비
def safe_graph_invoke(question: str) -> str:
    try:
        result = graph_chain.invoke({"query": question})
        return result.get("result", "")
    except Exception as e:
        print(f"⚠️ Graph QA failed: {e}")
        return "Graph QA failed to return an answer."

# ✅ 하이브리드 QA 함수
def hybrid_qa(question: str, vector_db_dir=VECTOR_DB_DIR, k: int = 3):
    print(f"\n💬 질문: {question}")
    
    # Vector DB 응답
    vector_answer, _ = run_qa_chain(question, k=k, VECTOR_DB_DIR=vector_db_dir, return_sources=True)

    # Graph DB 응답
    graph_answer = safe_graph_invoke(question)

    # 통합 응답 생성
    final_chain = prompt | llm | StrOutputParser()
    final_response = final_chain.invoke({
        "question": question,
        "vector_answer": vector_answer,
        "graph_answer": graph_answer
    })

    print("\n📌 Hybrid QA Result:")
    print(final_response)


# ✅ 테스트 실행
if __name__ == "__main__":
    hybrid_qa("Who proposed the LSTM model?")
