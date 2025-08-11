from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from dotenv import load_dotenv
from server.extension import db, migrate, jwt
from server.routes_controller import register_routes
import os
from datetime import timedelta

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Enhanced CORS configuration
    CORS(app,
         supports_credentials=True,
         origins=[
             "http://localhost:5173",
             "http://127.0.0.1:5173"
         ],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         expose_headers=["Authorization"],
         max_age=3600
    )
    
    # JWT Configuration
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"
    
    # Database Configuration
    app.config.from_prefixed_env()
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    api = Api(app)
    jwt.init_app(app)

    # Register routes
    register_routes(app)
    
    @app.route('/')
    def home():
        return {"message": "Welcome to paysync API"}
    
    # Add JWT error handlers
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {
            "message": "Invalid token",
            "error": str(error)
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {
            "message": "Missing authorization token",
            "error": str(error)
        }, 401
    
    
    return app

app = create_app()