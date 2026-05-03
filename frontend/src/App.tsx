function App() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-background text-fg">
      <div className="text-center">
        <h1
          className="text-primary"
          style={{
            fontFamily: 'var(--font-display)',
            fontStyle: 'italic',
            fontSize: '56px',
            lineHeight: 1.05,
          }}
        >
          Trader
        </h1>
        <p className="mt-4 text-fg-muted" style={{ fontFamily: 'var(--font-sans)' }}>
          Black Scholes options pricer, Oxblood theme placeholder.
        </p>
      </div>
    </main>
  )
}

export default App
