import type { TransferRecommendationResponse } from '../api/types'
import { capitalize, formatPoints, nonEmptyReasons } from '../lib/format'
import { CollapsibleSection } from './CollapsibleSection'
import { Panel } from './Panel'

interface WhyThisDecisionProps {
  bestTransfer: TransferRecommendationResponse | null
}

interface ComparisonRow {
  label: string
  buyValue: string
  sellValue: string
}

/** Ordinal only for choosing which direction to label a risk_level
 * comparison ("Lower risk" vs "Higher risk") - the values actually
 * displayed are always the backend's own strings, never this rank. */
const RISK_RANK: Record<string, number> = { low: 0, medium: 1, high: 2 }

function buildComparisonRows(pair: TransferRecommendationResponse): ComparisonRow[] {
  const { sell, buy } = pair
  const rows: ComparisonRow[] = []

  if (buy.expected_points !== sell.expected_points) {
    rows.push({
      label: buy.expected_points > sell.expected_points ? 'Higher expected points' : 'Lower expected points',
      buyValue: formatPoints(buy.expected_points),
      sellValue: formatPoints(sell.expected_points),
    })
  }

  if (buy.fixture_difficulty !== sell.fixture_difficulty) {
    rows.push({
      label: buy.fixture_difficulty < sell.fixture_difficulty ? 'Better fixture' : 'Tougher fixture',
      buyValue: buy.fixture_difficulty.toFixed(1),
      sellValue: sell.fixture_difficulty.toFixed(1),
    })
  }

  const buyRisk = RISK_RANK[buy.risk_level.toLowerCase()]
  const sellRisk = RISK_RANK[sell.risk_level.toLowerCase()]
  if (buyRisk !== undefined && sellRisk !== undefined && buyRisk !== sellRisk) {
    rows.push({
      label: buyRisk < sellRisk ? 'Lower risk' : 'Higher risk',
      buyValue: capitalize(buy.risk_level),
      sellValue: capitalize(sell.risk_level),
    })
  }

  if (buy.form !== sell.form) {
    rows.push({
      label: buy.form > sell.form ? 'Better recent form' : 'Weaker recent form',
      buyValue: formatPoints(buy.form),
      sellValue: formatPoints(sell.form),
    })
  }

  return rows
}

/**
 * A comparison layout, not a list of colored badges: each row is one
 * axis the backend already returned for both the sell and buy side of
 * the recommended pair (expected points, fixture, risk, form), with a
 * plain-English direction label. Nothing is scored or ranked here -
 * every value shown is a real field already on SellCandidateResponse
 * / BuyCandidateResponse, just placed side by side. The backend's own
 * free-text reasons for the pair are still available in full, just
 * folded behind disclosure so they don't duplicate the same
 * comparison as the Evidence section further down the page.
 */
export function WhyThisDecision({ bestTransfer }: WhyThisDecisionProps) {
  if (!bestTransfer) {
    return null
  }

  const rows = buildComparisonRows(bestTransfer)
  const reasons = nonEmptyReasons(bestTransfer.reasons)
  if (rows.length === 0 && reasons.length === 0) {
    return null
  }

  return (
    <Panel>
      <h2 className="text-base font-medium text-text">
        Why {bestTransfer.sell.web_name} → {bestTransfer.buy.web_name}?
      </h2>

      {rows.length > 0 && (
        <div className="mt-4 flex flex-col gap-3">
          {rows.map((row) => (
            <div key={row.label} className="flex items-baseline justify-between gap-4 text-sm">
              <span className="text-text-secondary">{row.label}</span>
              <span className="tabular-nums text-text">
                {row.buyValue} vs {row.sellValue}
              </span>
            </div>
          ))}
        </div>
      )}

      {reasons.length > 0 && (
        <CollapsibleSection summary="Backend reasoning">
          <ul className="list-inside list-disc space-y-1 text-sm text-text-secondary">
            {reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </CollapsibleSection>
      )}
    </Panel>
  )
}
