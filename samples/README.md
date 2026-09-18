# Reproducible examples

- `synthetic.csv` / `workspace.json`: seeded OHLC demonstration. **Not historical data.**
- `sugar-book.json`: all nine Book I bodies for March 17–April 19, 1993 replay.
  Select **Book transcribed ranges → sugar_daily** in the app, or use CLI
  `--book-ranges sugar_daily`. Only printed low/high observations are supplied.
- `sugar-price.html`: standalone interactive chart with embedded provenance.
- `sugar-price.png`, `sugar-clock.png`: inspected static chart examples.
- `sugar-results.zip`: CSV/JSON/settings bundle from the sparse source fixture.
- `saturn-dow-monthly.json`: monthly rounded Saturn construction for 1992.
- `october-1987.json`, `december-1993.json`: astronomy-only timing/calendar examples.
  Default occupancy is continuous; switch interpretations explicitly to investigate
  the source's broader approximate calendar arrows.
- `pine-workspace.json`: compact Mercury/Jupiter export configuration.
- `pine/*.pine`: complete generated Pine v6 indicators, 1993-02-20–1993-04-30 UTC.
- `pine/ephemeris.json`: their finite tables, metadata and interpolation measurements.

Regenerate with `python tools/reproduce_clock_examples.py --images` after optional
Kaleido/Chrome setup. The script replaces these generated examples deliberately.
See [the application guide](../docs/universal-clock.md) and
[TradingView verification](../docs/tradingview.md).
