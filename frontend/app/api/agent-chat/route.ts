// This route is deprecated. Use /api/agent-v3 instead.
export async function POST() {
  return new Response(JSON.stringify({ error: 'Deprecated. Use /api/agent-v3' }), {
    status: 410,
    headers: { 'Content-Type': 'application/json' },
  })
}
