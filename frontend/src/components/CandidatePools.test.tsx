import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makeBuyCandidate, makeSellCandidate } from '../test/fixtures'
import { CandidatePools } from './CandidatePools'

describe('CandidatePools', () => {
  it('shows all candidates as a numbered list with no expand control when there are 3 or fewer', () => {
    const candidates = [
      makeSellCandidate({ player_id: 1, web_name: 'A' }),
      makeSellCandidate({ player_id: 2, web_name: 'B' }),
    ]
    render(<CandidatePools sellCandidates={candidates} buyCandidates={[]} />)

    expect(screen.getByText('1. A')).toBeInTheDocument()
    expect(screen.getByText('2. B')).toBeInTheDocument()
    expect(screen.queryByText(/show all/i)).not.toBeInTheDocument()
  })

  it('shows the top 3 sell candidates by default, numbered, with the rest behind "Show all N", in backend order', () => {
    const candidates = [1, 2, 3, 4, 5].map((n) =>
      makeSellCandidate({ player_id: n, web_name: `Player ${n}`, rank: n }),
    )
    const { container } = render(<CandidatePools sellCandidates={candidates} buyCandidates={[]} />)

    expect(screen.getByText('Show all 5')).toBeInTheDocument()
    expect(screen.getByText('4. Player 4')).toBeInTheDocument()
    expect(screen.getByText('5. Player 5')).toBeInTheDocument()
    const text = container.textContent ?? ''
    expect(text.indexOf('Player 1')).toBeLessThan(text.indexOf('Player 2'))
    expect(text.indexOf('Player 4')).toBeLessThan(text.indexOf('Player 5'))
  })

  it('shows a deliberate empty state for empty sell and buy candidate pools', () => {
    render(<CandidatePools sellCandidates={[]} buyCandidates={[]} />)

    expect(screen.getAllByText(/none returned/i)).toHaveLength(2)
  })

  it('keeps sell and buy candidate expansion independent of each other', () => {
    const sell = [1, 2, 3, 4].map((n) => makeSellCandidate({ player_id: n, web_name: `Sell ${n}` }))
    const buy = [1, 2].map((n) => makeBuyCandidate({ player_id: n + 100, web_name: `Buy ${n}` }))

    render(<CandidatePools sellCandidates={sell} buyCandidates={buy} />)

    expect(screen.getByText('Show all 4')).toBeInTheDocument()
    expect(screen.queryByText('Show all 2')).not.toBeInTheDocument()
    expect(screen.getByText('1. Buy 1')).toBeInTheDocument()
    expect(screen.getByText('2. Buy 2')).toBeInTheDocument()
  })

  it('does not repeat a "best transfer" headline - this section is the raw pools only', () => {
    render(
      <CandidatePools
        sellCandidates={[makeSellCandidate({ web_name: 'Neto' })]}
        buyCandidates={[makeBuyCandidate({ web_name: 'Gakpo' })]}
      />,
    )

    expect(screen.queryByText(/best transfer/i)).not.toBeInTheDocument()
  })
})
