import { useQuery } from '@tanstack/react-query'
import { getGameweekDecision } from '../api/client'

/**
 * Fetches the unified gameweek decision for one FPL entry.
 *
 * Query key is [entryId, gameweek] so different entries/gameweeks are
 * cached independently, and changing either re-triggers the fetch.
 * Disabled until a valid entryId is supplied (initial state).
 */
export function useGameweekDecision(
  entryId: number | null,
  gameweek: number | null,
  freeTransfers: number | null,
) {
  return useQuery({
    queryKey: ['gameweek-decision', entryId, gameweek, freeTransfers],
    queryFn: () => {
      if (entryId === null) {
        // Guarded by `enabled` below; queryFn only runs with a valid id.
        throw new Error('entryId is required')
      }
      return getGameweekDecision(
        entryId,
        gameweek ?? undefined,
        freeTransfers ?? undefined,
      )
    },
    enabled: entryId !== null,
    retry: false,
  })
}
