'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { Card } from '@/components/ui/card'

interface ChartData {
  type: 'bar' | 'line' | 'pie'
  title: string
  data: any[]
  xKey: string
  yKey: string
  color?: string
  colors?: string[]
}

const DEFAULT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export function ChartRenderer({ chartData }: { chartData: string }) {
  let data: ChartData
  const renderError = (msg: string) => (
    <Card className="p-4 border-destructive/50 bg-destructive/5 text-destructive text-xs">
      {msg}
    </Card>
  )

  try {
    data = JSON.parse(chartData)
    if (!data.data || !Array.isArray(data.data)) {
      return renderError('Chart data is missing or invalid')
    }
    if (data.data.length === 0) {
      return renderError('No data available for this chart')
    }
  } catch (e) {
    return renderError('Failed to parse chart data')
  }

  const renderChart = () => {
    switch (data.type) {
      case 'bar':
        return (
          <BarChart data={data.data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey={data.xKey} 
              stroke="#888888" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
            />
            <YAxis 
              stroke="#888888" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
              tickFormatter={(value) => `${value}`} 
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
              itemStyle={{ color: '#ffffff' }}
            />
            <Bar 
              dataKey={data.yKey} 
              fill={data.color || '#3b82f6'} 
              radius={[4, 4, 0, 0]} 
            />
          </BarChart>
        )
      case 'line':
        return (
          <LineChart data={data.data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey={data.xKey} 
              stroke="#888888" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
            />
            <YAxis 
              stroke="#888888" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
            />
            <Line 
              type="monotone" 
              dataKey={data.yKey} 
              stroke={data.color || '#3b82f6'} 
              strokeWidth={2} 
              dot={{ r: 4 }} 
              activeDot={{ r: 6 }} 
            />
          </LineChart>
        )
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data.data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey={data.yKey}
              nameKey={data.xKey}
            >
              {data.data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={data.colors?.[index] || DEFAULT_COLORS[index % DEFAULT_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
            />
            <Legend />
          </PieChart>
        )
      default:
        return <div>Unsupported chart type</div>
    }
  }

  return (
    <Card className="my-4 overflow-hidden border-border bg-card/30 p-6 shadow-xl backdrop-blur-sm animate-in fade-in zoom-in duration-500">
      <h3 className="mb-6 text-sm font-semibold text-foreground/90 flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-accent" />
        {data.title}
      </h3>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
