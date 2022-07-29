"""Flask CLI/Application entry point."""
from datetime import date
import os
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_cors import CORS
from OpenSSL import SSL

from app.main import create_app, db
from app.main.models.models import MasterUser
from app import api_bp
from OpenSSL import SSL

from applogger import logger
from flask_sqlalchemy import get_debug_queries
# import flask_monitoringdashboard as dashboard

app = create_app('dev')
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.register_blueprint(api_bp, url_prefix="/api")
app.app_context().push()

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


app.config['SQLALCHEMY_RECORD_QUERIES'] = True
""" 
@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= 0:
            logger.info(f"{query.statement, query.parameters, query.duration, query.context}")
    return response
"""
# dashboard.bind(app)
      
@manager.command
def run():
    context = ('httpd.crt','httpd.key')
    app.run(host='0.0.0.0', debug=True, ssl_context=context)

if __name__=="__main__":
    manager.run()