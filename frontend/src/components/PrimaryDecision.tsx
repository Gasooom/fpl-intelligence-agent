import type {
  EvidenceBasisResponse,
  PlayerDecisionResponse,
  TransferRecommendationResponse,
} from '../api/types'
import { formatPoints, formatPrice, formatSigned } from '../lib/format'
import { EvidenceStrength } from './EvidenceStrength'

interface PrimaryDecisionProps {
  gameweek: number
  /** Both supplied by the backend. When the plan looks ahead to a
   * gameweek the manager has not picked a squad for yet, the heading
   * says so and names the squad it was planned with. */
  isFutureGameweek: boolean
  sourcePicksGameweek: number
  captain: PlayerDecisionResponse
  viceCaptain: PlayerDecisionResponse
  bestTransfer: TransferRecommendationResponse | null
  confidence: string
  evidenceBasis: EvidenceBasisResponse
  projectedGameweekPoints: number
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
 * The executive summary: what this gameweek's decision is, readable in
 * a few seconds and without knowing any FPL shorthand.
 *
 * The headline answers the two questions a first-time reader actually
 * has - how many points is this squad projected to score, and who is
 * captain - in plain words, with the technical abbreviation kept as a
 * quiet secondary marker rather than the primary label. The one action
 * item follows, then the evidence behind it all.
 *
 * Every value comes straight from the API; nothing is computed,
 * ranked, or re-totaled here.
 */
export function PrimaryDecision({
  gameweek,
  isFutureGameweek,
  sourcePicksGameweek,
  captain,
  viceCaptain,
  bestTransfer,
  confidence,
  evidenceBasis,
  projectedGameweekPoints,
  summary,
  freeTransfersAvailable,
  inTheBank,
}: PrimaryDecisionProps) {
  return (
    <div>
      {isFutureGameweek ? (
        <>
          <p className="text-xs text-text-muted">Upcoming Gameweek</p>
          <p className="mt-0.5 text-sm text-text-secondary">Gameweek {gameweek}</p>
        </>
      ) : (
        <p className="text-sm text-text-muted">Gameweek {gameweek}</p>
      )}
      <h2 className="mt-1 text-2xl font-semibold text-text">Recommended plan</h2>
      {isFutureGameweek && (
        <p className="mt-1.5 text-sm text-text-secondary">
          Planned with your Gameweek {sourcePicksGameweek} squad.
        </p>
      )}

      <div className="mt-7 flex flex-wrap items-start gap-x-12 gap-y-6">
        <div>
          <p className="text-xs text-text-muted">
            Projected points{' '}
            <abbr
              title="Expected points — the projected gameweek total, including the captain multiplier"
              className="text-text-muted/80 no-underline"
            >
              (xP)
            </abbr>
          </p>
          <p className="mt-1 text-4xl font-semibold tabular-nums text-text">
            {formatPoints(projectedGameweekPoints)}
          </p>
        </div>

        <div>
          <p className="text-xs text-text-muted">Captain</p>
          <p className="mt-1 text-2xl font-medium text-text">{captain.web_name}</p>
        </div>
      </div>

      <div className="mt-8 border-t border-border pt-6">
        <p className="text-xs text-text-muted">Best transfer</p>
        {bestTransfer ? (
          <>
            <p className="mt-0.5 text-2xl font-semibold text-text">
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

        {bestTransfer && <TransferEconomics transfer={bestTransfer} />}
      </div>

      <div className="mt-6 flex flex-wrap gap-x-8 gap-y-4 border-t border-border pt-6">
        <div>
          <p className="text-xs text-text-muted">Vice-captain</p>
          <p className="mt-0.5 text-base font-medium text-text">{viceCaptain.web_name}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">Free transfers</p>
          <p className="mt-0.5 text-base text-text">{freeTransfersAvailable ?? 'Not supplied'}</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">In the bank</p>
          <p className="mt-0.5 text-base text-text">
            {inTheBank === null ? 'Unknown' : formatPrice(inTheBank)}
          </p>
        </div>

        {/* Evidence sits with the decision it qualifies, not in a
            separate panel: it is context for reading the plan above,
            and is never styled as a warning. */}
        <EvidenceStrength confidence={confidence} basis={evidenceBasis} />
      </div>

      <p className="mt-6 max-w-xl text-sm leading-relaxed text-text-secondary">{summary}</p>
    </div>
  )
}
