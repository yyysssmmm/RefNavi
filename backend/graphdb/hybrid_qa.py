# hybrid_qa.py

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vectorstore.qa_chain import run_qa_chain
from graphdb.graph_qa import run_graph_rag_qa  # ✅ fallback 내장 함수 사용


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


# ✅ Hybrid QA 실행 함수
def hybrid_qa(
    question: str,
    vector_db_dir=VECTOR_DB_DIR,
    k: int = 3,
    return_sources=False,
    chat_history=[]
):
    print(f"\n💬 질문: {question}")

    # ✅ 1. Graph QA 실행 (히스토리 반영)
    graph_answer = run_graph_rag_qa(question)

    # ✅ 2. Graph 결과가 없거나 부족할 경우 Vector QA 실행
    if not graph_answer or graph_answer.strip() == "":
        vector_answer, sources = run_qa_chain(
            question, k=k, VECTOR_DB_DIR=vector_db_dir, return_sources=True
        )
        vector_docs_summary = format_vector_titles(sources)
    else:
        vector_answer, sources = "", []
        vector_docs_summary = ""

    # ✅ 3. System Prompt 정의
    system_template = SystemMessagePromptTemplate.from_template(
        """You are a helpful assistant. The user may ask in any language, and you must respond in that same language.

    You are given two optional answers to assist you:

    - Answer A (from Vector DB): {vector_answer}
    Related document titles extracted from Vector DB (for you to judge their relevance to the user's question): {vector_docs_summary}

    - Answer B (from Graph DB): {graph_answer}

    Your task is to answer the user's question using the most relevant, informative, and complete source.

    🔍 Source selection rules:
    1. First check the **substance and relevance** of the Graph DB answer:
    - If the Graph DB answer contains specific facts that directly and clearly answer the user's question (e.g., citation count, author names, explicit relationships), it can be used.
    - If the answer contains generic fallback text such as:
    - "현재 구축된 그래프 DB에는 질문한 내용과 일치하는 결과가 없습니다."
    - "관계기반 질문이 아닙니다."
    then it must be ignored.

    2. If Graph DB is not informative, examine the Vector DB answer and its related document titles:
    - If the answer from Vector DB includes a similar fallback like:
    - "현재 구축된 벡터 DB에 사용자의 질문을 답하는 데 도움이 되는 내용이 없습니다."
    then it must also be ignored.

    - If the document titles are clearly related to the topic of the user's question, and the answer provides helpful information, you may use it.

    3. If neither source is informative or clearly helpful, answer the question using your own general knowledge and reasoning.

    ⚠️ IMPORTANT:
    - You must **not** select an answer source just because it exists.
    - Prioritize **actual usefulness** of the content, not just presence.
    - Be especially strict when you detect known fallback or template-like phrases in the source answers.

    ✅ Finish your response with exactly one of:
    - [Answer Source: Vector DB]
    - [Answer Source: Graph DB]
    - [Answer Source: Own Knowledge]
    """
    )

    # ✅ 4. 히스토리 반영
    messages = []
    if chat_history:
        messages.extend(chat_history)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_template] + messages + [
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    )

    # ✅ 5. LLM 실행 체인
    chain = chat_prompt | llm | StrOutputParser()
    response = chain.invoke({
        "question": question,
        "vector_answer": vector_answer,
        "vector_docs_summary": vector_docs_summary,
        "graph_answer": graph_answer
    })

    # ✅ 6. 히스토리 업데이트
    if chat_history is not None:
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=response))

    print("\n📌 Hybrid QA Result:")
    print(response)

    return (response, sources) if return_sources else (response, [])


if __name__ == "__main__":
    question = "안녕"

    response, _ = hybrid_qa(
        question=question,
        k=3,
        return_sources=False
        )

    print(response)