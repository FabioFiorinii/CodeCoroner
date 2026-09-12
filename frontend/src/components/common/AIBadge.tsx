import { Bot } from 'lucide-react'

interface AIBadgeProps {
  aiGenerated?: boolean
  modelName?: string
  modelVersion?: string
  generatedAt?: string
  className?: string
}

export function AIBadge({
  aiGenerated = true,
  modelName = '',
  modelVersion = '',
  generatedAt = '',
  className = '',
}: AIBadgeProps) {
  if (!aiGenerated) return null

  const displayModel = modelVersion ? `${modelName.split(':')[0]}:${modelVersion}` : modelName
  const formattedDate = generatedAt
    ? new Date(generatedAt).toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : ''

  const tooltipParts = []
  if (displayModel) tooltipParts.push(`Model: ${displayModel}`)
  if (formattedDate) tooltipParts.push(`Generated: ${formattedDate}`)

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full bg-purple-50 text-purple-700 border border-purple-200 ${className}`}
      title={tooltipParts.join(' · ') || 'AI-generated content'}
      role="img"
      aria-label="AI-generated content"
    >
      <Bot className="w-3 h-3 shrink-0" aria-hidden="true" />
      <span className="font-medium">AI-generated</span>
    </span>
  )
}