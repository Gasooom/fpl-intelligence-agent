import type { ReactNode } from 'react'

interface CollapsibleSectionProps {
  summary: string
  children: ReactNode
}

/**
 * Native <details>/<summary> - keyboard-accessible and announces its
 * expanded/collapsed state to assistive tech automatically, with no
 * extra state management or JS event handling required.
 */
export function CollapsibleSection({ summary, children }: CollapsibleSectionProps) {
  return (
    <details className="mt-2">
      <summary className="cursor-pointer text-sm font-medium text-accent">{summary}</summary>
      <div className="mt-2 flex flex-col gap-2">{children}</div>
    </details>
  )
}
