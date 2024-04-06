import argparse
import asyncio
import ccxt.pro as ccxt
from oms import OMS
from data import Data

class Spready:

    def __init__(
        self,
        buy_leg,
        sell_leg,
        notional_each,
        wait_time=5,
        lev_check=False,
    ):

        self.buy_exch = buy_leg.split(':')[0]
        self.buy_inst = buy_leg.split(':')[1]
        self.sell_exch = sell_leg.split(':')[0]
        self.sell_inst = sell_leg.split(':')[1]
        self.notional = notional_each
        self.wait_time = wait_time
        self.lev_check = lev_check
        self.lev = 10

        print(
            self.buy_exch,
            self.buy_inst,
            self.sell_exch,
            self.sell_inst,
            self.notional,
        )

        key, sec = open('path_to_your_key_here.txt', 'r').read().split('\n')
        self.exchange = ccxt.binance({
            'apiKey': key,
            'secret': sec,
            'options': {
                'defaultType': 'future',
            }
        })

        self.data = Data(self.exchange)

        self.oms = OMS(
            self.exchange,
            self.notional,
            self.wait_time,
        )


    async def check_lev(self):
        for inst in [self.buy_inst, self.sell_inst]:
            try:
                lev = await self.exchange.set_leverage(leverage=self.lev, symbol=inst)
                print(lev)
            except Exception as e:
                print('error check_lev:', inst, e)


    async def update(self):

        while True:
            # update oms with last price
            for _ in self.data.data:
                self.oms.oms[_]['bid'] = self.data.data[_]['bid']
                self.oms.oms[_]['ask'] = self.data.data[_]['ask']


    async def run(self):

        if self.lev_check:
            await self.check_lev()

        await self.oms.populate_oms([
            {
                'inst': self.buy_inst,
                'side': 'buy',
            },
            {
                'inst': self.sell_inst,
                'side': 'sell',
            },
        ])

        await self.data.populate_data([
            self.buy_inst,
            self.sell_inst,
        ])

        try:
            await asyncio.gather(
                self.data.watch_multiple_ob([
                    self.buy_inst,
                    self.sell_inst,
                ]),
                self.update(),
                self.oms.cancel_replace(),
            )

        except Exception as e:
            await self.exchange.close()
            print('Rebalance.run():', e)
            print('exchange closed.')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("buy_leg", help="exchange:pair", type=str)
    parser.add_argument("sell_leg", help="exchange:pair", type=str)
    parser.add_argument("notional_each", help="123", type=float)

    args = parser.parse_args()

    s = Spready(
        buy_leg=args.buy_leg,
        sell_leg=args.sell_leg,
        notional_each=args.notional_each,
    )

    asyncio.run(s.run())
