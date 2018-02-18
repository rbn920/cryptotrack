import click
import configparser
import privy
import os
import ccxt
import time
import json
import cfscrape
from timeit import default_timer as timer


class Config:
    def __init__(self, password):
        password = password.encode()
        if os.path.isfile('config.ini'):
            self.__load_config(password)
        else:
            self.__new_config(password)

    def __new_config(self, password):
        '''try to get rid of repeated code in __new and __load methods'''

        self.password = password
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        # enc_password = privy.hide(password, password, security=5)
        enc_password = self.__crypt(password, 'encrypt')
        self.config['user'] = {'password': enc_password}
        self.config.write(open('config.ini', 'w'))
        self.keys = {}
        self.secrets = {}

    def __load_config(self, password):
        '''try to get rid of repeated code in __new and __load methods'''

        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        enc_password = self.config['user']['password']
        self.password = privy.peek(enc_password, password)
        self.existing = self.config.has_section('keys')
        if self.existing:
            # self.keys = {k: privy.peek(self.config['keys'][k], self.password) for
            #              k in self.config['keys']}
            # self.secrets = {k: privy.peek(self.config['secrets'][k], self.password) for
            #                 k in self.config['secrets']}
            self.keys = {k: self.__crypt(self.config['keys'][k], 'decrypt') for
                         k in self.config['keys']}
            self.secrets = {k: self.__crypt(self.config['secrets'][k], 'decrypt') for
                            k in self.config['secrets']}
        else:
            self.keys = {}
            self.secrets = {}

    def __crypt(self, item, crypt):
        '''change so you can also encrypt password'''
        if isinstance(item, str):
            item = item.encode()

        if crypt == 'encrypt':
            return privy.hide(item, self.password, security=5)

        return privy.peek(item, self.password)

    def add_keys(self, name, key, secret):
        self.keys[name] = key.encode()
        self.secrets[name] = secret.encode()
        print('Encrypting your credential...')
        enc_keys = {}
        enc_secrets = {}
        for k in self.keys:
            enc_keys[k] = self.__crypt(self.keys[k], 'encrypt')
        for k in self.secrets:
            enc_secrets[k] = self.__crypt(self.secrets[k], 'encrypt')

        self.config['keys'] = enc_keys
        self.config['secrets'] = enc_secrets
        self.config.write(open('config.ini', 'w'))


pass_config = click.make_pass_decorator(Config)


def get_exchange(name, key, secret):
    return getattr(ccxt, name)({'apiKey': key, 'secret': secret,
                                'nonce': lambda: time.time() * 10000,
                                'timeout': 30000,
                                'session': cfscrape.create_scraper()})


def get_balance(name, key, secret):
    exchange = get_exchange(name, key, secret)
    return exchange.fetch_balance()


def get_my_trades(name, key, secret, symbol):
    exchange = get_exchange(name, key, secret)
    time.sleep(exchange.rateLimit / 1000)
    return exchange.fetch_my_trades(symbol=symbol)


def get_trades(name, key, secret, symbol):
    exchange = get_exchange(name, key, secret)
    time.sleep(exchange.rateLimit / 1000)
    return exchange.fetch_trades(symbol=symbol)


def get_markets(name, key, secret):
    exchange = get_exchange(name, key, secret)
    return exchange.fetch_markets()


def parse_trade(trade):
    parsed = {
        'datetime': trade['datetime'],
        'timestamp': trade['timestamp'],
        'symbol': trade['symbol'],
        'side': trade['side'],
        'price': trade['price'],
        'amount': trade['amount'],
        'fee': trade['info']['fee_amount'],
        'fee_currency': trade['info']['fee_currency'],
        'exchange': trade['info']['exchange']
    }

    return parsed


@click.group()
@click.password_option()
@click.pass_context
def cli(ctx, password):
    ctx.obj = Config(password)


@cli.command()
@click.argument('name', nargs=1)
@click.argument('key', nargs=1)
@click.argument('secret', nargs=1)
@pass_config
def add_exchange(config, name, key, secret):
    config.add_keys(name, key, secret)


@cli.command()
@pass_config
def api_keys(config):
    print('keys')
    for k in config.keys:
        print('{}: {}'.format(k, config.keys[k].decode()))

    print('secrets')
    for k in config.secrets:
        print('{}: {}'.format(k, config.secrets[k].decode()))


@cli.command()
@click.argument('exchange', nargs=1)
@pass_config
def balance(config, exchange):
    key = config.keys[exchange].decode()
    secret = config.secrets[exchange].decode()
    print(get_balance(exchange, key, secret))


@cli.command()
@click.argument('exchange', nargs=1)
@click.argument('symbol', nargs=1)
@pass_config
def trades(config, exchange, symbol):
    key = config.keys[exchange].decode()
    secret = config.secrets[exchange].decode()
    print(get_trades(exchange, key, secret, symbol)[0])


@cli.command()
@click.argument('exchange', nargs=1)
@click.argument('symbol', nargs=1)
@pass_config
def my_trades(config, exchange, symbol):
    key = config.keys[exchange].decode()
    secret = config.secrets[exchange].decode()
    print(get_my_trades(exchange, key, secret, symbol))


@cli.command()
@click.argument('exchange', nargs=1)
@pass_config
def markets(config, exchange):
    key = config.keys[exchange].decode()
    secret = config.secrets[exchange].decode()
    print(get_markets(exchange, key, secret))


@cli.command()
@click.argument('exchange', nargs=1)
@pass_config
def trade_history(config, exchange):
    start = timer()
    key = config.keys[exchange].decode()
    secret = config.secrets[exchange].decode()
    symbols = []
    for market in get_markets(exchange, key, secret):
        symbols.append(market['symbol'])
    history = []
    for symbol in symbols:
        history.append(get_my_trades(exchange, key, secret, symbol))
        # if not history:
        #     time.sleep(0.1)

    # trades = []
    # for symbol in history:
    #     for trade in symbol:
    #         trades.append(parse_trade(trade))
    end = timer()
    print(end - start)
    trades = history
    fname = exchange + '.json'
    with open(fname, 'w') as fp:
        json.dump(trades, fp)


@cli.command()
@pass_config
def get_keys(config):
    return


if __name__ == '__main__':
    cli()
