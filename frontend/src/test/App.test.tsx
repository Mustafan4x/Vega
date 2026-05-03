import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders the project name', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /trader/i })).toBeInTheDocument()
  })
})
