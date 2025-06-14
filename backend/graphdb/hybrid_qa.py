from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from vectorstore.qa_chain import run_qa_chain
from graphdb.graph_qa import chain as graph_chain

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

base_dir = os.path.join(os.path.dirname(__file__), "../utils/metadata")
VECTOR_DB_DIR = os.path.join(base_dir, "chroma_db")

llm = ChatOpenAI(model="gpt-4", temperature=0)

def safe_graph_invoke(question: str) -> str:
    try:
        result = graph_chain.invoke({"query": question})
        return result.get("result", "")
    except Exception as e:
        print(f"⚠️ Graph QA failed: {e}")
        return ""

def hybrid_qa(question: str, vector_db_dir=VECTOR_DB_DIR, k: int = 3, return_sources=False, chat_history=None):
    print(f"\n💬 질문: {question}")
    
    # Vector DB 응답
    vector_answer, sources = run_qa_chain(question, k=k, VECTOR_DB_DIR=vector_db_dir, return_sources=return_sources)

    # Graph DB 응답
    graph_answer = safe_graph_invoke(question)

    # 🔁 이전 대화 반영 메시지 구성
    messages = chat_history[:] if chat_history else []

    messages.append(
        ("system",
        "You are a helpful assistant. The user may ask in any language, and you must respond in that same language.\n\n"
        "You are given two optional answers to assist you:\n"
        "- Answer A (from Vector DB): {vector_answer}\n"
        "- Answer B (from Graph DB): {graph_answer}\n\n"
        "Your job is to answer the user's question based on:\n"
        "1. These retrieved answers **if relevant**, or\n"
        "2. Your own knowledge **if the retrieved answers are empty or unrelated**.\n\n"
        "⚠️ Do NOT say 'I was given two answers'. Simply answer naturally as if you know the information.\n\n"
        "📌 At the end of your response, add one of the following lines to indicate the main source:\n"
        "- [Answer Source: Vector DB]\n"
        "- [Answer Source: Graph DB]\n"
        "- [Answer Source: Own Knowledge]\n"
        "- [Answer Source: Combined]"
        )
    )


    messages.append(HumanMessage(content=question))

    prompt = ChatPromptTemplate.from_messages(messages)

    final_chain = prompt | llm | StrOutputParser()

    response = final_chain.invoke({
        "question": question,
        "vector_answer": vector_answer,
        "graph_answer": graph_answer
    })

    # 🧾 히스토리 반영
    if chat_history is not None:
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=response))

    print("\n📌 Hybrid QA Result:")
    print(response)
    return (response, sources) if return_sources else (response, [])
