import click
import configparser
import privy
import os
import ccxt


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
        enc_password = privy.hide(password, password, security=5)
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
            self.keys = {k: privy.peek(self.config['keys'][k], self.password) for
                         k in self.config['keys']}
            self.secrets = {k: privy.peek(self.config['secrets'][k], self.password) for
                            k in self.config['secrets']}
        else:
            self.keys = {}
            self.secrets = {}

    def __encrypt(self, key, secret):
        '''change so you can also encrypt password'''

        return [privy.hide(key.encode(), self.password, security=5),
                privy.hide(secret.encode(), self.password, security=5)]

    def __decrypt(self, key, secret):
        '''change so you can also encrypt password'''

        return [privy.peek(key, self.password),
                privy.peek(secret, self.password)]

    def add_keys(self, name, key, secret):
        enc_key, enc_secret = self.__encrypt(key, secret)
        self.keys[name] = enc_key
        self.secrets[name] = enc_secret
        self.config['keys'] = self.keys
        self.config['secrets'] = self.secrets
        print('Encrypting your credential...')
        self.config.write(open('config.ini', 'w'))


pass_config = click.make_pass_decorator(Config)


def test_balance(key, secret):
    exchange = ccxt.gemini({
        'apiKey': key,
        'secret': secret
    })
    print(exchange.fetch_balance())


def test_trades(key, secret, symbol):
    exchange = ccxt.gemini({
        'apiKey': key,
        'secret': secret
    })
    print(exchange.fetch_my_trades(symbol=symbol))


def test_markets(key, secret):
    exchange = ccxt.gemini({
        'apiKey': key,
        'secret': secret
    })
    print(exchange.fetch_markets())


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
def get_balance(config):
    key = config.keys['gemini'].decode()
    secret = config.secrets['gemini'].decode()
    # print(key)
    # print(secret)
    print(test_balance(key, secret))


@cli.command()
@click.argument('symbol', nargs=1)
@pass_config
def get_trades(config, symbol):
    key = config.keys['gemini'].decode()
    secret = config.secrets['gemini'].decode()
    print(test_trades(key, secret, symbol))


@cli.command()
@pass_config
def get_markets(config):
    key = config.keys['gemini'].decode()
    secret = config.secrets['gemini'].decode()
    # print(key)
    # print(secret)
    print(test_markets(key, secret))


if __name__ == '__main__':
    cli()
