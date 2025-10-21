import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://dataprism-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/databases`, {
      headers: {
        'X-API-Key': API_KEY,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (_error) {
    return NextResponse.json(
      { detail: 'Failed to fetch databases' },
      { status: 500 }
    );
  }
}
