"""Interactive REPL for the Black Scholes pricer.

Run as ``python -m app.repl`` (or ``vega-repl`` once installed). Prompts for
the five inputs (S, K, T, r, sigma) and prints the call and put prices to
four decimal places.
"""

from __future__ import annotations

from app.pricing import black_scholes_call, black_scholes_put

_PROMPTS: tuple[tuple[str, str, bool], ...] = (
    ("S", "Spot price S (currency, must be non negative)", True),
    ("K", "Strike price K (currency, must be strictly positive)", True),
    ("T", "Time to expiry T (years, must be non negative)", True),
    ("r", "Risk free rate r (decimal, e.g. 0.05 for 5 percent; may be negative)", False),
    ("sigma", "Volatility sigma (decimal, e.g. 0.20 for 20 percent, must be non negative)", True),
)


def _read_float(label: str, prompt: str, require_non_negative: bool) -> float:
    while True:
        raw = input(f"{prompt}: ").strip()
        try:
            value = float(raw)
        except ValueError:
            print(f"  could not parse {label!r} as a float, try again")
            continue
        if require_non_negative and value < 0:
            print(f"  {label} must be non negative, got {value}, try again")
            continue
        return value


def main() -> int:
    print("Vega Black Scholes REPL. Enter the five inputs:")
    inputs: dict[str, float] = {}
    for label, prompt, require_non_negative in _PROMPTS:
        inputs[label] = _read_float(label, prompt, require_non_negative)

    try:
        call = black_scholes_call(**inputs)
        put = black_scholes_put(**inputs)
    except ValueError as exc:
        print(f"input rejected by pricer: {exc}")
        return 1

    print(f"call = {call:.4f}")
    print(f"put  = {put:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
