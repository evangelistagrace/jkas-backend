"""API endpoint definitions for /auth namespace."""
from http import HTTPStatus
from flask_restx import Namespace, Resource
from app.main.util.dto import (
    createFeedback_reqparser, 
    deleteFeedbackList_reqparser,
    updateFeedback_reqparser,
    submitApplication_reqparser,
    getInvoice_reqparser,
    createInvoice_reqparser,
    updateInvoice_reqparser,
    )

from app.main.service.agensi_service import(
    getAgensi,
    getFeedbackList,
    deleteFeedbackList,
    getFeedback,
    createFeedback,
    updateFeedback,
    getContractorList,
    getInvoice,
    createInvoice,
    updateInvoice,
    )

agensi_ns = Namespace(name="agensi", validate=True)

@agensi_ns.route("/getAgensi/<np_number>", endpoint="get_agensi")
class GetAgensi(Resource):
    """  Handles HTTP request to URL: /agensi/getAgensi """
    @agensi_ns.response(int(HTTPStatus.OK), "Agensi Fetched")
    @agensi_ns.response(int(HTTPStatus.NOT_FOUND), "Agensi not found ! Please try again.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self, np_number):
        """ Search for Agensi """
        agensi_result = getAgensi(np_number)
        return agensi_result

@agensi_ns.route("/getFeedbackList/<np_number>", endpoint="get_feedback_list")
class GetFeedbackList(Resource):
    """  Handles HTTP request to URL: /agensi/getFeedbackList """
    @agensi_ns.response(int(HTTPStatus.OK), "Feedback List Fetched")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self, np_number):
        """ Search for Feedback List """
        feedback_result = getFeedbackList(np_number)
        return feedback_result

@agensi_ns.route("/deleteFeedbackList", endpoint="delete_feedback_list")
class DeleteFeedbackList(Resource):
    """ Handles HTTP requests to URL: /public/deleteFeedbackList. """

    @agensi_ns.expect(deleteFeedbackList_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "List of Feedback Deleted Successfully")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def delete(self):
        """ Delete list of Feedback."""
        request_data=    deleteFeedbackList_reqparser.parse_args() 
        return deleteFeedbackList(request_data)
    
@agensi_ns.route("/getFeedback/<feedback_id>", endpoint="get_feedback")
class GetFeedback(Resource):
    """  Handles HTTP request to URL: /agensi/getFeedback """
    @agensi_ns.response(int(HTTPStatus.OK), "Feedback Fetched")
    @agensi_ns.response(int(HTTPStatus.NOT_FOUND), "Feedback not found ! Please try again.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self, feedback_id):
        """ Search for Single Feedback """
        feedback_result = getFeedback(feedback_id)
        return feedback_result

@agensi_ns.route("/createFeedback", endpoint="create_feedback")
class CreateFeedback(Resource):
    """  Handles HTTP request to URL: /agensi/createFeedback """
    @agensi_ns.expect(createFeedback_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "Feedback Created")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ create Feedback """
        request_data = createFeedback_reqparser.parse_args()
        return createFeedback(request_data)
    
@agensi_ns.route("/updateFeedback/<feedback_id>", endpoint="update_feedback")
class UpdateFeedback(Resource):
    """  Handles HTTP request to URL: /agensi/updateFeedback """
    @agensi_ns.expect(updateFeedback_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "Feedback Updated")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def put(self,feedback_id):
        """ create Feedback """
        request_data = updateFeedback_reqparser.parse_args()
        return updateFeedback(feedback_id,request_data)
 
@agensi_ns.route("/getContractorList", endpoint="get_contractor_list")
class GetContractorList(Resource):
    """Handles HTTP requests to URL: /agensi/getContractorList."""

    @agensi_ns.response(int(HTTPStatus.OK), "Contractor List Fetched")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Search Invoice Form"""
        return getContractorList()
            
@agensi_ns.route("/getInvoice", endpoint="get_invoice")
class GetInvoice(Resource):
    """Handles HTTP requests to URL: /agensi/getInvoice."""

    @agensi_ns.expect(getInvoice_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "Payment Claim Form Added")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Search Invoice Form"""
        
        request_data = getInvoice_reqparser.parse_args()
        return getInvoice(request_data)

@agensi_ns.route("/createInvoice", endpoint="create_invoice")
class CreateInvoice(Resource):
    """Handles HTTP requests to URL: /agensi/createInvoice."""

    @agensi_ns.expect(createInvoice_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "Payment Claim Form Added")
    @agensi_ns.response(int(HTTPStatus.FAILED_DEPENDENCY), "Payment Claim Not Added")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Add Inovicie Form"""
        
        request_data = createInvoice_reqparser.parse_args()
        return createInvoice(request_data)

@agensi_ns.route("/updateInvoice", endpoint="modify_payment_claim")
class UpdateInvoice(Resource):
    """Handles HTTP requests to URL: /agensi/updateInvoice."""

    @agensi_ns.expect(updateInvoice_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "Payment Claim Form Added")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def put(self):
        """ Update Invoice Form"""
        
        request_data = updateInvoice_reqparser.parse_args()
        return updateInvoice(request_data)
