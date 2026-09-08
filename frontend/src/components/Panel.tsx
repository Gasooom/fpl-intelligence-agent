import type { ReactNode } from 'react'

interface PanelProps {
  children: ReactNode
  /** Slightly more presence for the panel that carries the product's
   * core idea (the evaluation), without resorting to a colored
   * background or a heavy border. */
  emphasized?: boolean
}

/**
 * One of the handful of meaningful groups the page is built from -
 * decision, why, squad, transfers, evaluation. A quiet surface and a
 * hairline border, nothing more: this exists to group, not to
 * decorate, so there are five of these rather than a card per data
 * point.
 */
export function Panel({ children, emphasized = false }: PanelProps) {
  return (
    <section
      className={`rounded-xl border bg-surface px-5 py-6 sm:px-6 ${
        emphasized ? 'border-border-strong/60' : 'border-border-panel'
      }`}
    >
      {children}
    </section>
  )
}
