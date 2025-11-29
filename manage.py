import click
from flask.cli import with_appcontext
from app import app, db

@click.group()
def cli():
    """Management commands for MediQueue."""
    pass

@click.command()
@with_appcontext
def recreate_db():
    """Destroys and recreates the database."""
    db.drop_all()
    db.create_all()
    print("Database recreated.")

cli.add_command(recreate_db)

if __name__ == '__main__':
    cli()
