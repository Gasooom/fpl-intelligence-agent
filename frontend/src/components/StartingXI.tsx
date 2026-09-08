import type { PlayerDecisionResponse } from '../api/types'
import { formatPoints, positionLabel } from '../lib/format'
import { PlayerRow } from './PlayerRow'

interface StartingXIProps {
  players: PlayerDecisionResponse[]
  captainId: number
  viceCaptainId: number
  /** must_play, folded in here as a subtle per-player marker rather
   * than a separate section - it's most useful in context, and is
   * often empty (nothing to show as its own heading). */
  mustPlayIds: Set<number>
  /** Backend-computed, mirroring official FPL gameweek scoring - the
   * raw XI subtotal (bench excluded) and that total plus one extra
   * copy of the captain's expected points for the captain multiplier.
   * Never recomputed here from the player list. */
  startingXiExpectedPoints: number
  projectedGameweekPoints: number
  /** The captain's own expected_points, shown as the "bonus" line -
   * passed directly rather than derived by subtracting the two
   * totals above, so nothing here is computed in the browser. */
  captainExpectedPoints: number
}

function markerFor(
  player: PlayerDecisionResponse,
  captainId: number,
  viceCaptainId: number,
  mustPlayIds: Set<number>,
): string | undefined {
  if (player.player_id === captainId) return 'Captain'
  if (player.player_id === viceCaptainId) return 'Vice-captain'
  if (mustPlayIds.has(player.player_id)) return 'Must play'
  return undefined
}

/**
 * Groups by the position_type the backend actually assigned each
 * player - never re-derived or re-optimized here. Players already
 * arrive in goalkeeper -> defender -> midfielder -> forward order, so
 * grouping by encountered position preserves that order. Position is
 * shown once per group heading rather than repeated on every row.
 */
export function StartingXI({
  players,
  captainId,
  viceCaptainId,
  mustPlayIds,
  startingXiExpectedPoints,
  projectedGameweekPoints,
  captainExpectedPoints,
}: StartingXIProps) {
  const groups: { position: number; players: PlayerDecisionResponse[] }[] = []

  for (const player of players) {
    const currentGroup = groups.at(-1)
    if (currentGroup && currentGroup.position === player.position_type) {
      currentGroup.players.push(player)
    } else {
      groups.push({ position: player.position_type, players: [player] })
    }
  }

  return (
    <section className="border-t border-border pt-6 first:border-t-0 first:pt-0">
      <h2 className="text-base font-medium text-text">
        Starting XI <span className="text-text-muted">({players.length})</span>
      </h2>

      {/* Analogous to FPL's own gameweek total: the raw XI subtotal
          (bench excluded) plus one extra copy of the captain's
          expected points for the captain multiplier. Both figures come
          straight from the backend - never recomputed from the player
          rows below. */}
      <div className="mt-3 flex flex-wrap items-baseline gap-x-6 gap-y-1">
        <p className="text-sm text-text-secondary">
          XI expected: <span className="text-text">{formatPoints(startingXiExpectedPoints)}</span>
        </p>
        <p className="text-sm text-text-secondary">
          Captain bonus: <span className="text-text">+{formatPoints(captainExpectedPoints)}</span>
        </p>
        <p className="text-sm font-medium text-text">
          Projected total: {formatPoints(projectedGameweekPoints)} expected points
        </p>
      </div>

      <div className="mt-4 flex flex-col gap-5">
        {groups.map((group) => (
          // The same position_type can recur in non-contiguous groups
          // (players aren't always fully sorted by position), so the
          // position alone isn't a unique key across groups - pair it
          // with the first player's unique id in that group.
          <div key={`${group.position}-${group.players[0].player_id}`}>
            <p className="text-xs text-text-muted">{positionLabel(group.position)}</p>
            <div className="mt-1">
              {group.players.map((player) => (
                <PlayerRow
                  key={player.player_id}
                  name={player.web_name}
                  expectedPoints={player.expected_points}
                  riskLevel={player.risk_level}
                  marker={markerFor(player, captainId, viceCaptainId, mustPlayIds)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
