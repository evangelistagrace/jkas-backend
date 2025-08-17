"""API endpoint definitions for /auth namespace."""
from http import HTTPStatus
from flask_restx import Namespace, Resource
from app.main.service.resources_service import (readPDF, readImage, getPDF, getImage, getVideo)
from app.main.controller.public_controller import public_ns

resources_ns = Namespace(name="jkas_resourses", validate=True)

@resources_ns.route("/public/pdfs/<filename>", endpoint="readpdf")
class ReadPDF(Resource):
    """  Handles HTTP request to URL: /public/getPdf/ """
    @public_ns.doc(security="Bearer")
    @resources_ns.response(int(HTTPStatus.OK), "PDF Fetched")
    @resources_ns.response(int(HTTPStatus.NOT_FOUND), "PDF not found ! Please try again.")
    @resources_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    @resources_ns.produces(["application/pdf"])
    def get(self, filename):
        """ Search for PDF """
        pdf_result = readPDF(filename)
        return pdf_result
    
@resources_ns.route("/public/images/<filename>", endpoint="readimage")
class ReadImage(Resource):
    """  Handles HTTP request to URL: /public/getImage/ """
    @public_ns.doc(security="Bearer")
    @resources_ns.response(int(HTTPStatus.OK), "Image Fetched")
    @resources_ns.response(int(HTTPStatus.NOT_FOUND), "Image not found ! Please try again.")
    @resources_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    @resources_ns.produces(["image/png"])
    def get(self, filename):
        """ Search for Image """
        image_result = readImage(filename)
        return image_result

@resources_ns.route("/free/pdfs/<filename>", endpoint="get_pdf")
class GetPDF(Resource):
    """  Handles HTTP request to URL: /public/getPdf/ """
    @resources_ns.response(int(HTTPStatus.OK), "PDF Fetched")
    @resources_ns.response(int(HTTPStatus.NOT_FOUND), "PDF not found ! Please try again.")
    @resources_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    @resources_ns.produces(["application/pdf"])
    def get(self, filename):
        """ Search for PDF """
        pdf_result = getPDF(filename)
        return pdf_result


@resources_ns.route("/free/docs/<filename>", endpoint="get_docs")
class GetDocs(Resource):
    """  Handles HTTP request to URL: /public/getDocs/ """
    @resources_ns.response(int(HTTPStatus.OK), "Docs Fetched")
    @resources_ns.response(int(HTTPStatus.NOT_FOUND), "Docs not found ! Please try again.")
    @resources_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    @resources_ns.produces(["application/pdf"])
    def get(self, filename):
        """ Search for PDF """
        pdf_result = getPDF(filename)
        return pdf_result
    
@resources_ns.route("/free/images/<filename>", endpoint="get_image")
class GetImage(Resource):
    """  Handles HTTP request to URL: /public/getImage/ """
    @resources_ns.response(int(HTTPStatus.OK), "Image Fetched")
    @resources_ns.response(int(HTTPStatus.NOT_FOUND), "Image not found ! Please try again.")
    @resources_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    @resources_ns.produces(["image/png"])
    def get(self, filename):
        """ Search for Image """
        image_result = getImage(filename)
        return image_result


@resources_ns.route("/free/videos/<filename>", endpoint="readvideo")
class ReadImage(Resource):
    @public_ns.doc(security="Bearer")
    @resources_ns.response(int(HTTPStatus.OK), "Video Fetched")
    @resources_ns.response(int(HTTPStatus.NOT_FOUND), "Video not found ! Please try again.")
    @resources_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    @resources_ns.produces(["image/png"])
    def get(self, filename):
        """ Search for Video """
        video_result = getVideo(filename)
        return video_result