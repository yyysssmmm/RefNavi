# hybrid_qa.py

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vectorstore.vector_qa import run_qa_chain
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
    graph_answer = run_graph_rag_qa(question, chat_history)

    # ✅ 2. Vector QA 실행
    vector_answer, sources = run_qa_chain(
        question, k=k, VECTOR_DB_DIR=vector_db_dir, return_sources=True, chat_history=chat_history
    )
    vector_docs_summary = format_vector_titles(sources)

    # ✅ 3. System Prompt 정의
    system_template = SystemMessagePromptTemplate.from_template(
        """You are a helpful assistant. The user may ask in any language, and you must respond in that same language.

    You are provided with three sources of information to answer the user's question:

    - 📘 **Vector DB Answer**: {vector_answer}  
    Document titles retrieved from Vector DB: {vector_docs_summary}

    - 🔗 **Graph DB Answer**: {graph_answer}

    - 🧠 **Your own general knowledge**

    🎯 Your task is to synthesize a comprehensive, accurate, and helpful response by **integrating all three sources**:
    1. Use specific facts and insights from **Vector DB and Graph DB** whenever possible — such as citation contexts, abstract content, relationships, or keywords.
    2. Feel free to supplement with **your own general knowledge or reasoning** to fill in any missing details, clarify vague parts, or connect ideas.
    3. You must meaningfully incorporate **all three sources**, but you may emphasize the one that contributed most to answering the user's question.
    - Reflect this emphasis **naturally in the tone or content** of your answer, **not by directly naming the source**.

    💡 Think of yourself as a research assistant combining multiple views to give the best possible explanation — clear, informative, and well-grounded.

    ⚠️ Never mention the sources explicitly in your answer (e.g., do not say "According to the Graph DB...").
    ✅ Instead, at the end of your answer, include the following tag indicating which sources were most helpful:
    [Answer Source: (e.g., Mainly Graph DB + Own Knowledge)]
    """
    )


    # ✅ 4. 히스토리 반영

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_template] + chat_history + [
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