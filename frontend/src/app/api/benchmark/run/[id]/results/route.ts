import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://querydawg-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    // Pass through query parameters
    const { searchParams } = new URL(request.url);
    const queryString = searchParams.toString();

    const url = queryString
      ? `${BACKEND_URL}/api/benchmark/run/${params.id}/results?${queryString}`
      : `${BACKEND_URL}/api/benchmark/run/${params.id}/results`;

    const response = await fetch(url, {
      headers: { 'X-API-Key': API_KEY },
      cache: 'no-store',
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Benchmark results fetch error:', error);
    return NextResponse.json(
      { detail: 'Failed to fetch benchmark results' },
      { status: 500 }
    );
  }
}
