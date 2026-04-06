import { NextResponse } from 'next/server'

const COSMIC_URL = process.env.COSMIC_API_URL || 'http://localhost:7778'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  try {
    const response = await fetch(`${COSMIC_URL}/api/training-rooms/${id}`, {
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Room ikke fundet', id },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Cosmic API utilgængelig' },
      { status: 502 }
    )
  }
}
