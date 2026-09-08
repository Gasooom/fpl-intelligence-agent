import type { PlayerEvaluationResponse } from '../api/types'
import { formatPoints, formatSigned, positionLabel, signToneClass } from '../lib/format'
import { Panel } from './Panel'

interface PlayerPredictionsProps {
  startingXiPlayers: PlayerEvaluationResponse[]
  benchPlayers: PlayerEvaluationResponse[]
  /** The gameweek these rows belong to, straight from the evaluation
   * they came from - so a table showing a previous gameweek's results
   * can never be mistaken for the current one. */
  gameweek?: number
}

function ColumnHeadings() {
  return (
    <div className="hidden grid-cols-[1fr_auto_auto_auto] gap-x-6 border-b border-border pb-2 text-xs text-text-muted sm:grid">
      <span>Player</span>
      <span className="w-20 text-right">Expected</span>
      <span className="w-16 text-right">Actual</span>
      <span className="w-20 text-right">Difference</span>
    </div>
  )
}

/**
 * One player per row. On a wide screen the three figures line up in
 * their own columns under shared headings; on a narrow one each figure
 * keeps an inline label instead, so the row still reads without a
 * horizontal scrollbar.
 */
function PredictionRow({ player }: { player: PlayerEvaluationResponse }) {
  return (
    <div className="grid grid-cols-[1fr_auto] items-baseline gap-x-6 gap-y-1 border-b border-border py-2.5 last:border-b-0 sm:grid-cols-[1fr_auto_auto_auto]">
      <span className="text-sm text-text">{player.web_name}</span>

      <span className="col-start-2 row-start-2 text-xs text-text-muted sm:row-start-1 sm:w-20 sm:text-right">
        <span className="sm:hidden">Expected </span>
        {formatPoints(player.expected_points)}
      </span>

      <span className="col-start-2 row-start-3 text-xs text-text-secondary sm:col-start-3 sm:row-start-1 sm:w-16 sm:text-right">
        <span className="sm:hidden">Actual </span>
        {player.actual_points}
      </span>

      <span
        className={`col-start-2 row-start-4 text-xs sm:col-start-4 sm:row-start-1 sm:w-20 sm:text-right ${signToneClass(
          player.prediction_error,
        )}`}
      >
        <span className="text-text-muted sm:hidden">Difference </span>
        {formatSigned(player.prediction_error)}
      </span>
    </div>
  )
}

function PositionGroup({ players }: { players: PlayerEvaluationResponse[] }) {
  return (
    <div>
      <p className="text-xs text-text-muted">{positionLabel(players[0].position_type)}</p>
      <div className="mt-1">
        {players.map((player) => (
          <PredictionRow key={player.player_id} player={player} />
        ))}
      </div>
    </div>
  )
}

/** Groups consecutive players by the position the snapshot recorded,
 * exactly as StartingXI does for the plan above - the order is the
 * backend's, never re-sorted by score or error. */
function groupByPosition(
  players: PlayerEvaluationResponse[],
): PlayerEvaluationResponse[][] {
  const groups: PlayerEvaluationResponse[][] = []

  for (const player of players) {
    const current = groups.at(-1)
    if (current && current[0].position_type === player.position_type) {
      current.push(player)
    } else {
      groups.push([player])
    }
  }

  return groups
}

/**
 * Every player the system predicted, measured one by one against what
 * he actually scored. This is the closed loop made concrete: expected
 * came from the decision snapshot, actual came from the official FPL
 * results, and the difference between them was computed by the
 * backend. Nothing on this screen is derived in the browser.
 */
export function PlayerPredictions({
  startingXiPlayers,
  benchPlayers,
  gameweek,
}: PlayerPredictionsProps) {
  if (startingXiPlayers.length === 0 && benchPlayers.length === 0) {
    return null
  }

  return (
    <Panel>
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-base font-medium text-text">Player predictions</h2>
        {gameweek !== undefined && (
          <span className="text-xs text-text-muted">Gameweek {gameweek}</span>
        )}
      </div>
      <p className="mt-1 text-sm text-text-muted">
        Expected vs actual points for the squad.
      </p>

      {startingXiPlayers.length > 0 && (
        <div className="mt-5">
          <p className="text-sm font-medium text-text">Starting XI</p>
          <div className="mt-3">
            <ColumnHeadings />
            <div className="mt-2 flex flex-col gap-4">
              {groupByPosition(startingXiPlayers).map((group) => (
                <PositionGroup key={group[0].player_id} players={group} />
              ))}
            </div>
          </div>
        </div>
      )}

      {benchPlayers.length > 0 && (
        <div className="mt-7 border-t border-border pt-5">
          <p className="text-sm font-medium text-text-secondary">Bench</p>
          <div className="mt-3">
            {benchPlayers.map((player) => (
              <PredictionRow key={player.player_id} player={player} />
            ))}
          </div>
        </div>
      )}
    </Panel>
  )
}
