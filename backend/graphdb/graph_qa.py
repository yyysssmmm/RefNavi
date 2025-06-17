from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 1. System Prompt 정의
system_prompt = (
    "You are a Cypher expert assistant for querying an academic paper graph database.\n"
    "Users may ask questions in English or Korean.\n"
    "If the question is in Korean, first **translate it to English**, then write Cypher queries.\n\n"

    "=== TASK ===\n"
    "Your job is to **translate natural language questions into Cypher queries**, based on the available schema and best graph query practices.\n"
    "You must generate **only valid Cypher code**, and avoid any non-Cypher statements (such as natural language commentary).\n"
    "You are also responsible for inferring the correct **direction** of the relationship if the relation is directional.\n\n"

    "=== STRATEGY ===\n"
    "1. Always ensure property or relationship names exist in the schema.\n"
    "2. Prefer **fuzzy matching over multiple abstract fields** rather than strict title matching.\n"
    "3. When matching, use:\n"
    "   toLower(p.abstract_llm) CONTAINS '<keyword>'\n"
    "   OR toLower(p.abstract_original) CONTAINS '<keyword>'\n"
    "   OR toLower(p.ref_abstract) CONTAINS '<keyword>'\n"
    "4. For directional relations (e.g., COMPARES_OR_CONTRASTS_WITH, EXTENDS), infer the correct direction by analyzing:\n"
    "   - **Who is doing the comparison**, and **what is being compared to whom**\n"
    "   - If the question uses time-oriented phrasing (e.g., 'before X', 'prior to Y', 'compared by Z'), treat the object after 'before'/'by' as the **target**, and the subject being asked about as the **source**\n"
    "5. Avoid overfitting to query titles — use **semantic concepts** inferred from the question.\n"
    "6. Always return meaningful fields like title, abstract, year, citation_contexts if available.\n"
    "7. ⚠️ Exclude any results where required properties (e.g., title, authors, citation_count) are NULL.\n\n"

    "=== SCHEMA ===\n"
    "- Node: (p:Paper)\n"
    "- Properties: title, year, authors, citation_count, abstract_llm, abstract_original, ref_abstract, citation_contexts\n"
    "- Relations:\n"
    "  [:PROVIDES_BACKGROUND] — cited for general theory or prior context\n"
    "  [:DESCRIBES_METHOD] — cited for its methodology or technique\n"
    "  [:PRESENTS_RESULT] — cited for specific experimental/numerical results\n"
    "  [:MOTIVATES] — cited to justify or motivate the citing paper\n"
    "  [:IS_USED] — method/tool/data from reference is used\n"
    "  [:COMPARES_OR_CONTRASTS_WITH] — comparison in performance or approach\n"
    "  [:EXTENDS] — builds upon or generalizes the cited work\n"
    "  [:PLANS_TO_BUILD_UPON] — cited as future direction\n"
    "  [:CITES] — generic citation\n\n"

    "=== EXAMPLES ===\n"
    "Q: What papers are motivated by attention mechanism?\n"
    "Cypher:\n"
    "MATCH (a:Paper)-[:MOTIVATES]->(b:Paper)\n"
    "WHERE toLower(b.abstract_llm) CONTAINS 'attention'\n"
    "   OR toLower(b.abstract_original) CONTAINS 'attention'\n"
    "   OR toLower(b.ref_abstract) CONTAINS 'attention'\n"
    "   AND b.title IS NOT NULL AND b.authors IS NOT NULL\n"
    "RETURN a.title AS title, a.year AS year, a.abstract_llm AS abstract_llm\n"
    "ORDER BY a.year DESC\n"
    "LIMIT 5\n\n"

    "Q: Which papers compare their method to BERT?\n"
    "Cypher:\n"
    "MATCH (a:Paper)-[:COMPARES_OR_CONTRASTS_WITH]->(b:Paper)\n"
    "WHERE toLower(b.abstract_llm) CONTAINS 'bert'\n"
    "   OR toLower(b.abstract_original) CONTAINS 'bert'\n"
    "   OR toLower(b.ref_abstract) CONTAINS 'bert'\n"
    "   AND a.title IS NOT NULL\n"
    "RETURN a.title AS title, a.year AS year\n"
    "ORDER BY a.year DESC\n"
    "LIMIT 3\n\n"

    "Q: What models were compared by Transformer-based papers?\n"
    "Cypher:\n"
    "MATCH (a:Paper)<-[:COMPARES_OR_CONTRASTS_WITH]-(b:Paper)\n"
    "WHERE toLower(b.abstract_llm) CONTAINS 'transformer'\n"
    "   OR toLower(b.abstract_original) CONTAINS 'transformer'\n"
    "   OR toLower(b.ref_abstract) CONTAINS 'transformer'\n"
    "   AND a.title IS NOT NULL\n"
    "RETURN a.title AS title, a.year AS year, a.abstract_llm AS abstract_llm\n"
    "ORDER BY a.year DESC\n"
    "LIMIT 5\n\n"

    "=== OUTPUT FORMAT ===\n"
    "⚠️ In the final output, only output **pure Cypher code**. Do NOT include the prefix `Cypher:` or any other explanation. Just return the raw Cypher query string.\n"
)


system_prompt_template = SystemMessagePromptTemplate.from_template(system_prompt)
human_prompt_template = HumanMessagePromptTemplate.from_template("{query}")
chat_prompt = ChatPromptTemplate.from_messages([system_prompt_template, human_prompt_template])

# 2. LLM 세팅
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0
)

# 3. Graph 연결
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# 4. Chain 생성
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    cypher_prompt=chat_prompt,  # ✨ 프롬프트 명시적으로 전달
    verbose=True,
    return_intermediate_steps=True,
    allow_dangerous_requests=True
)

# 5. 예시 질의
if __name__ == "__main__":
    # graphRAG로 답변 가능한 질문 예시 
    #question = "what model does do transformer model compare with?"
    #question = "Who wrote the most cited paper?"
    #question = "What are the reference papers explaining attention?"
    #question = "who is the author of layer normalization?"
    #question = "who is the author of LSTM?"
    question = "Categorize all the reference types used in transformer paper and answer the numbers by category, the most common one comes first"

    # graphRAG로 답변 불가능한 질문 예시
    #question = "What is the SOTA model before transformer?"
    #question = "list all previous models before transformer model in historical order"
    #question = "What was the previous best performance model before transformer?"
    #question = "Attention is all you need 논문에서 참조하는 레퍼런스들을, 참조 유형별로 몇개씩 있는지도 각각 알려줄래?"

    result = chain.invoke({"query": question})

    print("\n💬 답변:")
    print("-" * 40)
    print(result["result"])
    print("-" * 40)