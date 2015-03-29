"""A wrapper for the Yahoo! Finance YQL api."""

import sys
import requests

PUBLIC_API_URL = 'http://query.yahooapis.com/v1/public/yql'
DATATABLES_URL = 'store://datatables.org/alltableswithkeys'
HISTORICAL_URL = 'http://ichart.finance.yahoo.com/table.csv?s='
RSS_URL = 'http://finance.yahoo.com/rss/headline?s='
FINANCE_TABLES = {'quotes': 'yahoo.finance.quotes',
                  'options': 'yahoo.finance.options',
                  'quoteslist': 'yahoo.finance.quoteslist',
                  'sectors': 'yahoo.finance.sectors',
                  'industry': 'yahoo.finance.industry'}


def executeYQLQuery(yql):
    reqdata = {'q': yql, 'format': 'json', 'env': DATATABLES_URL}
    resp = requests.get(PUBLIC_API_URL, params=reqdata)
    return resp.json()


class QueryError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def __format_symbol_list(symbolList):
    return ",".join(["\""+stock+"\"" for stock in symbolList])


def __is_valid_response(response, field):
    return 'query' in response and 'results' in response['query'] and field in response['query']['results']


def __validate_response(response, tagToCheck):
    if __is_valid_response(response, tagToCheck):
        quoteInfo = response['query']['results'][tagToCheck]
    else:
        if 'error' in response:
            raise QueryError('YQL query failed with error: "%s".' % response['error']['description'])
        else:
            raise QueryError('YQL response malformed.')
    return quoteInfo


def get_current_info(symbolList, columnsToRetrieve='*'):
    """Retrieves the latest data (15 minute delay) for the
    provided symbols."""

    columns = ','.join(columnsToRetrieve)
    symbols = __format_symbol_list(symbolList)

    yql = 'select %s from %s where symbol in (%s)' % (columns, FINANCE_TABLES['quotes'], symbols)
    response = executeYQLQuery(yql)
    return __validate_response(response, 'quote')


def get_historical_info(symbol):
    """Retrieves historical stock data for the provided symbol.
    Historical data includes date, open, close, high, low, volume,
    and adjusted close."""

    yql = 'select * from csv where url=\'%s\'' \
          ' and columns=\"Date,Open,High,Low,Close,Volume,AdjClose\"' % (HISTORICAL_URL + symbol)
    results = executeYQLQuery(yql)
    # delete first row which contains column names
    del results['query']['results']['row'][0]
    return results['query']['results']['row']


def get_news_feed(symbol):
    """Retrieves the rss feed for the provided symbol."""

    feedUrl = RSS_URL + symbol
    yql = 'select title, link, description, pubDate from rss where url=\'%s\'' % feedUrl
    response = executeYQLQuery(yql)
    if response['query']['results']['item'][0]['title'].find('not found') > 0:
        raise QueryError('Feed for %s does not exist.' % symbol)
    else:
        return response['query']['results']['item']


def get_options_info(symbol, expiration='', columnsToRetrieve='*'):
    """Retrieves options data for the provided symbol."""

    columns = ','.join(columnsToRetrieve)
    yql = 'select %s from %s where symbol = \'%s\'' % (columns, FINANCE_TABLES['options'], symbol)

    if expiration != '':
        yql += " and expiration='%s'" % (expiration)

    response = executeYQLQuery(yql)
    return __validate_response(response, 'optionsChain')


def get_index_summary(index, columnsToRetrieve='*'):
    columns = ','.join(columnsToRetrieve)
    yql = 'select %s from %s where symbol = \'@%s\'' % (columns, FINANCE_TABLES['quoteslist'], index)
    response = executeYQLQuery(yql)
    return __validate_response(response, 'quote')


def get_industry_ids():
    """retrieves all industry names and ids."""

    yql = 'select * from %s' % FINANCE_TABLES['sectors']
    response = executeYQLQuery(yql)
    return __validate_response(response, 'sector')


def get_industry_index(id):
    """retrieves all symbols that belong to an industry."""

    yql = 'select * from %s where id =\'%s\'' % (FINANCE_TABLES['industry'], id)
    response = executeYQLQuery(yql)
    return __validate_response(response, 'industry')


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            symb = sys.argv[1:]
        else:
            symb = 'T'
        for st in get_current_info(symb):
            print(st)
        # print(get_industry_ids())
        # get_news_feed('yhoo')
    except QueryError as e:
        print(e)
        sys.exit(2)
