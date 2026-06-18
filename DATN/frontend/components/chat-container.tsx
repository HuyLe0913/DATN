'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Sidebar } from '@/components/sidebar'
import { ChatHeader } from '@/components/chat-header'
import { ChatSidebar, type ChatSession } from '@/components/chat-sidebar'
import { ChatMessage } from '@/components/chat-message'
import { ChatInput } from '@/components/chat-input'
import { ChatEmptyState } from '@/components/chat-empty-state'
import { ScrollArea } from '@/components/ui/scroll-area'
import { revokeFileUrl, type PDFFile, createFileUrl, extractTextFromPDF } from '@/lib/pdf-utils'
import { X } from 'lucide-react'
import { useChat } from '@ai-sdk/react'
import { toast } from 'sonner'
import { v4 as uuidv4 } from 'uuid'

export function ChatContainer() {
  // Use a stable ID for the chat instance until a real session is created
  const [activeId, setActiveId] = useState<string>(uuidv4())
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [pdfFile, setPdfFile] = useState<PDFFile | null>(null)
  const [isSessionLoading, setIsSessionLoading] = useState(false)
  const [localInput, setLocalInput] = useState('')
  const [isCreatingSession, setIsCreatingSession] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const chat = useChat({
    api: '/api/chat',
    // Keep ID stable during a single conversation flow
    id: currentSessionId || activeId,
    initialMessages: [],
    onResponse: (response) => {
      if (!response.ok) {
        toast.error('Failed to get response from agent')
      }
    },
    onFinish: () => {
      fetchSessions()
    }
  })

  const { messages, isLoading, setMessages, stop } = chat

  const fetchSessions = async () => {
    try {
      const res = await fetch('/api/chats')
      if (res.ok) {
        const data = await res.json()
        setSessions(data)
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [])

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const handleNewChat = useCallback(() => {
    setCurrentSessionId(null)
    setActiveId(uuidv4()) // Generate new stable ID for the next conversation
    setMessages([])
    setPdfFile(null)
    setLocalInput('')
    if (window.innerWidth < 768) setSidebarOpen(false)
  }, [setMessages])

  const handleSelectSession = useCallback(async (id: string) => {
    if (id === currentSessionId) return
    
    setIsSessionLoading(true)
    setCurrentSessionId(id)
    setActiveId(id) // Sync stable ID with selected session
    setPdfFile(null)
    setLocalInput('')
    if (window.innerWidth < 768) setSidebarOpen(false)

    try {
      const res = await fetch(`/api/chats/${id}`)
      if (res.ok) {
        const data = await res.json()
        const formattedMessages = data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          parts: m.parts || (m.role === 'assistant' ? [{ type: 'text', text: m.content }] : undefined)
        }))
        setMessages(formattedMessages)
      }
    } catch (err) {
      console.error('Failed to fetch session details:', err)
      toast.error('Could not load chat history')
    } finally {
      setIsSessionLoading(false)
    }
  }, [currentSessionId, setMessages])

  const handleDeleteSession = useCallback(async (id: string) => {
    try {
      const res = await fetch(`/api/chats/${id}`, { method: 'DELETE' })
      if (res.ok) {
        setSessions(prev => prev.filter(s => s.id !== id))
        if (currentSessionId === id) {
          handleNewChat()
        }
        toast.success('Chat deleted')
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
      toast.error('Failed to delete chat')
    }
  }, [currentSessionId, handleNewChat])

  const performSendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return

    let sessionId = currentSessionId
    
    // If it's a new chat, we use the activeId (UUID) and create the session in parallel/background
    if (!sessionId && !isCreatingSession) {
      setIsCreatingSession(true)
      sessionId = activeId // Use the pre-generated UUID as the sessionId for the API call
      
      // Create the session in the background
      fetch('/api/chats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: sessionId, title: text.substring(0, 30) })
      }).then(res => {
        if (res.ok) {
          return res.json()
        }
      }).then(newChat => {
        if (newChat) {
          setCurrentSessionId(newChat.id)
          setSessions(prev => [newChat, ...prev])
        }
      }).catch(err => {
        console.error('Background session creation failed:', err)
      }).finally(() => {
        setIsCreatingSession(false)
      })
    }

    const messageText = pdfFile 
      ? `[Analyzing attached PDF: ${pdfFile.name}]\n\n${text}`
      : text

    const appendFn = (chat as any).append || (chat as any).sendMessage
    
    if (typeof appendFn === 'function') {
      try {
        await appendFn(
          { content: messageText, role: 'user' },
          {
            body: {
              pdfContext: pdfFile?.text || null,
              pdfName: pdfFile?.name || null,
              chatId: sessionId,
            },
          }
        )
      } catch (err) {
        console.error('Failed to append message:', err)
        toast.error('Failed to send message')
      }
    } else {
      toast.error('Chat system is not ready')
    }
  }, [currentSessionId, activeId, isLoading, isCreatingSession, pdfFile, chat])

  const handleSendMessage = async () => {
    const text = localInput
    setLocalInput('')
    await performSendMessage(text)
  }

  const handleSuggestionClick = async (suggestion: string) => {
    await performSendMessage(suggestion)
  }

  const handleFileUploaded = useCallback((file: PDFFile) => {
    if (pdfFile?.url) {
      revokeFileUrl(pdfFile.url)
    }
    setPdfFile(file)
  }, [pdfFile])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file')
      return
    }

    try {
      const url = createFileUrl(file)
      const { text, pageCount } = await extractTextFromPDF(file)
      const pdfData: PDFFile = {
        name: file.name,
        size: file.size,
        url,
        text,
        pageCount
      }
      handleFileUploaded(pdfData)
      toast.success('PDF attached successfully')
    } catch (err) {
      console.error('Failed to process PDF:', err)
      toast.error('Failed to process PDF file')
    }
    
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleClosePDF = useCallback(() => {
    if (pdfFile?.url) {
      revokeFileUrl(pdfFile.url)
    }
    setPdfFile(null)
  }, [pdfFile])

  return (
    <div className="fixed inset-0 flex overflow-hidden bg-background">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="application/pdf"
        className="hidden"
      />
      <ChatSidebar
        isOpen={sidebarOpen}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex flex-1 flex-col overflow-hidden">
          <ChatHeader
            onNewChat={handleNewChat}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          />

          <main className="flex flex-1 flex-col overflow-hidden">
            {pdfFile && (
              <div className="flex items-center gap-3 border-b border-border bg-secondary/20 px-6 py-2 animate-in slide-in-from-top duration-300">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/20">
                  <span className="text-[10px] font-bold text-accent">PDF</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">{pdfFile.name}</p>
                </div>
                <button
                  onClick={handleClosePDF}
                  className="text-muted-foreground hover:text-foreground p-1 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}

            {isSessionLoading ? (
              <div className="flex-1 space-y-4 px-6 py-10 mx-auto w-full max-w-3xl">
                <div className="h-24 bg-muted/40 animate-pulse rounded-2xl w-3/4" />
                <div className="h-24 bg-muted/20 animate-pulse rounded-2xl w-1/2 ml-auto" />
                <div className="h-32 bg-muted/40 animate-pulse rounded-2xl w-2/3" />
              </div>
            ) : messages.length === 0 ? (
              <ChatEmptyState 
                onSuggestionClick={handleSuggestionClick} 
                hasPdfAttached={!!pdfFile}
              />
            ) : (
              <ScrollArea className="flex-1 min-h-0 overflow-hidden">
                <div className="mx-auto max-w-3xl pb-10">
                  {messages.map((message) => (
                    <ChatMessage 
                      key={message.id} 
                      message={message} 
                      isLoading={isLoading && message.id === messages[messages.length - 1].id}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
            )}

            <ChatInput
              value={localInput}
              onChange={setLocalInput}
              onSubmit={handleSendMessage}
              isLoading={isLoading}
              onUploadClick={() => fileInputRef.current?.click()}
              hasAttachment={!!pdfFile}
              onStop={stop}
              placeholder={pdfFile ? `Ask about ${pdfFile.name}...` : 'Send a message...'}
            />
          </main>
        </div>
      </div>
    </div>
  )
}
