# W1-17 test report

Date: 2026-08-05  
Environment: Python 3.10.11, pytest 9.1.1

Command: `python -m pytest`

Result: **36 passed in 2.75 seconds**

| Area | Test file | Tests |
|---|---|---:|
| API comparison | `test_api_comparison.py` | 5 |
| Data layers | `test_build_data_layers.py` | 2 |
| Data cleaning | `test_clean_data.py` | 4 |
| Provider clients | `test_clients.py` | 4 |
| SEC fundamentals | `test_download_fundamentals.py` | 4 |
| Price downloads | `test_download_prices.py` | 2 |
| Indicator formulas | `test_features.py` | 10 |
| Indicator invariants | `test_indicator_invariants.py` | 5 |

The indicator tests cover simple/log returns, SMA, EMA, Wilder RSI, annualized
volatility, current drawdown, and maximum drawdown-to-date. They also verify
warm-up behavior, ticker isolation, input immutability, edge cases, and bounds.
