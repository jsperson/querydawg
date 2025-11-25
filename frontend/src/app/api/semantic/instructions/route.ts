import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://querydawg-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/semantic/instructions/get`, {
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
  } catch {
    return NextResponse.json(
      { detail: 'Failed to get custom instructions' },
      { status: 500 }
    );
  }
}

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

    const response = await fetch(`${BACKEND_URL}/api/semantic/instructions/set`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: 'Failed to set custom instructions' },
      { status: 500 }
    );
  }
}
