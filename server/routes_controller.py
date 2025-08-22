from server.controllers.auth import auth_bp
from server.controllers.debt import debt_bp
from server.controllers.business import business_bp
from server.controllers.item import item_bp
from server.controllers.dashboard import dashboard_bp
from server.controllers.settings import settings_bp
from server.controllers.onboarding import onboarding_bp
from server.controllers.finance import finance_bp
from server.controllers.changelog import changelog_bp
from server.controllers.customer import customer_bp
from server.controllers.payment import payment_bp
from server.controllers.reminder import reminder_bp

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
    app.register_blueprint(customer_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(reminder_bp)