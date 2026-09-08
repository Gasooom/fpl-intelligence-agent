import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makePlayerEvaluation, makeSquadPlayerEvaluations } from '../test/fixtures'
import { PlayerPredictions } from './PlayerPredictions'

describe('PlayerPredictions', () => {
  it('renders every player in the recorded squad', () => {
    const { startingXi, bench } = makeSquadPlayerEvaluations()

    render(<PlayerPredictions startingXiPlayers={startingXi} benchPlayers={bench} />)

    for (const player of [...startingXi, ...bench]) {
      expect(screen.getByText(player.web_name)).toBeInTheDocument()
    }
    expect(startingXi).toHaveLength(11)
    expect(bench).toHaveLength(4)
  })

  it('labels the Expected, Actual, and Difference columns', () => {
    const { startingXi, bench } = makeSquadPlayerEvaluations()

    render(<PlayerPredictions startingXiPlayers={startingXi} benchPlayers={bench} />)

    expect(screen.getByText('Player')).toBeInTheDocument()
    expect(screen.getAllByText('Expected').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Actual').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Difference').length).toBeGreaterThan(0)
  })

  it('shows expected, actual, and difference for one player from backend values', () => {
    const player = makePlayerEvaluation({
      web_name: 'Cherki',
      expected_points: 10.31,
      actual_points: 12,
      prediction_error: 1.69,
    })

    render(<PlayerPredictions startingXiPlayers={[player]} benchPlayers={[]} />)

    expect(screen.getByText('Cherki')).toBeInTheDocument()
    expect(screen.getByText('10.31')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('+1.69')).toBeInTheDocument()
  })

  it('colors a positive difference and a negative difference differently', () => {
    const over = makePlayerEvaluation({
      player_id: 1,
      web_name: 'Over',
      expected_points: 1.71,
      actual_points: 5,
      prediction_error: 3.29,
    })
    const under = makePlayerEvaluation({
      player_id: 2,
      web_name: 'Under',
      expected_points: 1.71,
      actual_points: 1,
      prediction_error: -0.71,
    })

    render(<PlayerPredictions startingXiPlayers={[over, under]} benchPlayers={[]} />)

    expect(screen.getByText('+3.29').className).toContain('eval-positive')
    expect(screen.getByText('-0.71').className).toContain('eval-negative')
  })

  it('renders a zero difference neutrally, with no outcome color', () => {
    const exact = makePlayerEvaluation({
      web_name: 'Exact',
      expected_points: 6,
      actual_points: 6,
      prediction_error: 0,
    })

    render(<PlayerPredictions startingXiPlayers={[exact]} benchPlayers={[]} />)

    const difference = screen.getByText('0.00')
    expect(difference).toBeInTheDocument()
    expect(difference.className).not.toMatch(/eval-(positive|negative)/)
  })

  it('groups the starting XI by position in the order the backend recorded', () => {
    const { startingXi } = makeSquadPlayerEvaluations()

    const { container } = render(
      <PlayerPredictions startingXiPlayers={startingXi} benchPlayers={[]} />,
    )

    const text = container.textContent ?? ''
    expect(text.indexOf('GK')).toBeLessThan(text.indexOf('DEF'))
    expect(text.indexOf('DEF')).toBeLessThan(text.indexOf('MID'))
    expect(text.indexOf('MID')).toBeLessThan(text.indexOf('FWD'))
  })

  it('never reorders players by what they scored', () => {
    const players = [
      makePlayerEvaluation({ player_id: 1, web_name: 'First', position_type: 1, actual_points: 0 }),
      makePlayerEvaluation({ player_id: 2, web_name: 'Second', position_type: 2, actual_points: 20 }),
      makePlayerEvaluation({ player_id: 3, web_name: 'Third', position_type: 2, actual_points: 2 }),
    ]

    const { container } = render(
      <PlayerPredictions startingXiPlayers={players} benchPlayers={[]} />,
    )

    const text = container.textContent ?? ''
    expect(text.indexOf('First')).toBeLessThan(text.indexOf('Second'))
    expect(text.indexOf('Second')).toBeLessThan(text.indexOf('Third'))
  })

  it('separates the bench from the starting XI', () => {
    const { startingXi, bench } = makeSquadPlayerEvaluations()

    render(<PlayerPredictions startingXiPlayers={startingXi} benchPlayers={bench} />)

    expect(screen.getByText('Starting XI')).toBeInTheDocument()
    expect(screen.getByText('Bench')).toBeInTheDocument()
  })

  it('renders nothing when the gameweek has not been evaluated', () => {
    const { container } = render(
      <PlayerPredictions startingXiPlayers={[]} benchPlayers={[]} />,
    )

    expect(container).toBeEmptyDOMElement()
  })
})
