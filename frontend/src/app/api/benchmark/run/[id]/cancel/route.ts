import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://querydawg-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const adminPassword = request.headers.get('X-Admin-Password');

    const headers: HeadersInit = {
      'X-API-Key': API_KEY,
    };

    if (adminPassword) {
      headers['X-Admin-Password'] = adminPassword;
    }

    const response = await fetch(
      `${BACKEND_URL}/api/benchmark/run/${params.id}/cancel`,
      {
        method: 'POST',
        headers,
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Benchmark cancel error:', error);
    return NextResponse.json(
      { detail: 'Failed to cancel benchmark' },
      { status: 500 }
    );
  }
}
