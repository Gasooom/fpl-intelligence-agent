import type { PlayerDecisionResponse } from '../api/types'
import { PlayerRow } from './PlayerRow'

interface BenchProps {
  players: PlayerDecisionResponse[]
}

/**
 * Visually subordinate to Starting XI: a smaller, muted heading and
 * muted rows - same fields, lower priority. Renders in the order the
 * backend returns it (substitute priority); 0-4 players, an empty or
 * short bench is a valid state.
 */
export function Bench({ players }: BenchProps) {
  return (
    <section className="border-t border-border pt-6 first:border-t-0 first:pt-0">
      <h2 className="text-sm font-medium text-text-secondary">
        Bench <span className="text-text-muted">({players.length})</span>
      </h2>
      {players.length === 0 ? (
        <p className="mt-3 text-sm text-text-muted">No bench players returned.</p>
      ) : (
        <div className="mt-3">
          {players.map((player, index) => (
            <PlayerRow
              key={player.player_id}
              name={player.web_name}
              expectedPoints={player.expected_points}
              riskLevel={player.risk_level}
              marker={`Sub ${index + 1}`}
              muted
            />
          ))}
        </div>
      )}
    </section>
  )
}
