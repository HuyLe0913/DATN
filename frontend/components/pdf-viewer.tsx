'use client'

import { useState, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, X, FileText, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { formatFileSize, type PDFFile } from '@/lib/pdf-utils'

import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

interface PDFViewerProps {
  file: PDFFile | null
  onClose: () => void
  className?: string
}

export function PDFViewer({ file, onClose, className }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [scale, setScale] = useState(1.0)

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setCurrentPage(1)
  }, [])

  const goToPrevPage = () => setCurrentPage((prev) => Math.max(1, prev - 1))
  const goToNextPage = () => setCurrentPage((prev) => Math.min(numPages, prev + 1))
  const zoomIn = () => setScale((prev) => Math.min(2, prev + 0.2))
  const zoomOut = () => setScale((prev) => Math.max(0.5, prev - 0.2))

  if (!file) {
    return (
      <div className={cn('flex flex-col items-center justify-center bg-card border-l border-border', className)}>
        <FileText className="h-16 w-16 text-muted-foreground mb-4" />
        <p className="text-muted-foreground text-sm">No PDF selected</p>
        <p className="text-muted-foreground text-xs mt-1">Upload a financial report to view here</p>
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col bg-card border-l border-border', className)}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-3 min-w-0">
          <FileText className="h-5 w-5 text-accent shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{file.name}</p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(file.size)} - {file.pageCount} pages
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => window.open(file.url, '_blank')}
            title="Download PDF"
          >
            <Download className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onClose}
            title="Close PDF"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-center gap-2 border-b border-border px-4 py-2 bg-secondary/30">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={goToPrevPage}
          disabled={currentPage <= 1}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm text-muted-foreground min-w-[80px] text-center">
          {currentPage} / {numPages}
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={goToNextPage}
          disabled={currentPage >= numPages}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <div className="w-px h-5 bg-border mx-2" />
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={zoomOut}
          disabled={scale <= 0.5}
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <span className="text-sm text-muted-foreground min-w-[50px] text-center">
          {Math.round(scale * 100)}%
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={zoomIn}
          disabled={scale >= 2}
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
      </div>

      {/* PDF Document */}
      <ScrollArea className="flex-1">
        <div className="flex justify-center p-4">
          <Document
            file={file.url}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin h-8 w-8 border-2 border-accent border-t-transparent rounded-full" />
              </div>
            }
            error={
              <div className="flex flex-col items-center justify-center h-64 text-destructive">
                <FileText className="h-12 w-12 mb-2" />
                <p className="text-sm">Failed to load PDF</p>
              </div>
            }
            className="pdf-document"
          >
            <Page
              pageNumber={currentPage}
              scale={scale}
              className="shadow-lg rounded-lg overflow-hidden"
              renderTextLayer={true}
              renderAnnotationLayer={true}
            />
          </Document>
        </div>
      </ScrollArea>
    </div>
  )
}
