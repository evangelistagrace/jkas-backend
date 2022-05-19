"""API blueprint configuration."""
from flask import Blueprint
from flask_restx import Api

from app.main.controller.public_controller import public_ns
from app.main.controller.agensi_controller import agensi_ns
from app.main.controller.dbkl_controller import dbkl_ns
from app.main.controller.resources_controller import resources_ns


api_bp = Blueprint("api", __name__)
authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = Api(
    api_bp,
    version="1.0",
    title="JKAS API",
    description="Welcome to the Swagger UI of JKAS API",
    authorizations=authorizations,
)

api.add_namespace(public_ns, path="/public")
api.add_namespace(agensi_ns, path="/agensi")
api.add_namespace(dbkl_ns, path="/dbkl")
api.add_namespace(resources_ns, path="/jkas_resourses")
