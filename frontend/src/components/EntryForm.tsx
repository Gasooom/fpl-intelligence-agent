import { useState } from 'react'
import type { FormEvent } from 'react'

interface EntryFormProps {
  onSubmit: (entryId: number, gameweek: number | null, freeTransfers: number | null) => void
  isFetching: boolean
}

export function EntryForm({ onSubmit, isFetching }: EntryFormProps) {
  const [entryIdInput, setEntryIdInput] = useState('')
  const [gameweekInput, setGameweekInput] = useState('')
  const [freeTransfersInput, setFreeTransfersInput] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const entryId = Number(entryIdInput)
    if (!Number.isInteger(entryId) || entryId <= 0) {
      return
    }

    const gameweek = gameweekInput.trim() === '' ? null : Number(gameweekInput)
    if (gameweek !== null && (!Number.isInteger(gameweek) || gameweek <= 0)) {
      return
    }

    // Optional: no public FPL endpoint exposes a manager's free-transfer
    // count, so it can only come from the manager themselves. Left blank,
    // the backend reports transfer economics as unknown rather than
    // assuming a number.
    const freeTransfers = freeTransfersInput.trim() === '' ? null : Number(freeTransfersInput)
    if (freeTransfers !== null && (!Number.isInteger(freeTransfers) || freeTransfers < 0)) {
      return
    }

    onSubmit(entryId, gameweek, freeTransfers)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-5 py-5">
      <div className="flex flex-col gap-1">
        <label htmlFor="entry-id" className="text-xs text-text-muted">
          FPL Entry ID
        </label>
        <input
          id="entry-id"
          type="number"
          min={1}
          required
          placeholder="8731757"
          value={entryIdInput}
          onChange={(event) => setEntryIdInput(event.target.value)}
          className="w-32 border-b border-border-strong bg-transparent py-1 text-sm text-text outline-none focus:border-accent"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="gameweek" className="text-xs text-text-muted">
          Gameweek
        </label>
        <input
          id="gameweek"
          type="number"
          min={1}
          placeholder="current"
          value={gameweekInput}
          onChange={(event) => setGameweekInput(event.target.value)}
          className="w-20 border-b border-border-strong bg-transparent py-1 text-sm text-text outline-none focus:border-accent"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="free-transfers" className="text-xs text-text-muted">
          Free transfers
        </label>
        <input
          id="free-transfers"
          type="number"
          min={0}
          placeholder="unknown"
          value={freeTransfersInput}
          onChange={(event) => setFreeTransfersInput(event.target.value)}
          className="w-24 border-b border-border-strong bg-transparent py-1 text-sm text-text outline-none focus:border-accent"
        />
      </div>

      <button
        type="submit"
        disabled={isFetching}
        className="rounded-md bg-accent px-4 py-1.5 text-sm font-medium text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isFetching ? 'Analyzing…' : 'Analyze'}
      </button>
    </form>
  )
}
