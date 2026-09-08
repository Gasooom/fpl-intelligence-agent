import type { PlayerDecisionResponse, TransferRecommendationResponse } from '../api/types'
import { formatPrice, formatSigned } from '../lib/format'

interface PrimaryDecisionProps {
  gameweek: number
  captain: PlayerDecisionResponse
  viceCaptain: PlayerDecisionResponse
  bestTransfer: TransferRecommendationResponse | null
  confidence: string
  summary: string
  freeTransfersAvailable: number | null
  inTheBank: number | null
}

function Figure({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <p className="text-xs text-text-muted">{label}</p>
      <p className={`mt-0.5 text-sm ${tone ?? 'text-text'}`}>{value}</p>
    </div>
  )
}

/**
 * The transfer's real economics, exactly as the backend computed them:
 * raw points gain, the hit cost of making it, and what's left after
 * that cost. Rendered only when the backend actually has them - it
 * returns null hit_cost/net_value when no free-transfer count was
 * supplied, since no public FPL endpoint exposes one. Nothing here is
 * recalculated in the browser; even the "Free" wording is chosen from
 * the backend's own hit_cost value.
 */
function TransferEconomics({ transfer }: { transfer: TransferRecommendationResponse }) {
  if (transfer.hit_cost === null || transfer.net_value === null) {
    return null
  }

  const isFree = transfer.hit_cost === 0

  return (
    <div className="mt-5 flex flex-wrap gap-x-8 gap-y-4">
      <Figure label="Expected gain" value={formatSigned(transfer.expected_point_gain)} />
      <Figure
        label="Transfer cost"
        value={isFree ? 'Free' : `-${transfer.hit_cost} points`}
        tone={isFree ? undefined : 'text-eval-negative'}
      />
      <Figure
        label="Net expected value"
        value={formatSigned(transfer.net_value)}
        tone={transfer.net_value > 0 ? 'text-eval-positive' : undefined}
      />
    </div>
  )
}

/**
 * The hero: the single most important thing on the page, readable in
 * a few seconds. Every value here comes straight from the API -
 * nothing computed, nothing ranked. The best transfer leads (it's the
 * one action item this gameweek), with its own priority shown
 * alongside it exactly as the backend labels it; captain, vice,
 * confidence, and the manager's transfer context follow as a compact
 * supporting line rather than a second headline. Confidence is
 * metadata, not a verdict - Low confidence is never colored like a
 * warning.
 */
export function PrimaryDecision({
  gameweek,
  captain,
  viceCaptain,
  bestTransfer,
  confidence,
  summary,
  freeTransfersAvailable,
  inTheBank,
}: PrimaryDecisionProps) {
  return (
    <div>
      <p className="text-sm text-text-muted">Gameweek {gameweek}</p>
      <h2 className="mt-1 text-2xl font-semibold text-text">Recommended plan</h2>

      <div className="mt-7">
        <p className="text-xs text-text-muted">Best transfer</p>
        {bestTransfer ? (
          <>
            <p className="mt-0.5 text-3xl font-semibold text-text">
              {bestTransfer.sell.web_name} → {bestTransfer.buy.web_name}
            </p>
            <p className="mt-1.5 text-sm text-text-secondary">
              {formatSigned(bestTransfer.expected_point_gain)} expected points ·{' '}
              <span className="capitalize">{bestTransfer.priority}</span>
            </p>
          </>
        ) : (
          <p className="mt-0.5 text-lg text-text-secondary">No worthwhile transfer this gameweek</p>
        )}
      </div>

      {bestTransfer && <TransferEconomics transfer={bestTransfer} />}

      <div className="mt-6 flex flex-wrap gap-x-8 gap-y-4">
        <div>
          <p className="text-xs text-text-muted">Captain</p>
          <p className="mt-0.5 text-base font-medium text-text">{captain.web_name}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Vice-captain</p>
          <p className="mt-0.5 text-base font-medium text-text">{viceCaptain.web_name}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Confidence</p>
          <p className="mt-0.5 text-base text-text">{confidence}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Free transfers</p>
          <p className="mt-0.5 text-base text-text">
            {freeTransfersAvailable ?? 'Not supplied'}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-muted">In the bank</p>
          <p className="mt-0.5 text-base text-text">
            {inTheBank === null ? 'Unknown' : formatPrice(inTheBank)}
          </p>
        </div>
      </div>

      {/* The backend derives this label from how much playing-time
          evidence backs the starting XI and how much risk it carries -
          so it is described as exactly that, and never relabeled
          "evidence strength", which would drop the risk half of the
          definition. Low here means thin evidence, not a weak
          recommendation, which is why it is never styled as a warning. */}
      <p className="mt-3 max-w-xl text-xs leading-relaxed text-text-muted">
        Confidence describes the evidence and risk behind this plan, not how strong the
        recommendation is.
      </p>

      <p className="mt-6 max-w-xl text-sm leading-relaxed text-text-secondary">{summary}</p>
    </div>
  )
}
