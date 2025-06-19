from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts.chat import (
    ChatPromptTemplate, 
    SystemMessagePromptTemplate, 
    HumanMessagePromptTemplate
)
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 1. System Prompt 정의
system_prompt = (
    """You are a Cypher expert assistant for querying an academic paper graph database.

=== TASK ===
Your job is to **translate natural language questions into Cypher queries**, based on the available schema and best practices.
You must generate **only valid Cypher code** and avoid any non-Cypher statements (such as natural language commentary).
You are also responsible for inferring the correct **directionality** of relationships when applicable.

You must **NOT include the user's question, translation, or any explanation** in the output.  
Just output the Cypher query directly.

=== STRATEGY ===
1. Always ensure that property or relationship names exist in the schema.

2. 🧭 First determine which paper is the **citing paper** and which is the **cited paper**.
   - The **citing paper** is the one doing the referencing — typically the uploaded paper or the main subject of the user's question.
   - The **cited paper** is the one being referenced — typically the reference in question.

   Use chat history and the phrasing of the current question to decide:
   - If the user previously uploaded a paper, treat it as the **citing paper**.
   - If the question refers to "this paper", "the uploaded paper", or no specific title, assume it refers to the **citing paper**.
   - If the question refers to a named paper (e.g., "What does Transformer compare itself to?"), that paper is likely the **citing paper**.

3. Once citing and cited roles are determined, apply **case-insensitive fuzzy matching** to the appropriate fields:

   For the **citing paper**, match over:
   - `toLower(p.abstract_llm)`
   - `toLower(p.abstract_original)`
   - `toLower(p.title)`

   For the **cited paper**, match over:
   - `toLower(p.ref_abstract)`
   - `toLower(p.title)`

   Use `OR` to combine all fields into a single robust match condition.  
   ❗Avoid using exact title match unless explicitly instructed.

4. For directional relationships (e.g., COMPARES_OR_CONTRASTS_WITH, HAS_BACKGROUND_ON, EXTENDS_IDEA_OF), infer direction based on:
   - Who is making the claim or comparison
   - Time-based phrasing (e.g., "before X" → X is the **cited**, the other is the **citing**)

5. Always return meaningful fields: `title`, `abstract`, `year`, and `citation_contexts` if available.

6. ⚠️ Exclude any results where essential properties (e.g., title, authors, citation_count) are NULL.

7. ⚠️ Do **not** use `LIMIT` unless the user explicitly requests a specific number of results or says "top-k".

8. Do not include any natural language instructions, questions, or summaries in your output — return only the valid Cypher query.


=== SCHEMA ===
- Node: (p:Paper)
- Relationships:
  All citation relationships follow this directional structure (be aware of edge direction):
  **(a:Paper)-[:RELATION]->(b:Paper)**
  where:
    - `a` is the **citing paper** (uploaded paper)
    - `b` is the **cited paper** (reference paper)

  Available relationships:
  (a)-[:HAS_BACKGROUND_ON]->(b): b provides background for a.
  (a)-[:USE_METHOD_OF]->(b): a uses or adapts a method, dataset, or technique from b.
  (a)-[:IS_MOTIVATED_BY]->(b): a is motivated or inspired by b.
  (a)-[:COMPARES_OR_CONTRASTS_WITH]->(b): a compares or contrasts itself with b.
  (a)-[:EXTENDS_IDEA_OF]->(b): a extends, generalizes, or builds upon an idea from b.

  Properties:
    - Citing paper (`a`): `title`, `abstract_llm`, `abstract_original`
    - Cited paper (`b`): `title`, `year`, `authors`, `citation_count`, `ref_abstract`, `citation_contexts`

=== EXAMPLES ===
❗️Avoid using `title` for keyword matching. Use abstract-based fuzzy matching instead.

❌ Bad example:
MATCH (p:Paper)
WHERE toLower(p.title) ='transformer'
RETURN p.title

✅ Good example:
MATCH (a:Paper)-[]->(b:Paper)
WHERE toLower(a.abstract_llm) CONTAINS 'transformer'
OR toLower(a.abstract_original) CONTAINS 'transformer'
OR toLower(b.ref_abstract) CONTAINS 'transformer'
RETURN b.title, b.year, b.citation_count

=== OUTPUT FORMAT ===
⚠️ Your output MUST be **only valid Cypher code** — no explanation, no natural language, no comments, and no user question included.

❌ Examples of forbidden output:
- “Translate: ...” → ❌
- “Here is the query:” → ❌
- `Cypher:` → ❌

✅ Just output **pure Cypher code**, starting directly from:
MATCH ...
RETURN ...

🛑 Even a single extra line (e.g., user's question or explanation) will invalidate the output.
"""
)

llm = ChatOpenAI(model="gpt-4", temperature=0)

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)


# ✅ 4. 실행 함수 정의
def run_graph_rag_qa(query: str, chat_history: list = []) -> str:
    """
    chat_history를 반영한 Cypher 프롬프트 생성 + Graph QA 실행
    """

    try:
        # 1. system message
        system_prompt_template = SystemMessagePromptTemplate.from_template(system_prompt)

        # 2. 히스토리 반영 및 최종 프롬프트 구성
        human_prompt_template = HumanMessagePromptTemplate.from_template("{query}")
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_prompt_template] + chat_history + [human_prompt_template]
        )

        # 3. chain 생성 및 실행
        graph_chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            cypher_prompt=chat_prompt,
            verbose=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True
        )

        result = graph_chain.invoke({"query": query})

        # 4. Cypher 결과 확인
        intermediate = result.get("intermediate_steps", [])
        context_docs = intermediate[1].get("context", []) if len(intermediate) > 1 else []

        print("✅ context_docs:", context_docs)

        if not context_docs:
            return "현재 구축된 그래프 DB에는 질문한 내용과 일치하는 결과가 없습니다. 다른 질문을 하거나 다른 모델 (벡터 DB 혹은 하이브리드 방식)을 이용해주세요."

        return result.get("result", "").strip()

    except Exception as e:
        print("❌ 에러 발생:", e)
        return "관계기반 질문이 아닙니다. 현재 질문으로 그래프 DB 조회를 할 수 없습니다. 다른 질문을 하거나 다른 모델 (벡터 DB 혹은 하이브리드 방식)을 이용해주세요."

    
# 5. 예시 질의
if __name__ == "__main__":
    # graphRAG로 답변 가능한 질문 예시 
    #question = "Attention is all you need 논문에서 참조하는 레퍼런스들을, 참조 유형별로 몇개씩 있는지도 각각 알려줄래?"
    
    #question = "what model does do transformer model compare with?"
    #question = "Who wrote the most cited paper?"
    #question = "What are the reference papers explaining attention?"
    #question = "who is the author of layer normalization?"
    #question = "who is the author of LSTM?"
    #question = "Categorize all the reference types used in transformer paper and answer the numbers by category, the most common one comes first"
    #question = "Reply all the techniques used in the transformer paper. I want to study those."
    #question = "What is the SOTA model before transformer?"
    #question = "hello"
    question = "transformer 논문에 대해 설명해줘"

    # graphRAG로 답변 불가능한 질문 예시
    #question = "Attention is all you need의 배경이 되었던 모델에 대해서 과거 순으로 알려줘"
    
    question = "list all previous models before transformer model in historical order"
    #question = "What was the previous best performance model before transformer?"


    result = run_graph_rag_qa(question, [])

    print("\n💬 답변:")
    print("-" * 40)
    print(result)
    print("-" * 40)