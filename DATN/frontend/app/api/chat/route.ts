import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'

export const maxDuration = 60
export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  const { messages, pdfContext, pdfName, chatId }: {
    messages: any[]
    pdfContext?: string | null
    pdfName?: string | null
    chatId?: string | null
  } = await req.json()

  console.log('[/api/chat] POST hit, chatId:', chatId, 'messages:', messages.length)

  if (!chatId) {
    return new Response('Missing chatId', { status: 400 })
  }
  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://app-backend:8000'
  const endpoint = `${BACKEND_URL}/api/chats/${chatId}/message`

  // Extract the user message text from the last message
  const lastMessage = messages[messages.length - 1]
  let userContent = ''
  if (typeof lastMessage.content === 'string') {
    userContent = lastMessage.content
  } else if (lastMessage.parts) {
    // AI SDK v6 UIMessage format - extract text from parts
    const textPart = lastMessage.parts.find((p: any) => p.type === 'text')
    userContent = textPart?.text || ''
  }

  console.log('[/api/chat] Sending to backend:', endpoint, 'content:', userContent.substring(0, 50))

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            role: 'user', 
            content: userContent,
            pdfContext: pdfContext || null,
            pdfName: pdfName || null,
            chatId: chatId
          }),
        })

        if (!response.ok) {
          const errorText = await response.text()
          console.error('[/api/chat] Backend error:', errorText)
          writer.write({ type: 'error', errorText: `Agent API error: ${errorText}` })
          return
        }

        const reader = response.body?.getReader()
        if (!reader) {
          writer.write({ type: 'error', errorText: 'No response body from Agent' })
          return
        }

        const decoder = new TextDecoder()
        let buffer = ''
        let textPartId = 'text-0'
        let reasoningPartId = 'reasoning-0'
        let lastType: 'thought' | 'final' | null = null
        let hasStartedText = false
        let hasStartedReasoning = false

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('THOUGHT: ')) {
              if (!hasStartedReasoning) {
                writer.write({ type: 'reasoning-start', id: reasoningPartId })
                hasStartedReasoning = true
              }
              lastType = 'thought'
              const thought = line.replace('THOUGHT: ', '')
              writer.write({
                type: 'reasoning-delta',
                id: reasoningPartId,
                delta: thought + '\n',
              })
            } else if (line.startsWith('FINAL: ')) {
              if (hasStartedReasoning) {
                writer.write({ type: 'reasoning-end', id: reasoningPartId })
                hasStartedReasoning = false
              }
              if (!hasStartedText) {
                writer.write({ type: 'text-start', id: textPartId })
                hasStartedText = true
              }
              lastType = 'final'
              const finalText = line.replace('FINAL: ', '')
              writer.write({
                type: 'text-delta',
                id: textPartId,
                delta: finalText,
              })
            } else if (lastType === 'final') {
              if (!hasStartedText) {
                writer.write({ type: 'text-start', id: textPartId })
                hasStartedText = true
              }
              writer.write({
                type: 'text-delta',
                id: textPartId,
                delta: '\n' + line,
              })
            } else if (lastType === 'thought') {
              if (!hasStartedReasoning) {
                writer.write({ type: 'reasoning-start', id: reasoningPartId })
                hasStartedReasoning = true
              }
              writer.write({
                type: 'reasoning-delta',
                id: reasoningPartId,
                delta: line + '\n',
              })
            }
          }
        }

        // Xử lý dòng còn sót trong buffer khi stream kết thúc
        if (buffer) {
          const line = buffer
          if (line.startsWith('THOUGHT: ')) {
            if (!hasStartedReasoning) {
              writer.write({ type: 'reasoning-start', id: reasoningPartId })
              hasStartedReasoning = true
            }
            const thought = line.replace('THOUGHT: ', '')
            writer.write({
              type: 'reasoning-delta',
              id: reasoningPartId,
              delta: thought + '\n',
            })
          } else if (line.startsWith('FINAL: ')) {
            if (hasStartedReasoning) {
              writer.write({ type: 'reasoning-end', id: reasoningPartId })
              hasStartedReasoning = false
            }
            if (!hasStartedText) {
              writer.write({ type: 'text-start', id: textPartId })
              hasStartedText = true
            }
            lastType = 'final'
            const finalText = line.replace('FINAL: ', '')
            writer.write({
              type: 'text-delta',
              id: textPartId,
              delta: finalText,
            })
          } else if (lastType === 'final') {
            if (!hasStartedText) {
              writer.write({ type: 'text-start', id: textPartId })
              hasStartedText = true
            }
            writer.write({
              type: 'text-delta',
              id: textPartId,
              delta: '\n' + line,
            })
          } else if (lastType === 'thought') {
            if (!hasStartedReasoning) {
              writer.write({ type: 'reasoning-start', id: reasoningPartId })
              hasStartedReasoning = true
            }
            writer.write({
              type: 'reasoning-delta',
              id: reasoningPartId,
              delta: line + '\n',
            })
          }
        }

        // Close any open parts
        if (hasStartedReasoning) {
          writer.write({ type: 'reasoning-end', id: reasoningPartId })
        }
        if (hasStartedText) {
          writer.write({ type: 'text-end', id: textPartId })
        }

        console.log('[/api/chat] Stream completed successfully')

      } catch (error) {
        console.error('[/api/chat] Stream execute error:', error)
        writer.write({ type: 'error', errorText: String(error) })
      }
    },
    onError: (error) => {
      console.error('[/api/chat] UIMessageStream error:', error)
      return String(error)
    },
  })

  return createUIMessageStreamResponse({ stream })
}
