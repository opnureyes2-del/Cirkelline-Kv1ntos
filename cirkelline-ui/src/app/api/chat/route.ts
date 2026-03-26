import { NextResponse } from 'next/server'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

export async function POST(request: Request) {
  try {
    const { message, session_id } = await request.json()
    const authHeader = request.headers.get('authorization') || ''

    const response = await fetch(`${API_URL}/api/terminal/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        message,
        session_id: session_id || undefined,
        include_system_context: true,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { reply: data.detail || data.error || 'Serverfejl', error: data.detail },
        { status: response.status }
      )
    }

    return NextResponse.json({
      reply: data.answer || data.reply || 'Intet svar',
      message_id: data.message_id,
      session_id: data.session_id,
      processing_time_ms: data.processing_time_ms,
    })
  } catch {
    return NextResponse.json(
      { reply: 'Kunne ikke forbinde til backend', error: 'connection_failed' },
      { status: 502 }
    )
  }
}
