import logging

from models.models import User
from routers.routers import router
from routers.websoket import websoket
from utils.api_router import api
from routers.auth import auth_bp
from utils.db_init import db
from models.models import *
from config import Config
from utils.socketio import socketio
from utils.migrate import migrate
from utils.jinja_filters import format_views, time_since_upload, format_subscribers
from utils.admin_pannel import admin

from flask import Flask, session

logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
app.config.from_object(obj=Config)

@app.after_request
def add_header(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.context_processor
def utility_processor():
    
    def is_authenticated():
        return 'user_id' in session

    def get_user_role():
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                return user.role.name
        return None

    return dict(is_auth=is_authenticated(), user_role=get_user_role())

# init
db.init_app(app=app)
socketio.init_app(app=app)
migrate.init_app(app=app, db=db)
admin.init_app(app=app)
app.permanent_session_lifetime = timedelta(days=7)
# blueprints
app.register_blueprint(blueprint=router)
app.register_blueprint(blueprint=websoket)
app.register_blueprint(blueprint=api, url_prefix='/api')
app.register_blueprint(blueprint=auth_bp, url_prefix='/auth')

# reg format
app.jinja_env.filters['format_views'] = format_views
app.jinja_env.filters['format_date'] = time_since_upload
app.jinja_env.filters['format_subscribers'] = format_subscribers

def create_table():
    try:
        with app.app_context():
            db.create_all()
            print("DB CONNECTED")
    except Exception as e:
        print(f"[DB ERROR] {e}")


def main():
    create_table()
    app.run(debug=True)


if __name__ == "__main__":
    main()
