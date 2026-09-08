import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makePlayer } from '../test/fixtures'
import { CaptainSection } from './CaptainSection'

describe('CaptainSection', () => {
  it('shows expected points and captaincy score as two distinct lines for captain and vice', () => {
    const captain = makePlayer({
      web_name: 'Cherki',
      expected_points: 10.31,
      captaincy_score: 8.65,
      effective_points: 20.62,
    })
    const viceCaptain = makePlayer({
      web_name: 'Haaland',
      expected_points: 8.25,
      captaincy_score: 7.35,
      effective_points: 8.25,
    })

    render(<CaptainSection captain={captain} viceCaptain={viceCaptain} />)

    expect(screen.getByText('Cherki')).toBeInTheDocument()
    expect(screen.getByText(/10\.31 expected points/)).toBeInTheDocument()
    expect(screen.getByText(/8\.65 captaincy score/)).toBeInTheDocument()

    expect(screen.getByText('Haaland')).toBeInTheDocument()
    expect(screen.getByText(/8\.25 expected points/)).toBeInTheDocument()
    expect(screen.getByText(/7\.35 captaincy score/)).toBeInTheDocument()
  })

  it('shows the captain\'s effective (2x) points as its own distinct line, from the backend value directly', () => {
    const captain = makePlayer({
      web_name: 'Cherki',
      expected_points: 10.31,
      effective_points: 20.62,
    })
    const viceCaptain = makePlayer({ web_name: 'Haaland', expected_points: 8.25, effective_points: 8.25 })

    render(<CaptainSection captain={captain} viceCaptain={viceCaptain} />)

    expect(screen.getByText(/20\.62 effective points \(2x\)/)).toBeInTheDocument()
  })

  it('does not show an effective-points line for the vice-captain, since the multiplier never applies to them', () => {
    const captain = makePlayer({ web_name: 'Cherki', expected_points: 10.31, effective_points: 20.62 })
    const viceCaptain = makePlayer({ web_name: 'Haaland', expected_points: 8.25, effective_points: 8.25 })

    render(<CaptainSection captain={captain} viceCaptain={viceCaptain} />)

    expect(screen.queryAllByText(/effective points/i)).toHaveLength(1)
  })

  it('never recomputes effective_points in the frontend - it renders exactly what the backend returned', () => {
    // A deliberately "wrong" effective_points (not literally 2x
    // expected_points) proves the component displays the backend
    // value verbatim rather than deriving its own.
    const captain = makePlayer({ web_name: 'Cherki', expected_points: 10.31, effective_points: 999.99 })
    const viceCaptain = makePlayer({ web_name: 'Haaland', expected_points: 8.25, effective_points: 8.25 })

    render(<CaptainSection captain={captain} viceCaptain={viceCaptain} />)

    expect(screen.getByText(/999\.99 effective points \(2x\)/)).toBeInTheDocument()
  })
})
