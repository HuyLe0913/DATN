import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://app-backend:8000'

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chats`, {
      cache: 'no-store'
    })
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Fetch chats error:', error)
    return NextResponse.json([], { status: 500 })
  }
}

export async function POST(req: Request) {
  console.log('POST /api/chats hit')
  try {
    const body = await req.json()
    console.log('Request body:', body)
    const response = await fetch(`${BACKEND_URL}/api/chats`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Create chat error:', error)
    return NextResponse.json({ error: 'Failed to create chat' }, { status: 500 })
  }
}
