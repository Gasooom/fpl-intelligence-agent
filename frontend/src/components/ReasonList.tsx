import { nonEmptyReasons, NO_REASONS_FALLBACK } from '../lib/format'

interface ReasonListProps {
  reasons: (string | null | undefined)[] | null | undefined
  /** Shown when nothing survives filtering. Defaults to the shared
   * honest fallback rather than rendering an empty list. */
  emptyMessage?: string
  className?: string
}

/**
 * The single place a list of reason sentences is rendered.
 *
 * Every caller previously filtered blanks for itself, which meant one
 * component forgetting to filter could put an empty bullet on screen.
 * Filtering happens here instead, so a blank, whitespace-only, null or
 * undefined entry can never produce a bullet with nothing next to it -
 * and a collection that empties out entirely renders a plain sentence
 * rather than an empty list.
 *
 * Only ever removes entries: the backend's own wording passes through
 * untouched, never reordered, reworded, or added to.
 */
export function ReasonList({
  reasons,
  emptyMessage = NO_REASONS_FALLBACK,
  className,
}: ReasonListProps) {
  const items = nonEmptyReasons(reasons)

  if (items.length === 0) {
    return <p className="mt-2 text-sm text-text-muted">{emptyMessage}</p>
  }

  return (
    <ul
      className={
        className ?? 'mt-2 list-inside list-disc space-y-1 text-sm text-text-secondary'
      }
    >
      {items.map((reason, index) => (
        // Reason text repeats across groups (several buy candidates
        // share "Better points-per-price value"), so the index is part
        // of the key - a duplicate key would make React drop a row that
        // the backend genuinely returned.
        <li key={`${reason}-${index}`}>{reason}</li>
      ))}
    </ul>
  )
}
