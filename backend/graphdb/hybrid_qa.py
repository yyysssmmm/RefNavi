from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

from vectorstore.qa_chain import run_qa_chain
from graphdb.graph_qa import chain as graph_chain

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

base_dir = os.path.join(os.path.dirname(__file__), "../utils/metadata")
VECTOR_DB_DIR = os.path.join(base_dir, "chroma_db")

llm = ChatOpenAI(model="gpt-4", temperature=0)


# ✅ 벡터 문서 title 요약용 함수
def format_vector_titles(docs: list[Document]) -> str:
    if not docs:
        return "[Vector DB] No documents retrieved."

    result = "[Vector DB] The following document titles were retrieved by similarity search:\n\n"
    for i, doc in enumerate(docs, 1):
        title = doc.metadata.get("title", "Unknown Title")
        result += f"{i}. {title}\n"
    return result.strip()


def safe_graph_invoke(question: str) -> str:
    try:
        result = graph_chain.invoke({"query": question})
        return result.get("result", "")
    except Exception as e:
        print(f"⚠️ Graph QA failed: {e}")
        return ""


def hybrid_qa(
    question: str,
    vector_db_dir=VECTOR_DB_DIR,
    k: int = 3,
    return_sources=False,
    chat_history=None
):
    print(f"\n💬 질문: {question}")

    # ✅ 1. Vector QA 실행: 응답 + 소스
    vector_answer, sources = run_qa_chain(
        question, k=k, VECTOR_DB_DIR=vector_db_dir, return_sources=True
    )
    vector_docs_summary = format_vector_titles(sources)

    # ✅ 2. Graph QA 실행
    graph_answer = safe_graph_invoke(question)

    # ✅ 3. System 메시지 프롬프트
    system_template = SystemMessagePromptTemplate.from_template(
    """You are a helpful assistant. The user may ask in any language, and you must respond in that same language.

    You are given two optional answers to assist you:

    - Answer A (from Vector DB): {vector_answer}
    Related document titles extracted from Vector DB (for you to judge their relevance to the user's question): {vector_docs_summary}

    - Answer B (from Graph DB): {graph_answer}

    Your task is to answer the user's question using the most relevant and informative source.

    🔍 Source selection rules:
    1. If the Graph DB gives a clear and specific answer (e.g., author names, publication year, citation counts), use it.
    2. If the Graph DB is unhelpful, check if the document titles from Vector DB are clearly semantically related to the question topic.
    - If titles are not relevant or only loosely connected, IGNORE the Vector DB answer.
    - Especially for greetings or casual questions (e.g., “hello”, “안녕”), do NOT use the Vector DB at all, even if it retrieved documents.

    3. If neither source is useful, use your own general knowledge to answer.

    ⚠️ VERY IMPORTANT:
    - Do not rely on the existence of documents alone. Only use them if they directly help answer the question.

    ✅ Finish your response with exactly one of:
    - [Answer Source: Vector DB]
    - [Answer Source: Graph DB]
    - [Answer Source: Own Knowledge]
    """
    )


    # ✅ 4. 이전 대화 히스토리 추가
    messages = []
    if chat_history:
        messages.extend(chat_history)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_template] + messages + [
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    )

    # ✅ 5. LLM 체인 실행
    chain = chat_prompt | llm | StrOutputParser()
    response = chain.invoke({
        "question": question,
        "vector_answer": vector_answer,
        "vector_docs_summary": vector_docs_summary,
        "graph_answer": graph_answer
    })

    # ✅ 6. 히스토리 갱신
    if chat_history is not None:
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=response))

    print("\n📌 Hybrid QA Result:")
    print(response)

    return (response, sources) if return_sources else (response, [])
