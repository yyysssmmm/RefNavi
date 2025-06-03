// query.ts
export async function sendQuery(query: string, top_k: number = 3) {
  const response = await fetch("http://localhost:8000/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`❌ 서버 응답 실패: ${err}`);
  }

  return response.json();  // { answer: string, sources: [...] }
}
