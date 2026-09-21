# Bitcoin Universal Clock native indicator

Paste the complete contents of `bitcoin_universal_clock_native.pine` into
TradingView's Pine Editor, save, and update the indicator on your chart.

The historical curves use constant default colors to consume **60 plot counts**:
10 bodies × 3 main branches × main/opposite. This addresses the reported RE10140
error: the previous input-based plot colors doubled the count to 120. Hiding a
body or branch does not reduce the compiled plot count.

- Edit historical curve colors individually under **Settings → Style**.
- The **Drawing color** input beside each body controls its future curves and
  event labels. It does not change historical plots.
- All body toggles, main branches, opposite channels and astronomy calculations
  remain available. Historical and drawing colors start with the same palette;
  subsequent color edits are independent.

The plot budget follows TradingView's
[plot-count rules](https://www.tradingview.com/pine-script-docs/visuals/plots/#plot-count-limit).
Local checks verify constant plot colors and the 60-call budget; they do not
compile or execute the indicator in TradingView. Platform runtime verification
is still required after replacing the script.
