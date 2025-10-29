import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://querydawg-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/benchmark/run/${params.id}/status`,
      {
        headers: { 'X-API-Key': API_KEY },
        cache: 'no-store',
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Benchmark status fetch error:', error);
    return NextResponse.json(
      { detail: 'Failed to fetch benchmark status' },
      { status: 500 }
    );
  }
}
