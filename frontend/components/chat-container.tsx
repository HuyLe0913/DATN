'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useChat } from '@ai-sdk/react'
import { ChatHeader } from '@/components/chat-header'
import { ChatSidebar, type ChatSession } from '@/components/chat-sidebar'
import { ChatMessage } from '@/components/chat-message'
import { ChatInput } from '@/components/chat-input'
import { ChatEmptyState } from '@/components/chat-empty-state'
import dynamic from 'next/dynamic'
const PDFViewer = dynamic(() => import('@/components/pdf-viewer').then(mod => mod.PDFViewer), { 
  ssr: false,
  loading: () => <div className="hidden lg:flex w-[500px] bg-muted/20 animate-pulse" />
})
import { PDFUploadModal } from '@/components/pdf-upload-modal'
import { ScrollArea } from '@/components/ui/scroll-area'
import { revokeFileUrl, type PDFFile } from '@/lib/pdf-utils'

export function ChatContainer() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [pdfFile, setPdfFile] = useState<PDFFile | null>(null)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  const { messages, sendMessage, status, setMessages } = useChat({
    body: {
      chatId: currentSessionId,
    }
  })

  const isLoading = status === 'streaming' || status === 'submitted'

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    const viewport = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]')
    if (viewport) {
      requestAnimationFrame(() => {
        viewport.scrollTop = viewport.scrollHeight
      })
    }
  }, [messages])

  // Load sessions from backend on mount
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await fetch('/api/chats')
        if (response.ok) {
          const data = await response.json()
          setSessions(data.map((s: any) => ({
            id: s.id,
            title: s.title,
            created_at: s.created_at,
            createdAt: s.created_at // providing both for safety
          })))
        }
      } catch (err) {
        console.error('Failed to fetch sessions:', err)
      }
    }
    fetchSessions()
  }, [])

  const handleNewChat = useCallback(() => {
    setCurrentSessionId(null)
    setMessages([])
    setPdfFile(null)
    setChatInput('')
  }, [setMessages])

  const handleSelectSession = useCallback(async (id: string) => {
    setCurrentSessionId(id)
    setSidebarOpen(false)
    try {
      const response = await fetch(`/api/chats/${id}`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages.map((m: any) => ({
          id: String(m.id),
          role: m.role,
          content: m.content,
          parts: m.role === 'assistant' ? [{ type: 'text', text: m.content }] : undefined
        })))
      }
    } catch (err) {
      console.error('Failed to load session messages:', err)
    }
  }, [setMessages])

  const handleDeleteSession = useCallback(async (id: string) => {
    try {
      const response = await fetch(`/api/chats/${id}`, { method: 'DELETE' })
      if (response.ok) {
        setSessions(prev => prev.filter(s => s.id !== id))
        if (currentSessionId === id) {
          handleNewChat()
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }, [currentSessionId, handleNewChat])

  // Cleanup PDF URL on unmount
  useEffect(() => {
    return () => {
      if (pdfFile?.url) {
        revokeFileUrl(pdfFile.url)
      }
    }
  }, [pdfFile])

  const handleSendMessage = useCallback(async () => {
    if (!chatInput.trim() || isLoading) return

    let sessionId = currentSessionId
    if (!sessionId) {
      try {
        const res = await fetch('/api/chats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: chatInput.substring(0, 30) || 'New Chat' })
        })
        if (res.ok) {
          const newChat = await res.json()
          sessionId = newChat.id
          setCurrentSessionId(sessionId)
          setSessions(prev => [newChat, ...prev])
        }
      } catch (err) {
        console.error('Failed to create session:', err)
        return
      }
    }

    // Include PDF context in the message if available
    const messageText = pdfFile
      ? `[Analyzing attached PDF: ${pdfFile.name}]\n\n${chatInput}`
      : chatInput

    sendMessage(
      { text: messageText },
      {
        body: {
          pdfContext: pdfFile?.text || null,
          pdfName: pdfFile?.name || null,
          chatId: sessionId,
        },
      }
    )
    setChatInput('')
  }, [chatInput, isLoading, sendMessage, pdfFile, currentSessionId, setSessions])

  const handleSuggestionClick = useCallback(
    async (suggestion: string) => {
      setChatInput(suggestion)
      
      let sessionId = currentSessionId
      if (!sessionId) {
        try {
          const res = await fetch('/api/chats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: suggestion.substring(0, 30) })
          })
          if (res.ok) {
            const newChat = await res.json()
            sessionId = newChat.id
            setCurrentSessionId(sessionId)
            setSessions(prev => [newChat, ...prev])
          }
        } catch (err) {
          console.error('Failed to create session:', err)
          return
        }
      }

      // Auto-submit after setting input
      setTimeout(() => {
        const messageText = pdfFile
          ? `[Analyzing attached PDF: ${pdfFile.name}]\n\n${suggestion}`
          : suggestion

        sendMessage(
          { text: messageText },
          {
            body: {
              pdfContext: pdfFile?.text || null,
              pdfName: pdfFile?.name || null,
              chatId: sessionId,
            },
          }
        )
      }, 100)
    },
    [sendMessage, pdfFile, currentSessionId, setSessions]
  )


  const handleFileUploaded = useCallback((file: PDFFile) => {
    // Revoke old URL if exists
    if (pdfFile?.url) {
      revokeFileUrl(pdfFile.url)
    }
    setPdfFile(file)
  }, [pdfFile])

  const handleClosePDF = useCallback(() => {
    if (pdfFile?.url) {
      revokeFileUrl(pdfFile.url)
    }
    setPdfFile(null)
  }, [pdfFile])

  return (
    <div className="fixed inset-0 flex overflow-hidden bg-background">
      <ChatSidebar
        isOpen={sidebarOpen}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Main Chat Area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <ChatHeader
            onNewChat={handleNewChat}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          />

          <main className="flex flex-1 flex-col overflow-hidden">
            {/* PDF Preview Strip (Mobile) */}
            {pdfFile && (
              <div className="flex items-center gap-3 border-b border-border bg-secondary/30 px-4 py-2 lg:hidden">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/20">
                  <span className="text-xs font-medium text-accent">PDF</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{pdfFile.name}</p>
                  <p className="text-xs text-muted-foreground">{pdfFile.pageCount} pages</p>
                </div>
                <button
                  onClick={handleClosePDF}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <span className="sr-only">Remove PDF</span>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            )}

            {messages.length === 0 ? (
              <ChatEmptyState 
                onSuggestionClick={handleSuggestionClick} 
                hasPdfAttached={!!pdfFile}
              />
            ) : (
              <ScrollArea ref={scrollAreaRef} className="flex-1 min-h-0 overflow-hidden">
                <div className="mx-auto max-w-3xl pb-4">
                  {messages.map((message) => (
                    <ChatMessage key={message.id} message={message} />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
            )}

            <ChatInput
              value={chatInput}
              onChange={setChatInput}
              onSubmit={handleSendMessage}
              isLoading={isLoading}
              onUploadClick={() => setUploadModalOpen(true)}
              hasAttachment={!!pdfFile}
              placeholder={pdfFile ? `Ask about ${pdfFile.name}...` : 'Send a message...'}
            />
          </main>
        </div>

        {/* PDF Viewer Panel (Desktop) */}
        <PDFViewer
          file={pdfFile}
          onClose={handleClosePDF}
          className="hidden lg:flex w-[500px] shrink-0"
        />
      </div>

      {/* Upload Modal */}
      <PDFUploadModal
        open={uploadModalOpen}
        onOpenChange={setUploadModalOpen}
        onFileUploaded={handleFileUploaded}
      />
    </div>
  )
}
