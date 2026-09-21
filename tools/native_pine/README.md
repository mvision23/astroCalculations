# Development validation only

The indicator is already populated at `pine/bitcoin_universal_clock_native.pine`.
None of these files is needed by TradingView, and there is no generator or feed to run before installation.

- `model.py`: separately readable Python mirror of the native algorithms.
- `source_harness.py`: deliberately restricted translation of scalar expressions in the actual delivered Pine source for tests. It is **not a Pine compiler**, does not check Pine qualifiers or IL, and does not implement chart execution, drawings or rollback.
- `validate_reference.py`: independent full-period comparison, using development-only pyswisseph 2.10.3.2 (Swiss Ephemeris 2.10.03 Moshier). It verifies actual translated Pine expressions against the mirror at every reference timestamp, writes aggregate errors and a small independent fixture, and never writes dated data into the indicator.

Already run by the build agent, from the repository root:

```sh
.venv/bin/python -m pip install --no-cache-dir --target /tmp/bitcoin-native-reference pyswisseph==2.10.3.2
PYTHONPATH=/tmp/bitcoin-native-reference .venv/bin/python tools/native_pine/validate_reference.py
.venv/bin/python -m pytest tests/test_bitcoin_native_pine.py tests/test_universal_geometry.py tests/test_universal_events.py tests/test_universal_market.py tests/test_universal_book.py -q
```

Ordinary fixture tests do not require pyswisseph or internet access. The full independent rerun requires that optional development package; it is not added to project or indicator runtime dependencies. Its AGPL/commercial licensing remains with its publisher, and no Swiss Ephemeris source is vendored here.

The machine-readable parameter audit in `docs/bitcoin-native-pine-parameters.json` and its Markdown counterpart must both be updated if the app schemas or widget labels change; tests enforce completeness and matching descriptions.
