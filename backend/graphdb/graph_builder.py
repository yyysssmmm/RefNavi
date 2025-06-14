from neo4j import GraphDatabase
import json
from pathlib import Path
import re
import os

from dotenv import load_dotenv

load_dotenv()

class GraphBuilder:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def insert_triples_with_metadata(self, metadata):
        title = metadata.get("title", "")
        abstract_orig = metadata.get("abstract_original", "")
        abstract_llm = metadata.get("abstract_llm", "")
        references = metadata.get("references", [])
        triples = metadata.get("triples", [])

        # reference 딕셔너리 생성
        ref_map = {ref["ref_title"]: ref for ref in references}

        with self.driver.session() as session:
            for i, (src, rel, tgt) in enumerate(triples):
                print(f"[{i+1:03}] Inserting triple:")
                print(f"     🔹 Source : {src}")
                print(f"     🔸 Relation : {rel}")
                print(f"     🔹 Target : {tgt}\n")

                # 대상 논문의 메타데이터 추출
                clean_tgt_title = re.sub(r"^\[\d+\]\s*", "", tgt)
                ref_info = ref_map.get(clean_tgt_title, {})

                ref_abstract = ref_info.get("abstract", "")
                ref_authors = ref_info.get("authors", "")

                # 연도와 인용수는 정수형으로 변환 시도
                try:
                    ref_year = int(ref_info.get("year", 0))
                except (ValueError, TypeError):
                    ref_year = 0

                try:
                    ref_citations = int(ref_info.get("citation_count", 0))
                except (ValueError, TypeError):
                    ref_citations = 0

                session.run(f"""
                    MERGE (a:Paper {{title: $src}})
                    SET a.abstract_original = $abstract_orig,
                        a.abstract_llm = $abstract_llm

                    MERGE (b:Paper {{title: $tgt}})
                    SET b.ref_abstract = $ref_abstract,
                        b.authors = $ref_authors,
                        b.year = $ref_year,
                        b.citation_count = $ref_citations

                    MERGE (a)-[:{rel.replace(" ", "_").upper()}]->(b)
                """, {
                    "src": src,
                    "tgt": tgt,
                    "abstract_orig": abstract_orig,
                    "abstract_llm": abstract_llm,
                    "ref_abstract": ref_abstract,
                    "ref_authors": ref_authors,
                    "ref_year": ref_year,
                    "ref_citations": ref_citations
                })


def insert_triples_to_graph(enriched_metadata_path: str):
    with open(enriched_metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"\n📦 총 triple 수: {len(metadata.get('triples', []))}\n")

    graph = GraphBuilder(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD")
    )
    graph.insert_triples_with_metadata(metadata)
    graph.close()

    print("✅ GraphDB triple 삽입 완료")


# 실행 예시
if __name__ == "__main__":
    enriched_path = Path(__file__).resolve().parent.parent / "utils/metadata/enriched_metadata.json"
    print(f"\n📂 Enriched metadata path: {enriched_path}")

    insert_triples_to_graph(str(enriched_path))
