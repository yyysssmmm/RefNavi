# 📁 RefNavi/backend/graphdb/neo4j_loader.py

from py2neo import Graph, Node, Relationship
import json
import os

# Neo4j 연결 설정 (비밀번호는 최초 로그인 후 변경된 값 사용)
NEO4J_URL = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_password"  # 여기를 실제 비밀번호로 수정!

graph = Graph(NEO4J_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def add_paper_to_graph(paper_data: dict):
    paper_node = Node(
        "Paper",
        title=paper_data.get("title"),
        year=paper_data.get("year"),
        doi=paper_data.get("doi"),
        abstract=paper_data.get("abstract"),
        citation_count=paper_data.get("citation_count", 0),
    )
    graph.merge(paper_node, "Paper", "title")

    for author_name in paper_data.get("authors", []):
        author_node = Node("Author", name=author_name)
        graph.merge(author_node, "Author", "name")
        graph.merge(Relationship(author_node, "WROTE", paper_node))


def load_metadata_and_insert(jsonl_path: str):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                add_paper_to_graph(data)
            except json.JSONDecodeError:
                continue

# ✅ 테스트용 실행 코드
if __name__ == "__main__":
    jsonl_path = os.path.join(os.path.dirname(__file__), "../utils/openalex_metadata.jsonl")
    load_metadata_and_insert(jsonl_path)
    print("✅ 그래프 DB에 논문 메타데이터 삽입 완료")
