import asyncio

class Data:

    def __init__(
        self,
        exchange,
    ):

        self.exchange = exchange
        self.data = {}

    async def populate_data(self, insts):
        for _ in insts:
            self.data[_] = {'bid': 0, 'ask': 0}

    async def watch_multiple_ob(self, symbols):

        try:
            while True:
                ob = await self.exchange.watch_order_book_for_symbols(symbols)
                print(f'{ob["symbol"]} {ob["bids"][0][0]} {ob["asks"][0][0]}')
                self.data[ob['symbol'].replace('/USDT:USDT', 'USDT')]['bid'] = ob['bids'][0][0]
                self.data[ob['symbol'].replace('/USDT:USDT', 'USDT')]['ask'] = ob['asks'][0][0]

        except Exception as e:
            print('Data.watch_multiple_trades', type(e), e)
            await self.exchange.close()
