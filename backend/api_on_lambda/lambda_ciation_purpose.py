import os
import json
import requests

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        citation_number = body['citation_number']
        local_context = body['local_context']
        exact_citation_sentence = body['exact_citation_sentence']
        all_contexts = body['all_contexts']
        abstract = body['abstract']
        full_text = body['full_text']
        ref_title = body['ref_title']

        api_key = os.environ["PERPLEXITY_API_KEY"]

        prompt = f"""당신은 학술 논문 분석 전문가입니다. 다음 정보를 바탕으로 인용의 목적을 간단명료하게 분석해주세요.

인용 정보:
- 인용된 논문 제목: {ref_title}
- 정확한 인용 문장: {exact_citation_sentence}
- 인용 문장의 문맥 (앞뒤 문장): {json.dumps(local_context, ensure_ascii=False)}
- 인용된 논문의 쓰인 다른 문장들: {json.dumps(all_contexts, ensure_ascii=False)}
- 인용된 논문의 초록: {abstract}

다음 두 가지에 초점을 맞춰 1~2가지 이유로 분석해 주세요:
1. 인용 문장에서 어떤 목적(예: 근거 제시, 방법 인용, 배경 설명 등)으로 이 논문이 쓰였는가?
2. 인용 논문의 어떤 구체적 내용이 그 목적에 활용되었는가?

분석은 다음 형식으로 작성해주세요:
[인용 목적] 해당 문장에서 이 인용이 사용된 이유를 1~2문장으로 설명해주세요.
[참조 내용] 인용된 논문의 어떤 개념, 방법, 결과 또는 주장이 문장에 연결되는지를 3~4문장으로 설명해주세요.

분석은 학술적 중요성에 초점을 맞추되, 반드시 간결하게 작성해주세요."""

        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            },
            timeout=30
        )

        if response.status_code != 200:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Perplexity API error", "detail": response.text})
            }

        result = response.json()
        purpose = result["choices"][0]["message"]["content"]

        return {
            "statusCode": 200,
            "body": json.dumps({"purpose": purpose})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }