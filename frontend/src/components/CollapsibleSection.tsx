import type { ReactNode } from 'react'

interface CollapsibleSectionProps {
  summary: string
  children: ReactNode
}

/**
 * Native <details>/<summary> - keyboard-accessible and announces its
 * expanded/collapsed state to assistive tech automatically, with no
 * extra state management or JS event handling required.
 *
 * `list-none` matters: a <summary> is `display: list-item`, and the
 * CSS reset only clears list styling from ul/ol/menu, so without it
 * the browser draws its own marker beside the toggle - which reads as
 * a stray empty bullet next to the label. The nested disclosures in
 * OtherTransferOptions suppress it the same way.
 */
export function CollapsibleSection({ summary, children }: CollapsibleSectionProps) {
  return (
    <details className="mt-2">
      <summary className="cursor-pointer list-none text-sm font-medium text-accent [&::-webkit-details-marker]:hidden">
        {summary}
      </summary>
      <div className="mt-2 flex flex-col gap-2">{children}</div>
    </details>
  )
}
