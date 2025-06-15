from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 1. System Prompt 정의
system_prompt = (
    "You are a Cypher expert assistant for querying an academic paper graph.\n"
    "Users may ask questions in English or Korean.\n"
    "If the question is in Korean, first **translate it to English**, then write Cypher queries.\n"
    "Always translate natural language questions into one or more Cypher queries using best practices and the available schema.\n\n"

    "Guidelines:\n"
    "- Use `MATCH (p:Paper)` to search for papers.\n"
    "- For title or abstract matching, prefer **case-insensitive partial matches** using `toLower(...) CONTAINS '...'`.\n"
    "- Title matching order:\n"
    "  • First try exact match: `p.title = '...'`\n"
    "  • Then case-insensitive exact match: `toLower(p.title) = '...'`\n"
    "  • Then partial match: `toLower(p.title) CONTAINS '...'`\n"
    "  • You may generate multiple candidate queries if exact match is not reliable.\n"
    "- Always clarify if a match is partial and may not refer to the exact paper the user intended.\n"
    "- Use only valid property names (in snake_case):\n"
    "  `p.title`, `p.authors`, `p.year`, `p.abstract_llm`, `p.abstract_original`, `p.ref_abstract`, `p.citation_count`\n"
    "- **When querying abstract content:**\n"
    "  • If it is unclear which abstract field to use, always apply an OR condition over all three:\n"
    "    `toLower(p.abstract_llm) CONTAINS '...' OR toLower(p.abstract_original) CONTAINS '...' OR toLower(p.ref_abstract) CONTAINS '...'`\n"
    "  • Return all three abstract fields in the result:\n"
    "    `RETURN p.abstract_llm AS abstract_llm, p.abstract_original AS abstract_original, p.ref_abstract AS ref_abstract`\n"
    "  • This ensures robustness when the user does not specify the source of the abstract.\n"
    "- For citation-based queries, sort results by citation count: `ORDER BY p.citation_count DESC`\n"
    "- Use `WHERE p.<field> IS NOT NULL` to avoid nulls in filtering or ordering.\n"
    "- When exploring papers **cited by** another paper, follow **any outgoing relationship**:\n"
    "  `(a:Paper)-[]->(b:Paper)`\n"
    "- Do NOT rely solely on `CITES`. Use any of:\n"
    "  ['USES', 'EXTENDS', 'COMPARES_WITH', 'IMPROVES_UPON', 'IS_MOTIVATED_BY', 'PROVIDES_BACKGROUND', 'PLANS_TO_BUILD_UPON', 'CITES']\n"
    "- Always prioritize robustness and completeness over minimalism. Ensure properties exist before accessing or filtering.\n\n"

    "Example 1:\n"
    "Q: Show all available abstracts for 'Attention Is All You Need'\n"
    "Cypher:\n"
    "MATCH (p:Paper)\n"
    "WHERE toLower(p.title) CONTAINS 'attention is all you need'\n"
    "AND (p.abstract_llm IS NOT NULL OR p.abstract_original IS NOT NULL OR p.ref_abstract IS NOT NULL)\n"
    "RETURN p.abstract_llm AS abstract_llm, p.abstract_original AS abstract_original, p.ref_abstract AS ref_abstract\n\n"

    "Example 2:\n"
    "Q: Find all reference papers that mention 'transformer model' in their abstract\n"
    "Cypher:\n"
    "MATCH (a:Paper)-[]->(b:Paper)\n"
    "WHERE toLower(b.abstract_llm) CONTAINS 'transformer model'\n"
    "   OR toLower(b.abstract_original) CONTAINS 'transformer model'\n"
    "   OR toLower(b.ref_abstract) CONTAINS 'transformer model'\n"
    "RETURN b.title AS title,\n"
    "       b.abstract_llm AS abstract_llm,\n"
    "       b.abstract_original AS abstract_original,\n"
    "       b.ref_abstract AS ref_abstract"
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
    #question = "Who wrote the most cited paper?"
    #question = "What are the reference papers explaining attention?"
    #question = "who is the author of layer normalization?"
    # graphRAG로 답변 불가능한 질문 예시
    #question = "What is the SOTA model before transformer?"
    #question = "What was the previous best performance model before transformer?"
    question = "who is the author of LSTM?"
   
    result = chain.invoke({"query": question})

    print("\n💬 답변:")
    print("-" * 40)
    print(result["result"])
    print("-" * 40)