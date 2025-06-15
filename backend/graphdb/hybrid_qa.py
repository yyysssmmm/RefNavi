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


def safe_graph_invoke(question: str, chat_history=None) -> str:
    try:
        if chat_history:
            history_str = "\n".join([
                f"Previous Q: {m.content}" if isinstance(m, HumanMessage) else f"Previous A: {m.content}"
                for m in chat_history
            ])
            question = (
                f"Context from previous conversation:\n{history_str}\n\n"
                f"Now, based on the above, answer this current question:\n{question}"
            )
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

    # ✅ 1. Graph QA 실행 (히스토리 반영)
    graph_answer = safe_graph_invoke(question, chat_history)

    # ✅ 2. Graph 답변이 유효하지 않으면 Vector QA 실행
    if not graph_answer or graph_answer.strip() == "":
        vector_answer, sources = run_qa_chain(
            question, k=k, VECTOR_DB_DIR=vector_db_dir, return_sources=True
        )
        vector_docs_summary = format_vector_titles(sources)
    else:
        vector_answer, sources = "", []
        vector_docs_summary = ""

    # ✅ 3. System 메시지 프롬프트
    system_template = SystemMessagePromptTemplate.from_template(
        """You are a helpful assistant. The user may ask in any language, and you must respond in that same language.

    You are given two optional answers to assist you:

    - Answer A (from Vector DB): {vector_answer}
    Related document titles extracted from Vector DB (for you to judge their relevance to the user's question): {vector_docs_summary}

    - Answer B (from Graph DB): {graph_answer}

    Your task is to answer the user's question using the most relevant, informative, and complete source.

    🔍 Source selection rules:
    1. First check the **substance and relevance** of the Graph DB answer:
    - If the answer from Graph DB contains specific facts that directly and clearly answer the user's question (e.g., citation count, author names, explicit relationships), it can be used.
    - However, if the Graph DB answer is vague, incomplete, uninformative, or simply reflects a failed query or generic fallback text, it must be ignored — even if it exists.

    2. If Graph DB is not informative enough, examine the Vector DB:
    - Check if the related document titles are **semantically relevant** to the user's question topic.
    - If they are clearly related, you may use the Vector DB answer to support your response.
    - If they are weakly or loosely related, ignore the Vector DB as well.

    3. If neither source is informative or clearly helpful, answer the question using your own general knowledge and reasoning.

    ⚠️ IMPORTANT:
    - You must **not** select an answer source just because it exists.
    - Prioritize **actual usefulness** of the content, not just presence.
    - For generic or open-ended questions (e.g., "what are prior SOTA models?"), use the source that actually contributes meaningful content.

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
