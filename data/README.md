# Local Bitcoin data

`bitcoin_2010-07-02_2025-07-05.csv` is the supplied original and is left unchanged.
`bitcoin_universal.csv` is the ascending, canonical-header import for the app.

The actual first candle starts 17 July 2010 and the last starts 4 July 2025,
closing at 5 July 2025. UTC midnight boundaries are assumed because the original
contains dates but no timezone. OHLC, volume and market capitalization retain
their supplied numeric values; no missing bars or opens/closes are invented.
Flat OHLC and zero-volume flags remain visible as additional columns.

The prepared file uses `timestamp` at bar open and `bar_end` at next midnight.
The saved market convention is UTC, 24/7, open-labeled, 1,440-minute bars,
00:00–00:00 sessions. A session is labeled by its closing date. Its range becomes
available only then. Price units are USD/BTC; the $0.01 tick is an assumed display
setting and never rounds the imported data. Source venue/provider and volume
units were not supplied.

The app sidebar's **Bitcoin research view → Load Bitcoin · $369** loads one of
`bitcoin-workspaces/{short,intermediate,long}.json` together with this file.
All use a locked $369 step, $8,856 full cycle and $4,428 opposite offset. Chosen
bodies are exploratory validation-ranked overlays, not validated predictors.

Reproduce with `.venv/bin/python tools/analyze_bitcoin.py`, followed by
`.venv/bin/python tools/render_bitcoin_research.py`. The full data audit, fixed
research protocol, model/event tables, charts and findings are under
[`reports/bitcoin`](../reports/bitcoin). The original file is needed to rerun
normalization; CSV git-ignore rules do not modify or remove it.

If a run stops after the exact-event archive is complete, resume its remaining
comparisons with `.venv/bin/python tools/analyze_bitcoin.py --finish-only`.
Resumption checks source and normalized file hashes, the saved protocol, and the
event cache's provider/engine signature before reusing results.
