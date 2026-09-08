import { formatPoints, riskTextClass } from '../lib/format'

interface PlayerRowProps {
  name: string
  expectedPoints: number
  riskLevel: string
  /** A subtle inline tag - "Captain", "Vice-captain", "Must play",
   * "Sub 1" - never a colored badge. */
  marker?: string
  /** Extra small supporting text before the points/risk, e.g. a rank. */
  meta?: string
  /** Reduced visual weight, used for the bench - same fields, lower
   * priority. */
  muted?: boolean
}

/**
 * One line per player: name, projection, risk. The projection is
 * always labeled "expected" rather than "pts", so a pre-gameweek
 * prediction can never be mistaken for points actually scored -
 * see the evaluation sections for real, post-gameweek figures.
 * Shared by
 * Starting XI, Bench, and the transfer candidate lists rather than
 * duplicating this markup per section. A hairline bottom border
 * separates rows - no per-player card, no badges, no icons.
 */
export function PlayerRow({ name, expectedPoints, riskLevel, marker, meta, muted = false }: PlayerRowProps) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border py-2.5 last:border-b-0">
      <div className="flex items-baseline gap-2">
        <span className={`text-sm ${muted ? 'text-text-secondary' : 'text-text'}`}>{name}</span>
        {marker && <span className="text-xs text-text-muted">{marker}</span>}
      </div>
      <div className="whitespace-nowrap text-right text-xs text-text-muted">
        {meta && <span className="mr-2">{meta}</span>}
        {formatPoints(expectedPoints)} expected ·{' '}
        <span className={riskTextClass(riskLevel)}>{riskLevel} risk</span>
      </div>
    </div>
  )
}
