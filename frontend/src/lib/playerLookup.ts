import type { GameweekDecisionResponse } from '../api/types'

/**
 * Resolves evidence.player_id -> web_name using player data already
 * present in the same GameweekDecisionResponse - starting_xi, bench,
 * captain, vice_captain, sell_candidates, buy_candidates, and the
 * sell/buy sides embedded in transfer_recommendations/best_transfer.
 * This is cross-referencing data the backend already returned, not a
 * new data source: no extra endpoint is called and no name is ever
 * invented.
 *
 * The transfer_recommendations/best_transfer sources matter in
 * practice, confirmed against live data: the backend ranks a
 * transfer's buy side within that sell candidate's specific position
 * (rank_buy_candidates(..., position_type=sell.position_type)), while
 * the top-level buy_candidates list is the overall top 10 across all
 * positions - so a real buy target can legitimately be absent from
 * buy_candidates while still appearing in a transfer pair. Without
 * this source, that player's evidence entry would fall back to
 * "Player #{id}" even though the backend did return its name, just in
 * a different part of the same response.
 *
 * Still a Map, not a guarantee - callers must handle a miss via
 * resolvePlayerName's fallback rather than assume every id resolves.
 */
export function buildPlayerNameLookup(decision: GameweekDecisionResponse): Map<number, string> {
  const lookup = new Map<number, string>()

  const addAll = (players: { player_id: number; web_name: string }[]) => {
    for (const player of players) {
      if (!lookup.has(player.player_id)) {
        lookup.set(player.player_id, player.web_name)
      }
    }
  }

  addAll(decision.starting_xi)
  addAll(decision.bench)
  addAll([decision.captain, decision.vice_captain])
  addAll(decision.sell_candidates)
  addAll(decision.buy_candidates)

  for (const pair of decision.transfer_recommendations) {
    addAll([pair.sell, pair.buy])
  }
  if (decision.best_transfer) {
    addAll([decision.best_transfer.sell, decision.best_transfer.buy])
  }

  return lookup
}

/** Defensive fallback for an id not present anywhere in the response -
 * never fabricates a name, just names the id honestly. */
export function resolvePlayerName(lookup: Map<number, string>, playerId: number): string {
  return lookup.get(playerId) ?? `Player #${playerId}`
}
