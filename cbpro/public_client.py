#
# coinbase exchange public api
# https://docs.cdp.coinbase.com/exchange/reference
#
# was cbpro/PublicClient.py
# Daniel Paquin
#
# For public requests to the Coinbase exchange

import requests


class PublicClient(object):
    """coinbase exchange public client API.

    All requests default to the `product_id` specified at object
    creation if not otherwise specified.

    Attributes:
        url (Optional[str]): API URL. Defaults to coinbase exchange API.

    """

    def __init__(self, api_url='https://api.exchange.coinbase.com', timeout=15):
        """Create coinbase exchange API public client.

        Args:
            api_url (Optional[str]): API URL. Defaults to coinbase exchange API.

        """
        self.url = api_url.rstrip('/')
        self.auth = None
        self.session = requests.Session()
        self.timeout = timeout

    def get_products(self):
        """Get a list of available currency pairs for trading.

        Returns:
            list: Info about all currency pairs. Example::
                [
                    {
                        "id": "BTC-USD",
                        "display_name": "BTC/USD",
                        "base_currency": "BTC",
                        "quote_currency": "USD",
                        "base_min_size": "0.01",
                        "base_max_size": "10000.00",
                        "quote_increment": "0.01"
                    }
                ]

        """
        return self._send_message('get', '/products')

    def get_product_order_book(self, product_id, level=1):
        """Get a list of open orders for a product.

        The amount of detail shown can be customized with the `level`
        parameter:
        * 1: Only the best bid and ask
        * 2: Top 50 bids and asks (aggregated)
        * 3: Full order book (non aggregated)

        Level 1 and Level 2 are recommended for polling. For the most
        up-to-date data, consider using the websocket stream.

        **Caution**: Level 3 is only recommended for users wishing to
        maintain a full real-time order book using the websocket
        stream. Abuse of Level 3 via polling will cause your access to
        be limited or blocked.

        Args:
            product_id (str): Product
            level (Optional[int]): Order book level (1, 2, or 3).
                Default is 1.

        Returns:
            dict: Order book. Example for level 1::
                {
                    "sequence": "3",
                    "bids": [
                        [ price, size, num-orders ],
                    ],
                    "asks": [
                        [ price, size, num-orders ],
                    ]
                }

        """
        params = {'level': level}
        return self._send_message('get',
                                  '/products/{}/book'.format(product_id),
                                  params=params)

    def get_product_ticker(self, product_id):
        """Snapshot about the last trade (tick), best bid/ask and 24h volume.

        **Caution**: Polling is discouraged in favor of connecting via
        the websocket stream and listening for match messages.

        Args:
            product_id (str): Product

        Returns:
            dict: Ticker info. Example::
                {
                  "trade_id": 4729088,
                  "price": "333.99",
                  "size": "0.193",
                  "bid": "333.98",
                  "ask": "333.99",
                  "volume": "5957.11914015",
                  "time": "2015-11-14T20:46:03.511254Z"
                }

        """
        return self._send_message('get',
                                  '/products/{}/ticker'.format(product_id))

    def get_product_trades(self, product_id, **kwargs):
        """List the latest trades for a product.

        This method returns a generator which may make multiple HTTP requests
        while iterating through it.

        Args:
             product_id (str): Product
             limit (Optional[int]): overall limit of number of trades returned
                (without this, the generator will continue as long as trades are available)
             pagelimit (Optional[int]): the desired number of trades per page
             before (Optional[str]): latest trade time in ISO 8601, default most recent trades
             after (Optional[str]): earliest trade time in ISO 8601, default most recent trades

        Returns:
             list generator of trades. Example:
                 [{
                     "time": "2014-11-07T22:19:28.578544Z",
                     "trade_id": 74,
                     "price": "10.00000000",
                     "size": "0.01000000",
                     "side": "buy"
                 }, {
                     "time": "2014-11-07T01:08:43.642366Z",
                     "trade_id": 73,
                     "price": "100.00000000",
                     "size": "0.01000000",
                     "side": "sell"
         }]
        """
        return self._send_paginated_message('/products/{}/trades'
                                            .format(product_id),
                                            **kwargs)

    def get_product_historic_rates(self, product_id, start=None, end=None,
                                   granularity=None):
        """Historic rates for a product.

        Rates are returned in grouped buckets based on requested
        `granularity`. If start, end, and granularity aren't provided,
        the exchange will assume some (currently unknown) default values.

        Historical rate data may be incomplete. No data is published for
        intervals where there are no ticks.

        **Caution**: Historical rates should not be polled frequently.
        If you need real-time information, use the trade and book
        endpoints along with the websocket feed.

        The maximum number of data points for a single request is 200
        candles. If your selection of start/end time and granularity
        will result in more than 200 data points, your request will be
        rejected. If you wish to retrieve fine granularity data over a
        larger time range, you will need to make multiple requests with
        new start/end ranges.

        Args:
            product_id (str): Product
            start (Optional[str]): Start time in ISO 8601
            end (Optional[str]): End time in ISO 8601
            granularity (Optional[int]): Desired time slice in seconds

        Returns:
            list: Historic candle data. Example:
                [
                    [ time, low, high, open, close, volume ],
                    [ 1415398768, 0.32, 4.2, 0.35, 4.2, 12.3 ],
                    ...
                ]

        """
        params = {}
        if start is not None:
            params['start'] = start
        if end is not None:
            params['end'] = end
        if granularity is not None:
            acceptedGrans = [60, 300, 900, 3600, 21600, 86400]
            if granularity not in acceptedGrans:
                raise ValueError( 'Specified granularity is {}, must be in approved values: {}'.format(
                        granularity, acceptedGrans) )

            params['granularity'] = granularity
        return self._send_message('get',
                                  '/products/{}/candles'.format(product_id),
                                  params=params)

    def get_product_24hr_stats(self, product_id):
        """Get 24 hr stats for the product.

        Args:
            product_id (str): Product

        Returns:
            dict: 24 hour stats. Volume is in base currency units.
                Open, high, low are in quote currency units. Example::
                    {
                        "open": "34.19000000",
                        "high": "95.70000000",
                        "low": "7.06000000",
                        "volume": "2.41000000"
                    }

        """
        return self._send_message('get',
                                  '/products/{}/stats'.format(product_id))

    def get_currencies(self):
        """List known currencies.

        Returns:
            list: List of currencies. Example::
                [{
                    "id": "BTC",
                    "name": "Bitcoin",
                    "min_size": "0.00000001"
                }, {
                    "id": "USD",
                    "name": "United States Dollar",
                    "min_size": "0.01000000"
                }]

        """
        return self._send_message('get', '/currencies')

    def get_time(self):
        """Get the API server time.

        Returns:
            dict: Server time in ISO and epoch format (decimal seconds
                since Unix epoch). Example::
                    {
                        "iso": "2015-01-07T23:47:25.201Z",
                        "epoch": 1420674445.201
                    }

        """
        return self._send_message('get', '/time')

    def _send_message(self, method, endpoint, params=None, data=None):
        """Send API request.

        Args:
            method (str): HTTP method (get, post, delete, etc.)
            endpoint (str): Endpoint (to be added to base URL)
            params (Optional[dict]): HTTP request parameters
            data (Optional[str]): JSON-encoded string payload for POST

        Returns:
            dict/list: JSON response

        """
        url = self.url + endpoint
        r = self.session.request(method, url, params=params, data=data,
                                 auth=self.auth, timeout=self.timeout)
        return r.json()

    def _send_paginated_message(self, endpoint, *, limit=None, pagelimit=None, before=None, after=None):
        """ Send API message that results in a paginated response.

        The paginated responses are abstracted away by making API requests on
        demand as the response is iterated over.

        Paginated API messages support 3 additional parameters: 'before',
        'after', and '[page]limit'. 'before' and 'after' are mutually exclusive. To
        use them, supply an index value for that endpoint (the field used for
        indexing varies by endpoint - get_fills() uses 'trade_id', for example).
            '[page]limit': Set amount of data per HTTP response (see pagelimit arg)
            'before': Only get data that occurs more recently than index
            'after': Only get data that occurs further in the past than index

        Args:
            endpoint (str): Endpoint (to be added to base URL)
            limit (Optional[int]): limit the overall number of records returned
            pagelimit (Optional[int]): supply the limit parameter, with a better name
            before (Optional[str]): supply the before parameter
            after (Optional[str]): supply the after parameter

        Yields:
            dict: API response objects

        """
        params = {}
        if before is not None:
            params['before'] = before
        if after is not None:
            params['after'] = after
        if pagelimit is not None:
            params['limit'] = pagelimit
        # don't bother fetching more than requested
        # 1000 was the coinbasepro default on 20210510
        if limit and limit < params.get('limit', 1000):
            params['limit'] = limit
        rescount = 0
        url = self.url + endpoint
        while True:
            r = self.session.get(url, params=params, auth=self.auth, timeout=self.timeout)
            results = r.json()
            rescount += len(results)
            for result in results:
                yield result
            #print('from %s, %d of %d' % (url, rescount, limit))
            # If there are no more pages, we're done. Otherwise update `after`
            # param to get next page.
            # If this request included `before` don't get any more pages - the
            # coinbase exchange API doesn't support multiple pages in that case.
            if not r.headers.get('cb-after') or \
                    (limit and rescount >= limit) or \
                    params.get('before') is not None:
                break
            else:
                params['after'] = r.headers['cb-after']




if __name__ == '__main__':

    import json
    import sys

    pc = PublicClient()

    #res = pc.get_products()
    #res = pc.get_currencies()
    #res = pc.get_time()
    product_id = sys.argv[1].upper()
    #res = pc.get_product_ticker(product_id)
    #res = list(pc.get_product_trades(product_id))  # never ends?
    #res = list(pc.get_product_trades(product_id, pagelimit=100))  # never ends?
    #res = next(pc.get_product_trades(product_id))  # only gets one?
    #res = next(pc.get_product_trades(product_id, pagelimit=100))  # only gets one?
    #res = list(pc.get_product_trades(product_id, limit=1000))
    res = list(pc.get_product_trades(product_id, limit=100))
    #res = pc.get_product_order_book(product_id)
    #res = pc.get_product_historic_rates(product_id)
    #res = pc.get_product_24hr_stats(product_id)

    print(json.dumps(res, indent=2))
