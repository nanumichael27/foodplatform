import os

import click
from flask import Flask
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate


db = SQLAlchemy()
login_manager = LoginManager()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'karma.sqlite'),
        SQLALCHEMY_DATABASE_URI='mysql+mysqlconnector://sc09lh1jmmfw8esb:''n205tplh7ep7stmf@grp6m5lz95d9exiz.cbetxkdyhwsb.us-east-1.rds.amazonaws.com/karma',
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        UPLOAD_FOLDER='uploads',
        
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # initialize Flask sqlalchemy and the init-db command
    db.init_app(app)
    app.cli.add_command(init_db_command)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    migrate = Migrate(app, db)

    from karma.auth.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from . import auth, shop, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(shop.bp)
    app.register_blueprint(admin.bp)
    app.add_url_rule('/', endpoint='index')

    return app


def init_db():
    db.drop_all()
    db.create_all()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")