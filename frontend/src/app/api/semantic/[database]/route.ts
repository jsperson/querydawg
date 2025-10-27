import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://querydawg-production.up.railway.app';
const API_KEY = process.env.BACKEND_API_KEY || '';

export async function GET(
  request: NextRequest,
  { params }: { params: { database: string } }
) {
  try {
    const { database } = params;
    const { searchParams } = new URL(request.url);
    const version = searchParams.get('version');

    const url = version
      ? `${BACKEND_URL}/api/semantic/${database}?version=${version}`
      : `${BACKEND_URL}/api/semantic/${database}`;

    const response = await fetch(url, {
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
      { detail: 'Failed to get semantic layer' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { database: string } }
) {
  try {
    const { database } = params;
    const { searchParams } = new URL(request.url);
    const connectionName = searchParams.get('connection_name') || 'Supabase';

    const response = await fetch(`${BACKEND_URL}/api/semantic/${database}?connection_name=${connectionName}`, {
      method: 'DELETE',
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
      { detail: 'Failed to delete semantic layer' },
      { status: 500 }
    );
  }
}
