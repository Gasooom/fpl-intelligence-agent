import type { BuyCandidateResponse, SellCandidateResponse } from '../api/types'
import { formatPoints, riskTextClass } from '../lib/format'
import { CollapsibleSection } from './CollapsibleSection'

const VISIBLE_COUNT = 3

interface CandidatePoolsProps {
  sellCandidates: SellCandidateResponse[]
  buyCandidates: BuyCandidateResponse[]
}

function CandidateRow({ rank, candidate }: { rank: number; candidate: SellCandidateResponse | BuyCandidateResponse }) {
  return (
    <li className="flex items-baseline justify-between gap-3 text-sm">
      <span className="text-text-secondary">
        {rank}. {candidate.web_name}
      </span>
      <span className="whitespace-nowrap text-right text-xs text-text-muted">
        {formatPoints(candidate.expected_points)} expected points ·{' '}
        <span className={riskTextClass(candidate.risk_level)}>{candidate.risk_level} risk</span>
      </span>
    </li>
  )
}

function CandidateColumn({
  title,
  candidates,
}: {
  title: string
  candidates: (SellCandidateResponse | BuyCandidateResponse)[]
}) {
  const visible = candidates.slice(0, VISIBLE_COUNT)
  const rest = candidates.slice(VISIBLE_COUNT)

  return (
    <div>
      <p className="text-xs text-text-muted">
        {title} <span>({candidates.length})</span>
      </p>
      {candidates.length === 0 ? (
        <p className="mt-2 text-sm text-text-muted">None returned.</p>
      ) : (
        <>
          <ol className="mt-2 flex flex-col gap-1.5">
            {visible.map((candidate, index) => (
              <CandidateRow key={candidate.player_id} rank={index + 1} candidate={candidate} />
            ))}
          </ol>
          {rest.length > 0 && (
            <CollapsibleSection summary={`Show all ${candidates.length}`}>
              <ol className="flex flex-col gap-1.5">
                {rest.map((candidate, index) => (
                  <CandidateRow key={candidate.player_id} rank={VISIBLE_COUNT + index + 1} candidate={candidate} />
                ))}
              </ol>
            </CollapsibleSection>
          )}
        </>
      )}
    </div>
  )
}

/**
 * The full sell/buy candidate pools the optimizer considered, as
 * numbered lists in the backend's own rank order - evidence of the
 * system's depth, kept behind the recommendation rather than
 * competing with it, which is why this sits at the very end of the
 * page. The best transfer itself is not repeated here (it's already
 * named in the hero, Why this decision, and the evidence above) - this
 * section is purely the raw pools.
 */
export function CandidatePools({ sellCandidates, buyCandidates }: CandidatePoolsProps) {
  return (
    <section className="border-t border-border px-5 py-7 sm:px-6">
      <h2 className="text-base font-medium text-text">Full candidate pools</h2>
      <div className="mt-4 grid grid-cols-1 gap-6 sm:grid-cols-2">
        <CandidateColumn title="Sell" candidates={sellCandidates} />
        <CandidateColumn title="Buy" candidates={buyCandidates} />
      </div>
    </section>
  )
}
