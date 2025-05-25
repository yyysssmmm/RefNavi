from dotenv import load_dotenv
import os

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
semantic_url = os.getenv("SEMANTIC_SCHOLAR_ENDPOINT")

print("✅ OpenAI Key:", openai_key[:8] + "..." if openai_key else "❌ 없음")
print("✅ Semantic Scholar Endpoint:", semantic_url)
