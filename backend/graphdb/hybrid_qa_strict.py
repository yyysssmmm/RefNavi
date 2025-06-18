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
    graph_answer = run_graph_rag_qa(question, chat_history=chat_history)

    graph_failure_msgs = ["현재 구축된 그래프 DB에는 질문한 내용과 일치하는 결과가 없습니다. 다른 질문을 하거나 다른 모델 (벡터 DB 혹은 하이브리드 방식)을 이용해주세요.",
                    "관계기반 질문이 아닙니다. 현재 질문으로 그래프 DB 조회를 할 수 없습니다. 다른 질문을 하거나 다른 모델 (벡터 DB 혹은 하이브리드 방식)을 이용해주세요."]

    # ✅ 2. Graph 결과가 없거나 부족할 경우 Vector QA 실행
    if graph_answer in graph_failure_msgs:
        vector_answer, sources = run_qa_chain(
            question, k=k, VECTOR_DB_DIR=vector_db_dir, return_sources=True, chat_history=chat_history
        )
        vector_docs_summary = format_vector_titles(sources)
    else:
        vector_answer, sources = "그래프 DB에서 이미 충분한 내용이 검색되었습니다. 벡터DB를 검색하지 않습니다.", []
        vector_docs_summary = ""

    # ✅ 3. System Prompt 정의
    system_template = SystemMessagePromptTemplate.from_template(
        """You are a helpful assistant. The user may ask questions in any language, and you must respond in the same language.

    You are given two optional answers to assist with your response:

    - Answer A (from Graph DB): {graph_answer}
    - Answer B (from Vector DB): {vector_answer}

    You are also given a list of related document titles retrieved from the Vector DB to help assess the relevance of its content:
    {vector_docs_summary}

    ---

    🎯 Your task: Choose the **most relevant, informative, and complete** answer source to respond to the user’s question.

    🔍 Source selection rules:

    1. **Evaluate the Graph DB answer first**:
        - Use it **only if** it contains specific factual information that clearly and directly addresses the user’s question.
        Examples include: citation counts, author names, or explicit citation relationships.
        - **Do not use it** if it contains generic fallback text such as:
            - "현재 구축된 그래프 DB에는 질문한 내용과 일치하는 결과가 없습니다."
            - "관계기반 질문이 아닙니다."

    2. **Then evaluate the Vector DB answer and its context**:
        - Use it **only if**:
            - The vector answer is informative and helpful,
            - AND the related document titles are clearly relevant to the user's question.
        - **Do not use it** if it contains fallback phrases such as:
            - "현재 구축된 벡터 DB에 사용자의 질문을 답하는 데 도움이 되는 내용이 없습니다."
            - "그래프 DB에서 이미 충분한 내용이 검색되었습니다. 벡터DB를 검색하지 않습니다."

    3. **Fallback to your own knowledge**:
        - If **neither** source is informative or relevant, answer using your own general academic knowledge and reasoning.

    ---

    ⚠️ Important Instructions:
    - Never choose a source **just because it exists**.
    - Base your choice on **actual usefulness and content quality**, not mere presence.
    - Be especially cautious with known fallback or template-like responses.

    ✅ At the end of your answer, append exactly one of the following:
    - [Answer Source: Graph DB]
    - [Answer Source: Vector DB]
    - [Answer Source: Own Knowledge]
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
    question = "트랜스포머에 대해 간단히 설명해줘"
    #question = "attention is all you need에 대해 간단히 설명해줘"

    response, _ = hybrid_qa(
        question=question,
        k=3,
        return_sources=False
        )

    print(response)