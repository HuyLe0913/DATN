'use client'

import { Bot, Copy, Check, User, Loader2, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { UIMessage } from 'ai'

interface ChatMessageProps {
  message: UIMessage
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const getMessageText = () => {
    if (message.content) return message.content
    if (!message.parts || !Array.isArray(message.parts)) return ''
    return message.parts
      .filter((p): p is { type: 'text'; text: string } => p.type === 'text')
      .map((p) => p.text)
      .join('')
  }

  const text = getMessageText()

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      className={cn(
        'group flex gap-4 px-4 py-6',
        isUser ? 'bg-transparent' : 'bg-card/50'
      )}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
          isUser ? 'bg-secondary' : 'bg-primary'
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-secondary-foreground" />
        ) : (
          <Bot className="h-4 w-4 text-primary-foreground" />
        )}
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">
            {isUser ? 'You' : 'AI Agent'}
          </span>
        </div>

        <div className="prose prose-invert max-w-none text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
          {message.parts?.map((part, index) => {
            if (part.type === 'reasoning') {
              const isDone = message.parts!.slice(index + 1).some(p => p.type === 'text' || p.type === 'tool-invocation')
              return (
                <div key={index} className="mb-4 overflow-hidden rounded-lg border border-border bg-muted/20">
                  <details open={!isDone} className="group">
                    <summary className="flex cursor-pointer items-center gap-2 p-2 text-xs font-medium text-muted-foreground/70 hover:bg-muted/40 transition-colors">
                      {isDone ? (
                        <Check className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <Loader2 className="h-3 w-3 animate-spin text-primary" />
                      )}
                      <span>{isDone ? 'Thought process' : 'Thinking...'}</span>
                      <div className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
                        <ChevronDown className="h-3 w-3 transition-transform group-open:rotate-180" />
                      </div>
                    </summary>
                    <div className="border-t border-border/50 p-3 text-xs italic text-muted-foreground/60 bg-muted/5">
                      {part.text}
                    </div>
                  </details>
                </div>
              )
            }
            if (part.type === 'text') {
              return (
                <div key={index} className="mb-2 last:mb-0">
                  {part.text}
                </div>
              )
            }
            return null
          })}
          {message.content && !message.parts?.some(p => p.type === 'text') && (
            <div className="mb-2 last:mb-0">{message.content}</div>
          )}
        </div>

        {!isUser && text && (
          <div className="mt-2 flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  Copy
                </>
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
