import { NextResponse } from 'next/server'

const COSMIC_URL = process.env.COSMIC_API_URL || 'http://localhost:7778'

export async function GET() {
  try {
    const response = await fetch(`${COSMIC_URL}/api/training-rooms`, {
      headers: { 'Content-Type': 'application/json' },
      next: { revalidate: 30 },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Cosmic API fejl', status: response.status },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Cosmic API utilgængelig', rooms: [] },
      { status: 502 }
    )
  }
}
