from flask import Flask

from auth import login_manager
from config import get_app_secret_key
from db import init_database
from routes.auth_main import register_auth_main_routes
from routes.dashboard import register_dashboard_routes
from routes.public import register_public_routes
from routes.reservations import register_reservations_routes
from routes.stock_pages import register_stock_routes


def create_app():
    app = Flask(__name__)
    app.secret_key = get_app_secret_key()

    login_manager.init_app(app)
    login_manager.login_view = "login"
    init_database()

    register_public_routes(app)
    register_auth_main_routes(app)
    register_reservations_routes(app)
    register_dashboard_routes(app)
    register_stock_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
