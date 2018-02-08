import click
import configparser
import privy
import os


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
            self.keys = {k: self.config['keys'][k] for
                         k in self.config['keys']}
            self.secrets = {k: self.config['secrets'][k] for
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


if __name__ == '__main__':
    cli()
