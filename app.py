from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restful import Api, Resource
from dotenv import load_dotenv
from server.extension import db,migrate,jwt

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app,
         supports_credentials=True,
         origins=[
             "http://localhost:5173"
            ]
        )
    app.config.from_prefixed_env()
    db.init_app(app)
    migrate.init_app(app,db)
    api=Api(app)
    jwt.init_app(app)


    @app.route('/')
    def home():
        return {"message":"Welcome to paysync API"}
    
    return app
app = create_app()
