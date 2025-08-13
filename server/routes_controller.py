from server.controllers.auth import auth_bp
from server.controllers.debt import debt_bp
from server.controllers.business import business_bp
from server.controllers.item import item_bp
from server.controllers.dashboard import dashboard_bp
from server.controllers.settings import settings_bp
from server.controllers.onboarding import onboarding_bp
from server.controllers.finance import finance_bp
from server.controllers.changelog import changelog_bp


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(debt_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(changelog_bp)