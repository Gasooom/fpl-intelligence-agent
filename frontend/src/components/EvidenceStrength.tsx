import type { EvidenceBasisResponse } from '../api/types'
import { buildEvidenceFactors } from '../lib/evidenceFactors'
import { evidenceStrengthLabel } from '../lib/format'
import { CollapsibleSection } from './CollapsibleSection'

interface EvidenceStrengthProps {
  confidence: string
  basis: EvidenceBasisResponse
}

/**
 * Evidence strength, stated as what it measures rather than as a
 * verdict.
 *
 * "Limited" describes the playing-time record behind the projections,
 * not the quality of the recommendation - a limited-evidence plan is
 * still the plan the engine stands behind, which is why the
 * explanation says so in as many words. The detail is folded behind a
 * disclosure so the headline stays a single calm word, and it carries
 * no color of its own: evidence strength is context, never a warning.
 */
export function EvidenceStrength({ confidence, basis }: EvidenceStrengthProps) {
  const label = evidenceStrengthLabel(confidence)
  const isLimited = confidence.toLowerCase() === 'low'
  const factors = buildEvidenceFactors(basis)

  return (
    <div>
      <p className="text-xs text-text-muted">Evidence strength</p>
      <p className="mt-0.5 text-base text-text">
        Evidence: <span className="font-medium">{label}</span>
      </p>

      <CollapsibleSection
        summary={isLimited ? 'Why is the evidence limited?' : 'How is evidence strength measured?'}
      >
        <p className="max-w-xl text-sm leading-relaxed text-text-secondary">
          Evidence strength reflects how much playing time the selected eleven has on record this
          season. It does not indicate a weak recommendation — this plan is still the recommended
          course of action.
        </p>

        <ul className="max-w-xl list-inside list-disc space-y-1 text-sm text-text-secondary">
          {factors.map((factor) => (
            <li key={factor}>{factor}</li>
          ))}
        </ul>

        <p className="max-w-xl text-sm leading-relaxed text-text-muted">
          Evidence strengthens as players accumulate minutes through the season.
        </p>
      </CollapsibleSection>
    </div>
  )
}
