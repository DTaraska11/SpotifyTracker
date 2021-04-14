import os

from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    application = Flask(__name__, instance_relative_config=True)
    application.config.from_mapping(
        SECRET_KEY='',
        DATABASE=os.path.join(application.instance_path, 'playlistTracker.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        application.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        application.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(application.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @application.route('/hello')
    def hello():
        return 'Hello, World!'

    import db
    db.init_app(application)

    import auth
    application.register_blueprint(auth.bp)

    import playlistTracker
    application.register_blueprint(playlistTracker.bp)
    application.add_url_rule('/', endpoint='home')

    return application

application = create_app()