'use client'

import { MessageSquare, Trash2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

export interface ChatSession {
  id: string
  title: string
  createdAt?: Date | string
  created_at?: Date | string
}

interface ChatSidebarProps {
  isOpen: boolean
  sessions: ChatSession[]
  currentSessionId: string | null
  onSelectSession: (id: string) => void
  onDeleteSession: (id: string) => void
  onClose: () => void
}

export function ChatSidebar({
  isOpen,
  sessions,
  currentSessionId,
  onSelectSession,
  onDeleteSession,
  onClose,
}: ChatSidebarProps) {
  const formatDate = (dateInput: Date | string | undefined) => {
    if (!dateInput) return 'Unknown'
    const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput
    if (isNaN(date.getTime())) return 'Invalid Date'
    
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    return date.toLocaleDateString()
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 flex h-full max-h-screen w-72 flex-col overflow-hidden border-r border-border bg-sidebar transition-transform duration-300 md:relative md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-sidebar-border px-4">
          <h2 className="text-sm font-semibold text-sidebar-foreground">
            Chat History
          </h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-sidebar-foreground/70 hover:text-sidebar-foreground md:hidden"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <ScrollArea className="flex-1 min-h-0 p-2">
          {sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <MessageSquare className="mb-3 h-10 w-10 text-sidebar-foreground/30" />
              <p className="text-sm text-sidebar-foreground/50">
                No conversations yet
              </p>
              <p className="mt-1 text-xs text-sidebar-foreground/40">
                Start a new chat to begin
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={cn(
                    'group relative flex cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]',
                    currentSessionId === session.id
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground shadow-sm'
                      : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground'
                  )}
                  onClick={() => onSelectSession(session.id)}
                >
                  {currentSessionId === session.id && (
                    <div className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-accent" />
                  )}
                  <div className="flex min-w-0 flex-1 flex-col ml-1">
                    <span className="truncate text-sm font-medium">
                      {session.title}
                    </span>
                    <span className="text-xs text-sidebar-foreground/50 group-hover:text-sidebar-foreground/70 transition-colors">
                      {formatDate(session.createdAt || (session as any).created_at)}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteSession(session.id)
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                    <span className="sr-only">Delete chat</span>
                  </Button>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </aside>
    </>
  )
}
