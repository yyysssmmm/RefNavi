from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.api.types import EmbeddingFunction
import warnings

# ✅ 경고 무시 (의존성 관련)
warnings.filterwarnings("ignore", category=UserWarning)

# ✅ 1. HuggingFace 임베딩 클래스 정의 (Chroma 인터페이스 맞춤)
class HuggingFaceEmbedding(EmbeddingFunction):
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input):  # ❗ 반드시 'input'이라는 파라미터명이어야 함
        return self.model.encode(input).tolist()

# ✅ 2. 임베딩 함수 인스턴스 생성
embedding_func = HuggingFaceEmbedding()

# ✅ 3. Chroma DB 초기화 및 컬렉션 생성
client = chromadb.Client()
collection = client.get_or_create_collection(
    name="refnavi_abstracts",
    embedding_function=embedding_func
)

# ✅ 4. Abstract 추가 함수
def add_abstract(title: str, abstract: str, id: str):
    if not abstract:
        print(f"⚠️ Abstract 없음, 저장 생략: {title}")
        return
    try:
        collection.add(
            documents=[abstract],
            ids=[id],
            metadatas=[{"title": title}]
        )
        print(f"✅ 저장 완료: {title}")
    except Exception as e:
        print(f"❌ 저장 실패: {title} | {e}")

# ✅ 5. 테스트 실행
if __name__ == "__main__":
    sample_title = "Attention Is All You Need"
    sample_abs = (
        "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks..."
    )

    print("🧪 벡터 DB 테스트 중...")
    add_abstract(sample_title, sample_abs, id="test1")

    results = collection.get()
    print(f"📦 저장된 문서 개수: {len(results['ids'])}")
    print("📄 첫 문서 제목:", results["metadatas"][0]["title"])
    print("🧠 임베딩 벡터 길이:", len(embedding_func(results["documents"])[0]))
