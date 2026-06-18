'use client'

import { ArrowUp, Loader2, Paperclip, Square } from 'lucide-react'
import { useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  isLoading: boolean
  placeholder?: string
  onUploadClick?: () => void
  hasAttachment?: boolean
  onStop?: () => void
}

export function ChatInput({
  value = '',
  onChange,
  onSubmit,
  isLoading,
  placeholder = 'Send a message...',
  onUploadClick,
  hasAttachment = false,
  onStop,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`
    }
  }, [value])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value?.trim() && !isLoading) {
        onSubmit()
      }
    }
  }

  return (
    <div className="border-t border-border bg-background/95 p-4 backdrop-blur-sm">
      <div className="mx-auto max-w-3xl">
        <div className="relative flex items-end gap-2 rounded-2xl border border-border bg-input p-2 shadow-lg transition-colors focus-within:border-ring">
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              'h-9 w-9 shrink-0 transition-colors',
              hasAttachment
                ? 'text-accent hover:text-accent/80'
                : 'text-muted-foreground hover:text-foreground'
            )}
            disabled={isLoading}
            onClick={onUploadClick}
          >
            <Paperclip className="h-5 w-5" />
            <span className="sr-only">Attach PDF file</span>
          </Button>

          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange?.(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className={cn(
              'min-h-[40px] flex-1 resize-none border-0 bg-transparent px-2 py-2.5 text-base md:text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0',
              'scrollbar-thin scrollbar-track-transparent scrollbar-thumb-border'
            )}
          />

          <Button
            size="icon"
            onClick={isLoading ? onStop : onSubmit}
            disabled={!isLoading && !value?.trim()}
            className={cn(
              'h-9 w-9 shrink-0 rounded-xl transition-all flex items-center justify-center',
              isLoading 
                ? 'bg-destructive/10 text-destructive hover:bg-destructive/20'
                : (value?.trim() ? 'bg-primary text-primary-foreground hover:bg-primary/90' : 'bg-secondary text-muted-foreground')
            )}
          >
            {isLoading ? (
              <Square className="h-4 w-4 fill-current" />
            ) : (
              <ArrowUp className="h-5 w-5" />
            )}
            <span className="sr-only">{isLoading ? 'Stop generating' : 'Send message'}</span>
          </Button>
        </div>

        <p className="mt-2 text-center text-xs text-muted-foreground">
          AI may produce inaccurate information. Consider verifying important facts.
        </p>
      </div>
    </div>
  )
}
