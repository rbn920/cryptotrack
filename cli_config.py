import click
import configparser
import privy


class Config:
    def __init__(self, password):
        self._load()
        self.password = password.encode()

    def _load(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.existing = self.config.has_section('keys')
        if self.existing:
            self.keys = {k: self.config['keys'][k] for
                         k in self.config['keys']}
            self.secrets = {k: self.config['secrets'][k] for
                            k in self.config['secrets']}
        else:
            self.keys = {}
            self.secrets = {}

    def _encrypt(self, key, secret):
        return [privy.hide(key.encode(), self.password, security=5),
                privy.hide(secret.encode(), self.password, security=5)]

    def _decrypt(self, key, secret):
        return [privy.peek(key, self.password, security=5),
                privy.peek(secret, self.password, security=5)]

    def add_password(self, password):
        pass

    def add_keys(self, name, key, secret):
        enc_key, enc_secret = self._encrypt(key, secret)
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
