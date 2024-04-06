import asyncio
from datetime import datetime, timedelta

class OMS:

    def __init__(
        self,
        client,
        notional,
        wait_time,

    ):

        self.client = client
        self.oms = {}
        self.notional = notional
        self.wait_time = wait_time

    async def populate_oms(self, insts):

        for _ in insts:
            self.oms[_['inst']] = {
                'side': _['side'],
                'bid': 0,
                'ask': 0,
                'filled': False,
                'active': False,
                'last_update': None,
                'order_id': 0,
            }

    async def trade(self, sym, qty=None):

        if self.oms[sym]['side'] == 'buy':
            px = self.oms[sym]['bid']
        if self.oms[sym]['side'] == 'sell':
            px = self.oms[sym]['ask']

        if qty != None:
            print(sym, 'trading partial!')

        if qty == None:
            qty = self.notional/px

        order = await self.client.create_order(
            symbol=sym,
            type='limit',
            side=self.oms[sym]['side'],
            amount=qty,
            price=px,
            params={
                'postOnly': True,
            },
        )
        return order

    async def cancel_replace(self):

        while True:

            for sym in self.oms:

                if self.oms[sym]['bid'] == 0 and self.oms[sym]['ask'] == 0:
                    # print(sym, 'no data')
                    continue

                if len([_ for _ in self.oms if self.oms[_]['filled'] == True]) == 2:
                    print('both filled')
                    return

                if self.oms[sym]['filled']:
                    print(sym, 'filled')
                    continue

                # if order, cancel/replace or leave it (if px unch)
                if self.oms[sym]['active'] == True:

                    # check order... was it filled?
                    order = await self.client.fetch_order(
                        symbol=sym,
                        id=self.oms[sym]['order_id'],
                    )

                    if order['status'] == 'closed':
                        self.oms[sym]['filled'] = True
                        continue

                    # if not filled, did px move?
                        # then move up/dn
                    if order['status'] != 'filled':

                        # if buy, check bid vs. limit
                        if self.oms[sym]['side'] == 'buy':
                            # if bid > price
                            if self.oms[sym]['bid'] > order['price']:
                                print(sym, 'bid', self.oms[sym]['bid'], 'limit', order['price'])
                                print('move up!!!')

                                order = await self.client.cancel_order(
                                    symbol=sym,
                                    id=self.oms[sym]['order_id'],
                                )
                                try:
                                    order = await self.trade(
                                        sym,
                                        qty=order['remaining'],
                                    )
                                except Exception as e:
                                    # in case the orderbook moves up/down rapidly,
                                    # there may be a case where you try a postonly order at price that would now be taking...
                                    # this would cause an exception
                                    print('exception with order')
                                    await asyncio.sleep(0.5)
                                    order = await self.trade(
                                        sym,
                                        qty=order['remaining'],
                                    )

                                self.oms[sym]['last_update'] = datetime.utcnow()
                                self.oms[sym]['order_id'] = order['info']['orderId']

                            if self.oms[sym]['bid'] == order['price']:
                                # print(sym, 'bid == px, do nothing')
                                pass

                        # if ask, check ask vs. limit
                        if self.oms[sym]['side'] == 'sell':
                            # if ask < limit
                            if self.oms[sym]['ask'] < order['price']:
                                print(sym, 'ask', self.oms[sym]['ask'], 'limit', order['price'])
                                print('move dn!!!')

                                order = await self.client.cancel_order(
                                    symbol=sym,
                                    id=self.oms[sym]['order_id'],
                                )
                                try:
                                    order = await self.trade(
                                        sym,
                                        qty=order['remaining'],
                                    )
                                except Exception as e:
                                    # in case the orderbook moves up/down rapidly,
                                    # there may be a case where you try a postonly order at price that would now be taking...
                                    # this would cause an exception
                                    print('exception with order')
                                    await asyncio.sleep(0.5)
                                    order = await self.trade(
                                        sym,
                                        qty=order['remaining'],
                                    )
                                self.oms[sym]['last_update'] = datetime.utcnow()
                                self.oms[sym]['order_id'] = order['info']['orderId']

                            if self.oms[sym]['ask'] == order['price']:
                                # print(sym, 'ask == px, do nothing')
                                pass

                # if no order, make order
                if self.oms[sym]['active'] == False:

                    print(sym, 'inactive')

                    order = await self.trade(sym)
                    self.oms[sym]['active'] = True
                    self.oms[sym]['last_update'] = datetime.utcnow()
                    self.oms[sym]['order_id'] = order['info']['orderId']
                    print('first order:', order, '\n')
                    # continue
