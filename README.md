# ccxt_async_example
Example of handling multiple orderbooks in ccxt

The point of this code is to show an example of combining orderbook data, order management, and execution! There are still quirks, and it may break.

See the article on substack for full explanation.

# How to run

Replace path to your API key in main.py (or use os.environ).

`python3 main.py binance:BTCUSDT binance:ETHUSDT 1000`

- First leg = buy leg
- Second leg = sell leg
- Notional amount for each in USDT
