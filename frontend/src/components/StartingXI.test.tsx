import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makePlayer } from '../test/fixtures'
import { StartingXI } from './StartingXI'

const projectedTotals = {
  startingXiExpectedPoints: 47.7,
  projectedGameweekPoints: 54.87,
  captainExpectedPoints: 7.17,
}

describe('StartingXI', () => {
  it('groups players by position_type as returned, without reordering', () => {
    const players = [
      makePlayer({ player_id: 1, web_name: 'GK One', position_type: 1 }),
      makePlayer({ player_id: 2, web_name: 'Def One', position_type: 2 }),
      makePlayer({ player_id: 3, web_name: 'Def Two', position_type: 2 }),
    ]

    const { container } = render(
      <StartingXI
        players={players}
        captainId={-1}
        viceCaptainId={-1}
        mustPlayIds={new Set()}
        {...projectedTotals}
      />,
    )

    expect(screen.getByText('GK')).toBeInTheDocument()
    expect(screen.getByText('DEF')).toBeInTheDocument()
    const text = container.textContent ?? ''
    expect(text.indexOf('GK One')).toBeLessThan(text.indexOf('Def One'))
    expect(text.indexOf('Def One')).toBeLessThan(text.indexOf('Def Two'))
  })

  it('marks the captain, vice-captain, and must-play players subtly', () => {
    const players = [
      makePlayer({ player_id: 1, web_name: 'Cherki', position_type: 3 }),
      makePlayer({ player_id: 2, web_name: 'Haaland', position_type: 4 }),
      makePlayer({ player_id: 3, web_name: 'Gakpo', position_type: 3 }),
    ]

    render(
      <StartingXI
        players={players}
        captainId={1}
        viceCaptainId={2}
        mustPlayIds={new Set([3])}
        {...projectedTotals}
      />,
    )

    expect(screen.getByText('Captain')).toBeInTheDocument()
    expect(screen.getByText('Vice-captain')).toBeInTheDocument()
    expect(screen.getByText('Must play')).toBeInTheDocument()
  })

  it('does not mark a player who is neither captain, vice, nor must-play', () => {
    const players = [makePlayer({ player_id: 9, web_name: 'Plain Player', position_type: 3 })]

    render(
      <StartingXI
        players={players}
        captainId={1}
        viceCaptainId={2}
        mustPlayIds={new Set()}
        {...projectedTotals}
      />,
    )

    expect(screen.queryByText('Captain')).not.toBeInTheDocument()
    expect(screen.queryByText('Vice-captain')).not.toBeInTheDocument()
    expect(screen.queryByText('Must play')).not.toBeInTheDocument()
  })

  // --- Projected Gameweek total (F, G, H, I) ---

  it('shows the XI expected subtotal, captain bonus, and projected total from backend values', () => {
    const players = [makePlayer({ player_id: 1, web_name: 'Player One' })]

    render(
      <StartingXI
        players={players}
        captainId={-1}
        viceCaptainId={-1}
        mustPlayIds={new Set()}
        {...projectedTotals}
      />,
    )

    expect(screen.getByText('XI expected:')).toBeInTheDocument()
    expect(screen.getByText('47.70')).toBeInTheDocument()
    expect(screen.getByText('Captain bonus:')).toBeInTheDocument()
    expect(screen.getByText('+7.17')).toBeInTheDocument()
    expect(screen.getByText(/Projected total: 54\.87 expected points/)).toBeInTheDocument()
  })

  it('matches the worked example from the spec exactly', () => {
    // Raya, Kayode, Gabriel, Virgil, Cash, Cherki, Mbeumo, Neto,
    // Armstrong, João Pedro, Haaland -> XI 47.70, captain 7.17 -> 54.87.
    render(
      <StartingXI
        players={[makePlayer()]}
        captainId={-1}
        viceCaptainId={-1}
        mustPlayIds={new Set()}
        startingXiExpectedPoints={47.7}
        projectedGameweekPoints={54.87}
        captainExpectedPoints={7.17}
      />,
    )

    expect(screen.getByText('47.70')).toBeInTheDocument()
    expect(screen.getByText('+7.17')).toBeInTheDocument()
    expect(screen.getByText(/54\.87 expected points/)).toBeInTheDocument()
  })

  it('never recomputes the totals - it renders exactly the backend-supplied numbers', () => {
    // A deliberately inconsistent captain bonus (not actually
    // projected - XI) proves the component displays the prop as
    // given rather than deriving it by subtraction.
    render(
      <StartingXI
        players={[makePlayer()]}
        captainId={-1}
        viceCaptainId={-1}
        mustPlayIds={new Set()}
        startingXiExpectedPoints={47.7}
        projectedGameweekPoints={54.87}
        captainExpectedPoints={999.99}
      />,
    )

    expect(screen.getByText('+999.99')).toBeInTheDocument()
  })
})
