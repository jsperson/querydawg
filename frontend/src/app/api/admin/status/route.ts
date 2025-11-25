import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://querydawg-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/admin/status`, {
      headers: {
        'X-API-Key': API_KEY,
      },
    });

    if (!response.ok) {
      return NextResponse.json({ admin_required: false });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ admin_required: false });
  }
}
