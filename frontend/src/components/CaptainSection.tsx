import type { PlayerDecisionResponse } from '../api/types'
import { formatPoints } from '../lib/format'

interface CaptainSectionProps {
  captain: PlayerDecisionResponse
  viceCaptain: PlayerDecisionResponse
}

/**
 * Projection (expected_points), captaincy_score, and effective_points
 * are three distinct labeled lines, never merged into one number - the
 * hero above already names the captain; this is where the supporting
 * figures live. effective_points (the FPL 2x multiplier) is shown only
 * for the captain, since it's only ever applied to whoever is actually
 * captained - the vice's own effective_points from the API always
 * equals their expected_points, so a "2x" line for them would be
 * misleading rather than merely redundant.
 */
export function CaptainSection({ captain, viceCaptain }: CaptainSectionProps) {
  return (
    <section className="border-t border-border pt-6 first:border-t-0 first:pt-0">
      <h2 className="text-base font-medium text-text">Captaincy</h2>
      <div className="mt-4 grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <p className="text-xs text-text-muted">Captain</p>
          <p className="mt-0.5 text-lg font-medium text-text">{captain.web_name}</p>
          <p className="mt-1 text-sm text-text-secondary">
            {formatPoints(captain.expected_points)} expected points
          </p>
          <p className="text-sm text-text-secondary">
            {formatPoints(captain.captaincy_score)} captaincy score
          </p>
          <p className="text-sm text-text-secondary">
            {formatPoints(captain.effective_points)} effective points (2x)
          </p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Vice</p>
          <p className="mt-0.5 text-lg font-medium text-text">{viceCaptain.web_name}</p>
          <p className="mt-1 text-sm text-text-secondary">
            {formatPoints(viceCaptain.expected_points)} expected points
          </p>
          <p className="text-sm text-text-secondary">
            {formatPoints(viceCaptain.captaincy_score)} captaincy score
          </p>
        </div>
      </div>
    </section>
  )
}
