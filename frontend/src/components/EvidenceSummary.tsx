import type { EvidenceResponse, TransferRecommendationResponse } from '../api/types'
import { NO_REASONS_FALLBACK, nonEmptyReasons } from '../lib/format'
import { resolvePlayerName } from '../lib/playerLookup'
import { CollapsibleSection } from './CollapsibleSection'

interface EvidenceSummaryProps {
  evidence: EvidenceResponse[]
  nameLookup: Map<number, string>
  captainId: number
  viceCaptainId: number
  bestTransfer: TransferRecommendationResponse | null
}

/**
 * Reasons phrased as "X vs Y" are the same pairwise comparison
 * WhyThisDecision already shows (built from the same underlying
 * fields, just labeled differently) - dropped here so the best
 * transfer's evidence group adds source-level facts instead of
 * repeating that comparison a second time. Every reason kept is still
 * verbatim backend text; nothing here is reworded or invented.
 */
function isComparativeReason(reason: string): boolean {
  return / vs /i.test(reason)
}

/**
 * Renders only when there's a matching evidence entry (`items` is
 * non-empty) - if that entry's reasons are empty (or filter down to
 * nothing after dropping blank strings and, for the best-transfer
 * group, comparative duplicates), the heading still renders with an
 * honest fallback line rather than disappearing or leaving empty
 * bullets.
 */
function EvidenceGroup({
  title,
  items,
  excludeComparative = false,
}: {
  title: string
  items: EvidenceResponse[]
  excludeComparative?: boolean
}) {
  if (items.length === 0) return null

  const reasons = nonEmptyReasons(items.flatMap((item) => item.reasons)).filter(
    (reason) => !excludeComparative || !isComparativeReason(reason),
  )

  return (
    <div>
      <p className="text-sm text-text">{title}</p>
      {reasons.length > 0 ? (
        <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-text-secondary">
          {reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-text-muted">{NO_REASONS_FALLBACK}</p>
      )}
    </div>
  )
}

/**
 * A compact "decision evidence" summary - only the reasons directly
 * behind the captain, vice-captain, and best transfer by default.
 * Everything else the backend returned in `evidence` (e.g. must_play,
 * other sell/buy candidates) sits behind "View all evidence" rather
 * than a long wall of text on the default view. Filtering which
 * already-returned entries to feature is presentation, not decision
 * logic - nothing here is computed, reworded, or reordered.
 */
export function EvidenceSummary({
  evidence,
  nameLookup,
  captainId,
  viceCaptainId,
  bestTransfer,
}: EvidenceSummaryProps) {
  const captainEvidence = evidence.filter(
    (item) => item.decision === 'captain' && item.player_id === captainId,
  )
  const viceEvidence = evidence.filter(
    (item) => item.decision === 'vice_captain' && item.player_id === viceCaptainId,
  )
  const bestTransferEvidence = bestTransfer
    ? evidence.filter(
        (item) =>
          (item.decision === 'sell' && item.player_id === bestTransfer.sell.player_id) ||
          (item.decision === 'buy' && item.player_id === bestTransfer.buy.player_id),
      )
    : []

  const highlighted = new Set([...captainEvidence, ...viceEvidence, ...bestTransferEvidence])
  const rest = evidence.filter((item) => !highlighted.has(item))

  return (
    <section className="border-t border-border px-5 py-7 sm:px-6">
      <h2 className="text-base font-medium text-text">Decision evidence</h2>

      {evidence.length === 0 ? (
        <p className="mt-4 text-sm text-text-muted">
          No supporting evidence is available for this decision.
        </p>
      ) : (
        <>
          <div className="mt-4 flex flex-col gap-6">
            <EvidenceGroup
              title={`Captain — ${resolvePlayerName(nameLookup, captainId)}`}
              items={captainEvidence}
            />
            <EvidenceGroup
              title={`Vice-captain — ${resolvePlayerName(nameLookup, viceCaptainId)}`}
              items={viceEvidence}
            />
            {bestTransfer && (
              <EvidenceGroup
                title={`Best transfer — ${bestTransfer.sell.web_name} → ${bestTransfer.buy.web_name}`}
                items={bestTransferEvidence}
                excludeComparative
              />
            )}
          </div>

          {rest.length > 0 && (
            <CollapsibleSection summary="View all evidence">
              <div className="flex flex-col gap-5">
                {rest.map((item, index) => {
                  const reasons = nonEmptyReasons(item.reasons)

                  return (
                    <div key={`${item.decision}-${item.player_id}-${index}`}>
                      <p className="text-sm text-text">
                        {item.decision} — {resolvePlayerName(nameLookup, item.player_id)}
                      </p>
                      {reasons.length > 0 ? (
                        <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-text-secondary">
                          {reasons.map((reason) => (
                            <li key={reason}>{reason}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="mt-2 text-sm text-text-muted">{NO_REASONS_FALLBACK}</p>
                      )}
                    </div>
                  )
                })}
              </div>
            </CollapsibleSection>
          )}
        </>
      )}
    </section>
  )
}
