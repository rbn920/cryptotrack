import click

@click.command()
@click.option('--passwd', prompt='Enter password')
def login(passwd):
    click.echo(passwd)


if __name__ == '__main__':
    login()


