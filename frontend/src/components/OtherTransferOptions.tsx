import type { TransferRecommendationResponse } from '../api/types'
import { formatSigned, nonEmptyReasons, NO_REASONS_FALLBACK } from '../lib/format'
import { Panel } from './Panel'

interface OtherTransferOptionsProps {
  transferRecommendations: TransferRecommendationResponse[]
  bestTransfer: TransferRecommendationResponse | null
  freeTransfersAvailable: number | null
}

function isSamePair(a: TransferRecommendationResponse, b: TransferRecommendationResponse): boolean {
  return a.sell.player_id === b.sell.player_id && a.buy.player_id === b.buy.player_id
}

/**
 * Level 2 of the transfer recommendation: the other sell -> buy pairs
 * the backend returned in transfer_recommendations, beyond the one
 * already named as best_transfer in the hero. Rendered in the exact
 * order the backend returned them - never re-ranked. Each pair shows
 * only sell -> buy, expected gain, and priority by default; the
 * pair's own reasons are inspectable per-row via native <details>
 * rather than shown for every pair at once.
 *
 * These are alternatives, not a combined instruction: each is its own
 * standalone one-transfer move a manager could make *instead of* the
 * best transfer, not a batch to execute together - the heading and
 * subtext say so explicitly so the list can't be read as "do all of
 * these".
 */
export function OtherTransferOptions({
  transferRecommendations,
  bestTransfer,
  freeTransfersAvailable,
}: OtherTransferOptionsProps) {
  const others = bestTransfer
    ? transferRecommendations.filter((pair) => !isSamePair(pair, bestTransfer))
    : transferRecommendations

  if (others.length === 0) {
    return null
  }

  return (
    <Panel>
      <h2 className="text-base font-medium text-text">
        Alternative transfers <span className="text-text-muted">({others.length})</span>
      </h2>
      <p className="mt-1 text-xs text-text-muted">
        Each option is a separate one-transfer move, not a combined plan. Your available free
        transfers: {freeTransfersAvailable ?? 'not supplied'}.
      </p>
      <div className="mt-4">
        {others.map((pair) => {
          const reasons = nonEmptyReasons(pair.reasons)

          return (
            <details
              key={`${pair.sell.player_id}-${pair.buy.player_id}`}
              className="border-b border-border py-2.5 last:border-b-0"
            >
              <summary className="flex cursor-pointer list-none items-baseline justify-between gap-3 text-sm">
                <span className="text-text">
                  {pair.sell.web_name} → {pair.buy.web_name}
                </span>
                <span className="whitespace-nowrap text-right text-xs text-text-muted">
                  {formatSigned(pair.expected_point_gain)} expected ·{' '}
                  <span className="capitalize">{pair.priority}</span>
                </span>
              </summary>
              {reasons.length > 0 ? (
                <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-text-secondary">
                  {reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-text-muted">{NO_REASONS_FALLBACK}</p>
              )}
            </details>
          )
        })}
      </div>
    </Panel>
  )
}
