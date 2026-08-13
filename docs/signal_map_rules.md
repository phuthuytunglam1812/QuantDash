# Signal Map rules (W2-16)

The RSI-vs-P/E Signal Map receives the already filtered W2-15 dataframe. It
therefore plots exactly the current screener subset rather than independently
querying the full universe.

- X axis: raw P/E ratio.
- Y axis: RSI 14.
- Bubble size: composite score (0–100).
- Bubble color: W2-14 Overall Signal.
- Bubble label: ticker.

All active W2-15 criteria continue to use AND logic. Resetting filters restores
both the screener and chart to the default stock universe.

Rows missing RSI or P/E are excluded from the chart without filling. The UI
reports both the plotted count and excluded count. A stock can remain in the
screener when its missing feature was not actively filtered, while still being
excluded from this two-axis visual because its position is unknown.

RSI reference lines at 30 and 70 are context, not automatic trading signals.
Likewise, lower P/E is not automatically more attractive; the chart supports
comparison and does not replace the component scores or their coverage notes.
