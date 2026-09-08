import { useMemo, useState } from 'react'
import { Bench } from './components/Bench'
import { CandidatePools } from './components/CandidatePools'
import { CaptainSection } from './components/CaptainSection'
import { EmptyState } from './components/EmptyState'
import { EntryForm } from './components/EntryForm'
import { ErrorBanner } from './components/ErrorBanner'
import { Evaluation } from './components/Evaluation'
import { EvidenceSummary } from './components/EvidenceSummary'
import { Header } from './components/Header'
import { LoadingState } from './components/LoadingState'
import { OtherTransferOptions } from './components/OtherTransferOptions'
import { Panel } from './components/Panel'
import { PlayerPredictions } from './components/PlayerPredictions'
import { PrimaryDecision } from './components/PrimaryDecision'
import { StartingXI } from './components/StartingXI'
import { WhyThisDecision } from './components/WhyThisDecision'
import { useGameweekDecision } from './hooks/useGameweekDecision'
import { useGameweekEvaluation } from './hooks/useGameweekEvaluation'
import { useLatestCompletedEvaluation } from './hooks/useLatestCompletedEvaluation'
import { buildPlayerNameLookup } from './lib/playerLookup'

function App() {
  const [entryId, setEntryId] = useState<number | null>(null)
  const [gameweek, setGameweek] = useState<number | null>(null)
  const [freeTransfers, setFreeTransfers] = useState<number | null>(null)

  const query = useGameweekDecision(entryId, gameweek, freeTransfers)
  const decision = query.data

  // Evaluated against the gameweek the decision actually resolved to,
  // not the (possibly blank) one typed into the form, so both halves
  // of the page always describe the same gameweek.
  const evaluationQuery = useGameweekEvaluation(entryId, decision?.gameweek ?? null)

  // Independent of the resolved gameweek above: the backend decides on
  // its own which completed gameweek (if any) this refers to, so the
  // dashboard can showcase evaluation even while the current gameweek
  // is still pending.
  const latestCompletedQuery = useLatestCompletedEvaluation(entryId)

  function handleSubmit(
    newEntryId: number,
    newGameweek: number | null,
    newFreeTransfers: number | null,
  ) {
    setEntryId(newEntryId)
    setGameweek(newGameweek)
    setFreeTransfers(newFreeTransfers)
  }

  // The player-by-player table follows whichever evaluation actually
  // has results: this gameweek's once it has been played, otherwise the
  // latest completed one the backend already identified. Both payloads
  // arrive fully computed - nothing here re-derives a player's figures,
  // and neither one is shown unless the backend returned real rows.
  const currentEvaluation = evaluationQuery.data
  const hasCurrentPlayerResults =
    currentEvaluation !== undefined &&
    (currentEvaluation.starting_xi_players.length > 0 ||
      currentEvaluation.bench_players.length > 0)
  const playerEvaluation = hasCurrentPlayerResults
    ? currentEvaluation
    : (latestCompletedQuery.data?.evaluation ?? undefined)

  const nameLookup = useMemo(
    () => (decision ? buildPlayerNameLookup(decision) : new Map<number, string>()),
    [decision],
  )
  const mustPlayIds = useMemo(
    () => new Set((decision?.must_play ?? []).map((player) => player.player_id)),
    [decision],
  )

  return (
    <div className="mx-auto flex max-w-3xl flex-col px-5 py-8 sm:px-6">
      <Header />

      <EntryForm onSubmit={handleSubmit} isFetching={query.isFetching} />

      {entryId === null && <EmptyState />}

      {query.isFetching && <LoadingState />}

      {query.isError && !query.isFetching && <ErrorBanner error={query.error} />}

      {decision && !query.isFetching && !query.isError && (
        <div className="flex flex-col gap-4">
          <Panel>
            <PrimaryDecision
              gameweek={decision.gameweek}
              captain={decision.captain}
              viceCaptain={decision.vice_captain}
              bestTransfer={decision.best_transfer}
              confidence={decision.confidence}
              evidenceBasis={decision.evidence_basis}
              projectedGameweekPoints={decision.projected_gameweek_points}
              summary={decision.decision_summary}
              freeTransfersAvailable={decision.free_transfers_available}
              inTheBank={decision.in_the_bank}
            />
          </Panel>

          <WhyThisDecision bestTransfer={decision.best_transfer} />

          <Panel>
            <CaptainSection captain={decision.captain} viceCaptain={decision.vice_captain} />
            <StartingXI
              players={decision.starting_xi}
              captainId={decision.captain.player_id}
              viceCaptainId={decision.vice_captain.player_id}
              mustPlayIds={mustPlayIds}
              startingXiExpectedPoints={decision.starting_xi_expected_points}
              projectedGameweekPoints={decision.projected_gameweek_points}
              captainExpectedPoints={decision.captain.expected_points}
            />
            <Bench players={decision.bench} />
          </Panel>

          <OtherTransferOptions
            transferRecommendations={decision.transfer_recommendations}
            bestTransfer={decision.best_transfer}
            freeTransfersAvailable={decision.free_transfers_available}
          />

          <Panel emphasized>
            <Evaluation
              evaluation={evaluationQuery.data}
              isFetching={evaluationQuery.isFetching}
              error={evaluationQuery.isError ? evaluationQuery.error : null}
              latestCompleted={latestCompletedQuery.data}
              latestCompletedFetching={latestCompletedQuery.isFetching}
              latestCompletedError={latestCompletedQuery.isError ? latestCompletedQuery.error : null}
            />
          </Panel>

          {playerEvaluation && (
            <PlayerPredictions
              startingXiPlayers={playerEvaluation.starting_xi_players}
              benchPlayers={playerEvaluation.bench_players}
              gameweek={playerEvaluation.gameweek}
            />
          )}

          <EvidenceSummary
            evidence={decision.evidence}
            nameLookup={nameLookup}
            captainId={decision.captain.player_id}
            viceCaptainId={decision.vice_captain.player_id}
            bestTransfer={decision.best_transfer}
          />

          <CandidatePools
            sellCandidates={decision.sell_candidates}
            buyCandidates={decision.buy_candidates}
          />
        </div>
      )}
    </div>
  )
}

export default App
