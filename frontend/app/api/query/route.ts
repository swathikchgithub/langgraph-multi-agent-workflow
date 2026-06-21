import { NextRequest, NextResponse } from 'next/server';

export const maxDuration = 60;

export async function POST(req: NextRequest) {
  const apiUrl = process.env.API_URL;
  if (!apiUrl) {
    return NextResponse.json({ error: 'API_URL not configured' }, { status: 500 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${apiUrl}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ error: 'Failed to reach workflow API' }, { status: 502 });
  }
}
