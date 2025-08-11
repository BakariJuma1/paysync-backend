from server.controllers.auth import auth_bp
from server.controllers.debt import debt_bp
from server.controllers.business import business_bp
from server.controllers.item import item_bp



def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(debt_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(item_bp)
    