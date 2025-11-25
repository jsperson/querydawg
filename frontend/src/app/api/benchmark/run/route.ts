import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://querydawg-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const adminPassword = request.headers.get('X-Admin-Password');

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    };

    if (adminPassword) {
      headers['X-Admin-Password'] = adminPassword;
    }

    const response = await fetch(`${BACKEND_URL}/api/benchmark/run`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Benchmark start error:', error);
    return NextResponse.json(
      { detail: 'Failed to start benchmark' },
      { status: 500 }
    );
  }
}
