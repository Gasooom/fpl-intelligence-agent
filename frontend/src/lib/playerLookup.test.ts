import { describe, expect, it } from 'vitest'
import { makeBuyCandidate, makeGameweekDecision, makeSellCandidate, makeTransferPair } from '../test/fixtures'
import { buildPlayerNameLookup, resolvePlayerName } from './playerLookup'

describe('buildPlayerNameLookup / resolvePlayerName', () => {
  it('resolves a player_id that appears in starting_xi', () => {
    const decision = makeGameweekDecision()
    const lookup = buildPlayerNameLookup(decision)

    // player_id 11 is the captain, also fixture default's first starting_xi id used elsewhere
    expect(resolvePlayerName(lookup, decision.captain.player_id)).toBe(decision.captain.web_name)
  })

  it('resolves a player_id that only appears in sell_candidates', () => {
    const decision = makeGameweekDecision()
    const sellId = decision.sell_candidates[0].player_id
    const lookup = buildPlayerNameLookup(decision)

    expect(resolvePlayerName(lookup, sellId)).toBe(decision.sell_candidates[0].web_name)
  })

  it('resolves a player_id that only appears in buy_candidates', () => {
    const decision = makeGameweekDecision()
    const buyId = decision.buy_candidates[0].player_id
    const lookup = buildPlayerNameLookup(decision)

    expect(resolvePlayerName(lookup, buyId)).toBe(decision.buy_candidates[0].web_name)
  })

  it('resolves a player_id only present as a transfer pair buy side, not in buy_candidates', () => {
    // Real case confirmed against live data: the backend ranks a
    // transfer's buy side within the sell candidate's own position,
    // while buy_candidates is only the overall top 10 across all
    // positions - so a real buy target can be absent from
    // buy_candidates while still appearing in transfer_recommendations.
    const offListBuy = makeBuyCandidate({ player_id: 125, web_name: 'Georginio' })
    const pair = makeTransferPair({
      sell: makeSellCandidate({ player_id: 491, web_name: 'Igor Jesus' }),
      buy: offListBuy,
    })
    const decision = makeGameweekDecision({
      buy_candidates: [makeBuyCandidate({ player_id: 21, web_name: 'Strong Target' })],
      transfer_recommendations: [pair],
      best_transfer: null,
    })

    const lookup = buildPlayerNameLookup(decision)

    expect(resolvePlayerName(lookup, 125)).toBe('Georginio')
  })

  it('resolves a player_id only present as best_transfer.sell/.buy', () => {
    const pair = makeTransferPair({
      sell: makeSellCandidate({ player_id: 500, web_name: 'Only In Best Transfer Sell' }),
      buy: makeBuyCandidate({ player_id: 501, web_name: 'Only In Best Transfer Buy' }),
    })
    const decision = makeGameweekDecision({
      sell_candidates: [],
      buy_candidates: [],
      transfer_recommendations: [],
      best_transfer: pair,
    })

    const lookup = buildPlayerNameLookup(decision)

    expect(resolvePlayerName(lookup, 500)).toBe('Only In Best Transfer Sell')
    expect(resolvePlayerName(lookup, 501)).toBe('Only In Best Transfer Buy')
  })

  it('falls back to "Player #{id}" for an id not present anywhere in the response', () => {
    const decision = makeGameweekDecision()
    const lookup = buildPlayerNameLookup(decision)

    expect(resolvePlayerName(lookup, 999999)).toBe('Player #999999')
  })

  it('does not fabricate a name - the fallback never reuses an unrelated name', () => {
    const decision = makeGameweekDecision()
    const lookup = buildPlayerNameLookup(decision)
    const unknownId = 424242

    const resolved = resolvePlayerName(lookup, unknownId)

    expect(resolved).not.toBe(decision.captain.web_name)
    expect(resolved).toContain(String(unknownId))
  })
})
