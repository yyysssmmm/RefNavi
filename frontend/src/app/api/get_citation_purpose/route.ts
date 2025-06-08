import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { citation_number, local_context, all_contexts, abstract, full_text } = body;

    // 백엔드 API로 요청 전달
    const response = await fetch('http://localhost:8000/get_citation_purpose', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        citation_number,
        local_context,
        all_contexts,
        abstract,
        full_text
      }),
    });

    if (!response.ok) {
      throw new Error('Backend API request failed');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in citation purpose API:', error);
    return NextResponse.json(
      { error: 'Failed to get citation purpose' },
      { status: 500 }
    );
  }
} 