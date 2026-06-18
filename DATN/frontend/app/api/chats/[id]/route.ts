import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://app-backend:8000'

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const response = await fetch(`${BACKEND_URL}/api/chats/${id}`)
    if (!response.ok) {
      return NextResponse.json({ error: 'Chat not found' }, { status: 404 })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Fetch chat error:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const response = await fetch(`${BACKEND_URL}/api/chats/${id}`, {
      method: 'DELETE'
    })
    if (!response.ok) {
      return NextResponse.json({ error: 'Failed to delete chat' }, { status: response.status })
    }
    return new Response(null, { status: 204 })
  } catch (error) {
    console.error('Delete chat error:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}
