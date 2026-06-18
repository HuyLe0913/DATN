'use client'

import { useState, useCallback, useRef } from 'react'
import { Upload, FileText, X, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import {
  validatePDFFile,
  extractTextFromPDF,
  createFileUrl,
  formatFileSize,
  type PDFFile,
} from '@/lib/pdf-utils'

interface PDFUploadModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onFileUploaded: (file: PDFFile) => void
}

export function PDFUploadModal({ open, onOpenChange, onFileUploaded }: PDFUploadModalProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const resetState = useCallback(() => {
    setError(null)
    setSelectedFile(null)
    setIsProcessing(false)
  }, [])

  const handleClose = useCallback(() => {
    resetState()
    onOpenChange(false)
  }, [onOpenChange, resetState])

  const processFile = useCallback(async (file: File) => {
    const validation = validatePDFFile(file)
    if (!validation.valid) {
      setError(validation.error || 'Invalid file')
      return
    }

    setSelectedFile(file)
    setError(null)
    setIsProcessing(true)

    try {
      const { text, pageCount } = await extractTextFromPDF(file)
      const url = createFileUrl(file)

      const pdfFile: PDFFile = {
        name: file.name,
        size: file.size,
        url,
        text,
        pageCount,
      }

      onFileUploaded(pdfFile)
      handleClose()
    } catch (err) {
      console.error('Error processing PDF:', err)
      setError('Failed to process PDF file. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }, [handleClose, onFileUploaded])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      processFile(file)
    }
  }, [processFile])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      processFile(file)
    }
  }, [processFile])

  const handleBrowseClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md bg-card border-border">
        <DialogHeader>
          <DialogTitle className="text-foreground">Upload Financial Report</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Upload a PDF file to analyze. Maximum file size is 10MB.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleBrowseClick}
            className={cn(
              'relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all cursor-pointer',
              isDragging
                ? 'border-accent bg-accent/10'
                : 'border-border hover:border-muted-foreground hover:bg-secondary/50',
              isProcessing && 'pointer-events-none opacity-60'
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileSelect}
              className="sr-only"
            />

            {isProcessing ? (
              <>
                <Loader2 className="h-12 w-12 text-accent animate-spin mb-4" />
                <p className="text-sm font-medium text-foreground">Processing PDF...</p>
                <p className="text-xs text-muted-foreground mt-1">Extracting text content</p>
              </>
            ) : selectedFile ? (
              <>
                <FileText className="h-12 w-12 text-accent mb-4" />
                <p className="text-sm font-medium text-foreground truncate max-w-full">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatFileSize(selectedFile.size)}
                </p>
              </>
            ) : (
              <>
                <Upload className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-sm font-medium text-foreground">
                  Drop your PDF here or click to browse
                </p>
                <p className="text-xs text-muted-foreground mt-1">PDF files only, up to 10MB</p>
              </>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p className="text-sm">{error}</p>
              <Button
                variant="ghost"
                size="icon"
                className="ml-auto h-6 w-6"
                onClick={() => setError(null)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={handleClose} disabled={isProcessing}>
              Cancel
            </Button>
            <Button onClick={handleBrowseClick} disabled={isProcessing}>
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing
                </>
              ) : (
                'Select File'
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
