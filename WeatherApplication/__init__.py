import os

from flask import (Flask, session)
from flask_bootstrap import  Bootstrap
from . import suggest

def create_app(test_config=None):
    """

    :param test_config: instance of test_config
    :return: main flask application
    """

    # creating app
    app = Flask(__name__, instance_relative_config=True)
    Bootstrap(app)
    # needed during deployment
    app.config.from_mapping(
        SECRET_KEY = 'dev',
    )


    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    app.register_blueprint(suggest.bp)
    app.add_url_rule('/', endpoint='index')

    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    return app