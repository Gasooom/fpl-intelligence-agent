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

  function handleSubmit(
    newEntryId: number,
    newGameweek: number | null,
    newFreeTransfers: number | null,
  ) {
    setEntryId(newEntryId)
    setGameweek(newGameweek)
    setFreeTransfers(newFreeTransfers)
  }

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
            />
          </Panel>

          {evaluationQuery.data && (
            <PlayerPredictions
              startingXiPlayers={evaluationQuery.data.starting_xi_players}
              benchPlayers={evaluationQuery.data.bench_players}
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
