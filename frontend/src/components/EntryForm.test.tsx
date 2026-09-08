import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { EntryForm } from './EntryForm'

describe('EntryForm', () => {
  it('renders the entry ID and gameweek inputs and the submit button', () => {
    render(<EntryForm onSubmit={vi.fn()} isFetching={false} />)

    expect(screen.getByLabelText(/fpl entry id/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/gameweek/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^analyze$/i })).toBeInTheDocument()
  })

  it('calls onSubmit with the entered entry ID and null gameweek when gameweek is omitted', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<EntryForm onSubmit={onSubmit} isFetching={false} />)

    await user.type(screen.getByLabelText(/fpl entry id/i), '8731757')
    await user.click(screen.getByRole('button', { name: /^analyze$/i }))

    expect(onSubmit).toHaveBeenCalledWith(8731757, null, null)
  })

  it('calls onSubmit with a numeric gameweek when supplied', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<EntryForm onSubmit={onSubmit} isFetching={false} />)

    await user.type(screen.getByLabelText(/fpl entry id/i), '8731757')
    await user.type(screen.getByLabelText(/gameweek/i), '5')
    await user.click(screen.getByRole('button', { name: /^analyze$/i }))

    expect(onSubmit).toHaveBeenCalledWith(8731757, 5, null)
  })

  it('passes the free-transfer count through when the manager supplies it', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<EntryForm onSubmit={onSubmit} isFetching={false} />)

    await user.type(screen.getByLabelText(/fpl entry id/i), '8731757')
    await user.type(screen.getByLabelText(/free transfers/i), '2')
    await user.click(screen.getByRole('button', { name: /^analyze$/i }))

    expect(onSubmit).toHaveBeenCalledWith(8731757, null, 2)
  })

  it('treats a blank free-transfer field as unknown rather than zero', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<EntryForm onSubmit={onSubmit} isFetching={false} />)

    await user.type(screen.getByLabelText(/fpl entry id/i), '8731757')
    await user.click(screen.getByRole('button', { name: /^analyze$/i }))

    expect(onSubmit).toHaveBeenCalledWith(8731757, null, null)
  })

  it('accepts zero free transfers as a real, distinct value', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<EntryForm onSubmit={onSubmit} isFetching={false} />)

    await user.type(screen.getByLabelText(/fpl entry id/i), '8731757')
    await user.type(screen.getByLabelText(/free transfers/i), '0')
    await user.click(screen.getByRole('button', { name: /^analyze$/i }))

    expect(onSubmit).toHaveBeenCalledWith(8731757, null, 0)
  })

  it('does not call onSubmit when entry ID is missing', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<EntryForm onSubmit={onSubmit} isFetching={false} />)

    await user.click(screen.getByRole('button', { name: /^analyze$/i }))

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('disables the submit button while fetching', () => {
    render(<EntryForm onSubmit={vi.fn()} isFetching={true} />)

    expect(screen.getByRole('button', { name: /analyzing/i })).toBeDisabled()
  })
})
