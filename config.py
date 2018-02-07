import click
import configparser
import privy
from getpass import getpass


@click.command()
class Config:
    def __init__(self):
        ready = self._load()

        if not ready:
            self.configure()

        elif ready:
            self.unlock()

    def _load(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        ready = self.loaded()

        self.key = None
        self.secret = None

        return ready

    def loaded(self):
        return self.config.has_section('creds')

    def ready(self):
        return self.key is not None and self.secret is not None

    def configure(self):
        print('-- API Configuration --')

        check = False
        password = getpass('Enter your password: ')
        while check != password:
            check = getpass('Re-enter your password: ')
            if check == password:
                break

        password = password.encode()
        key = input('API Key: ').strip().encode()
        secret = input('API Secret: ').strip().encode()

        self.key = key
        self.secret = secret

        print('Encrypting your credentials...')
        key = privy.hide(key, password, security=5)
        secret = privy.hide(secret, secret, security=5)

        creds = {'key': key, 'secret': secret}
        self.config['creds'] = creds
        self.config.write(open('config.ini', 'w'))

    def unlock(self):
        password = getpass('Enter your password: ')
        password = password.encode()
        print('Unlocking encrypted credentials...')

        try:
            self.key = privy.peek(self.config['creds']['key'], password)
            self.secret = privy.peek(self.config['creds']['secret'], password)
        except ValueError:
            print('Incorrect Password!')
            exit(1)


if __name__ == '__main__':
    Config()
