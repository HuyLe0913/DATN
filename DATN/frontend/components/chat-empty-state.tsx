'use client'

import { Bot, TrendingUp, PieChart, BarChart3, FileText, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatEmptyStateProps {
  onSuggestionClick: (suggestion: string) => void
  hasPdfAttached?: boolean
}

const defaultSuggestions = [
  {
    icon: TrendingUp,
    title: 'Revenue Analysis',
    description: 'Analyze revenue trends',
    prompt: 'Upload a financial report and I can help analyze revenue trends, growth rates, and key performance indicators.',
  },
  {
    icon: PieChart,
    title: 'Balance Sheet Review',
    description: 'Review assets and liabilities',
    prompt: 'I can help review balance sheets to analyze assets, liabilities, equity positions and financial health indicators.',
  },
  {
    icon: BarChart3,
    title: 'Profitability Metrics',
    description: 'Calculate key ratios',
    prompt: 'Let me help you calculate and interpret profitability ratios like gross margin, operating margin, and ROE.',
  },
  {
    icon: FileText,
    title: 'Compare Reports',
    description: 'Year-over-year analysis',
    prompt: 'I can help compare financial reports across different periods to identify trends and changes in performance.',
  },
]

const pdfSuggestions = [
  {
    icon: TrendingUp,
    title: 'Summarize Report',
    description: 'Get key highlights',
    prompt: 'Please provide a summary of the key financial highlights from this report, including main revenue figures and profit metrics.',
  },
  {
    icon: PieChart,
    title: 'Financial Ratios',
    description: 'Calculate important ratios',
    prompt: 'Calculate and explain the key financial ratios from this report, including liquidity, profitability, and efficiency ratios.',
  },
  {
    icon: BarChart3,
    title: 'Risk Analysis',
    description: 'Identify potential risks',
    prompt: 'Analyze this financial report and identify any potential risks or concerns that investors should be aware of.',
  },
  {
    icon: FileText,
    title: 'Performance Review',
    description: 'Year-over-year comparison',
    prompt: 'Compare the financial performance shown in this report with previous periods and highlight significant changes or trends.',
  },
]

export function ChatEmptyState({ onSuggestionClick, hasPdfAttached = false }: ChatEmptyStateProps) {
  const suggestions = hasPdfAttached ? pdfSuggestions : defaultSuggestions

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-12 min-h-0 overflow-y-auto">
      <div className="mb-8 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary shadow-lg shadow-primary/20">
        <Bot className="h-8 w-8 text-primary-foreground" />
      </div>

      <h1 className="mb-2 text-center text-2xl font-semibold text-foreground sm:text-3xl text-balance">
        {hasPdfAttached 
          ? 'Ready to Analyze Your Report'
          : 'Financial Report Analyzer'
        }
      </h1>
      
      {hasPdfAttached ? (
        <div className="mb-6 flex items-center gap-2 rounded-full bg-accent/20 px-4 py-2">
          <CheckCircle className="h-4 w-4 text-accent" />
          <span className="text-sm text-accent">PDF attached and ready for analysis</span>
        </div>
      ) : (
        <p className="mb-10 max-w-md text-center text-muted-foreground text-pretty">
          Upload a financial report PDF to get started, or choose a suggestion below to learn more.
        </p>
      )}

      <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-2">
        {suggestions.map((suggestion) => (
          <Button
            key={suggestion.title}
            variant="outline"
            className="group flex h-auto flex-col items-start gap-1 border-border bg-card p-4 text-left transition-all hover:border-ring hover:bg-card/80"
            onClick={() => onSuggestionClick(suggestion.prompt)}
          >
            <div className="flex items-center gap-2">
              <suggestion.icon className="h-4 w-4 text-muted-foreground group-hover:text-accent" />
              <span className="text-sm font-medium text-foreground">
                {suggestion.title}
              </span>
            </div>
            <span className="text-xs text-muted-foreground">
              {suggestion.description}
            </span>
          </Button>
        ))}
      </div>
    </div>
  )
}
