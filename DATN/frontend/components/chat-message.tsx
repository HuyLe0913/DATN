'use client'

import { Bot, Copy, Check, User, Loader2, ChevronDown, BarChart3 } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { UIMessage } from 'ai'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ChartRenderer } from '@/components/chart-renderer'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

interface ChatMessageProps {
  message: UIMessage
  isLoading?: boolean
}

export function ChatMessage({ message, isLoading }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const [isReasoningOpen, setIsReasoningOpen] = useState(true)
  const isUser = message.role === 'user'

  const getFullText = () => {
    if (message.content) return message.content
    if (!message.parts || !Array.isArray(message.parts)) return ''
    return message.parts
      .filter((p): p is { type: 'text'; text: string } => p.type === 'text')
      .map((p) => p.text)
      .join('')
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(getFullText())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const renderContent = () => {
    if (message.parts && message.parts.length > 0) {
      return message.parts.map((part, index) => {
        if (part.type === 'reasoning') {
          // Check if there is subsequent text to determine if thinking is "done"
          const hasFollowUp = message.parts!.slice(index + 1).some(p => p.type === 'text' || p.type === 'tool-invocation')
          const isStreaming = isLoading && index === message.parts!.length - 1
          
          return (
            <Collapsible
              key={`reasoning-${index}`}
              defaultOpen={true}
              className="mb-6 w-full"
            >
              <div className="rounded-2xl border border-border/40 bg-muted/10 overflow-hidden backdrop-blur-sm">
                <CollapsibleTrigger asChild>
                  <button className="flex w-full items-center gap-3 p-3 text-xs font-medium text-muted-foreground/80 hover:bg-muted/20 transition-all group/trigger">
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-muted/30">
                      {hasFollowUp ? (
                        <Check className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <Loader2 className="h-3 w-3 animate-spin text-accent" />
                      )}
                    </div>
                    <span className="flex-1 text-left">
                      {hasFollowUp ? 'Analysis Complete' : 'Thinking Process...'}
                    </span>
                    <ChevronDown className="h-4 w-4 transition-transform duration-300" />
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="border-t border-border/20 p-4 text-xs italic text-muted-foreground/70 bg-muted/5 leading-relaxed whitespace-pre-wrap">
                    {part.text || (isStreaming ? '...' : '')}
                  </div>
                </CollapsibleContent>
              </div>
            </Collapsible>
          )
        }
        if (part.type === 'text') {
          return (
            <div key={`text-${index}`} className="message-content animate-in fade-in slide-in-from-top-1 duration-500">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, className, children, ...props }) {
                    const match = /language-(\w+):(\w+)/.exec(className || '')
                    const isChart = match && match[1] === 'json' && match[2] === 'chart'
                    
                    if (isChart) {
                      return <ChartRenderer chartData={String(children).replace(/\n$/, '')} />
                    }

                    return (
                      <code className={cn("bg-muted px-1.5 py-0.5 rounded text-accent-foreground font-mono text-xs", className)} {...props}>
                        {children}
                      </code>
                    )
                  },
                  table({ children }) {
                    return (
                      <div className="my-6 overflow-x-auto rounded-xl border border-border/50 shadow-sm">
                        <table className="w-full border-collapse text-xs">
                          {children}
                        </table>
                      </div>
                    )
                  },
                  thead({ children }) {
                    return <thead className="bg-muted/50 text-muted-foreground">{children}</thead>
                  },
                  th({ children }) {
                    return <th className="border-b border-border/50 px-4 py-3 text-left font-semibold">{children}</th>
                  },
                  td({ children }) {
                    return <td className="border-b border-border/20 px-4 py-3 align-top">{children}</td>
                  },
                  p({ children }) {
                    return <p className="mb-4 last:mb-0 leading-7">{children}</p>
                  },
                  ul({ children }) {
                    return <ul className="mb-4 ml-6 list-disc space-y-2">{children}</ul>
                  },
                  ol({ children }) {
                    return <ol className="mb-4 ml-6 list-decimal space-y-2">{children}</ol>
                  }
                }}
              >
                {part.text}
              </ReactMarkdown>
            </div>
          )
        }
        return null
      })
    }

    if (message.content) {
      return (
        <div className="animate-in fade-in duration-500">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      )
    }

    return null
  }

  return (
    <div
      className={cn(
        'group flex gap-4 px-6 py-10 transition-colors duration-300',
        isUser ? 'bg-transparent' : 'bg-card/30 border-y border-border/10'
      )}
    >
      <div
        className={cn(
          'flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl shadow-xl transition-transform group-hover:scale-110',
          isUser ? 'bg-secondary text-secondary-foreground' : 'bg-primary text-primary-foreground'
        )}
      >
        {isUser ? (
          <User className="h-5 w-5" />
        ) : (
          <Bot className="h-5 w-5" />
        )}
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-4 pr-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold tracking-tight text-foreground/90">
            {isUser ? 'You' : 'Financial Agent'}
          </span>
        </div>

        <div className="prose prose-invert max-w-none text-sm leading-7 text-foreground/90">
          {renderContent()}
        </div>

        {!isUser && getFullText() && (
          <div className="mt-4 flex items-center gap-3 opacity-0 transition-all duration-300 group-hover:opacity-100">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-8 gap-2 rounded-lg text-xs font-medium text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-500" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  Copy Text
                </>
              )}
            </Button>
            
            <div className="h-3 w-[1px] bg-border/40" />
            
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/40 font-bold">
              AI Generated Response
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
