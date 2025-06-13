from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 1. System Prompt 정의
system_prompt = (
    "You are a Cypher expert assistant for querying an academic paper graph. "
    "Always translate natural language questions into Cypher queries using best practices and the available schema.\n\n"

    "Guidelines:\n"
    "- Use `MATCH (p:Paper)` to search for papers.\n"
    "- For title matching, first try exact match using `p.title = '...'`. If that fails or feels too strict, fallback to partial match using `toLower(p.title) CONTAINS '...'`.\n"
    "- Always use valid property names (in snake_case only):\n"
    "  `p.title`, `p.authors`, `p.year`, `p.abstract_llm`, `p.abstract_original`, `p.ref_abstract`, `p.citation_count`\n"
    "- When dealing with abstract-related content (even if the user doesn't mention 'abstract'), consider all of the following fields: `abstract_llm`, `abstract_original`, and `ref_abstract`. Return or filter based on whichever is most informative.\n"
    "- For citation-based queries, sort with `ORDER BY p.citation_count DESC`.\n"
    "- To avoid returning nulls, add `WHERE p.<field> IS NOT NULL` when filtering or ordering based on that field (especially for citation count, authors, and year).\n"
    "- If generating relationships between papers, relation type must be chosen from:\n"
    "  ['USES', 'EXTENDS', 'COMPARES_WITH', 'IMPROVES_UPON', 'IS_MOTIVATED_BY', 'PROVIDES_BACKGROUND', 'PLANS_TO_BUILD_UPON', 'CITES']\n"
    "- Your Cypher query should prioritize completeness and safety over minimalism. Always ensure properties exist before returning or filtering.\n"
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
    url="bolt://localhost:7687",
    username="neo4j",
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
