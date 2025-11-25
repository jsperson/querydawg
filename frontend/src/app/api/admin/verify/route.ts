import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://querydawg-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function POST(request: NextRequest) {
  try {
    const adminPassword = request.headers.get('X-Admin-Password');

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    };

    if (adminPassword) {
      headers['X-Admin-Password'] = adminPassword;
    }

    const response = await fetch(`${BACKEND_URL}/api/admin/verify`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Invalid password' }));
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: 'Failed to verify admin password' },
      { status: 500 }
    );
  }
}
