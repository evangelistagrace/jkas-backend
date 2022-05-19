"""API endpoint definitions for /auth namespace."""
from http import HTTPStatus
from flask_restx import Namespace, Resource
from app.main.util.dto import (
    createFeedback_reqparser, deleteFeedbackList_reqparser, updateFeedback_reqparser, submitApplication_reqparser,
    getInvoice_reqparser,createInvoice_reqparser,updateInvoice_reqparser,
    )

from app.main.service.agensi_service import(
    getAgensi,getProfileInformation,getFeedbackList,getOrganisationList,deleteFeedbackList,getFeedback,createFeedback,getLastFeedback,
    updateFeedback,logout,getContractorList,getInvoice,createInvoice,updateInvoice,
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

@agensi_ns.route("/getProfileInformation", endpoint="agensi_get_profile_information")
class GetProfileInformation(Resource):
    """Handles HTTP requests to URL: /agensi/getProfileInformation."""

    @agensi_ns.doc(security="Bearer")
    @agensi_ns.response(int(HTTPStatus.OK), "Profile Information fetched")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """Get Profile Information of DBKL User"""
        return getProfileInformation()
    
@agensi_ns.route("/getOrganisationList", endpoint="get_organisation_list")
class GetOrganisationList(Resource):
    """Handles HTTP requests to URL: /agensi/getOrganisationList."""

    @agensi_ns.response(int(HTTPStatus.OK), "Organisation List Fetched")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Get Organisation List"""
        return getOrganisationList()
    
@agensi_ns.route("/getFeedbackList", endpoint="get_feedback_list")
class GetFeedbackList(Resource):
    """  Handles HTTP request to URL: /agensi/getFeedbackList """
    @agensi_ns.doc(security="Bearer")
    @agensi_ns.response(int(HTTPStatus.OK), "Feedback List Fetched")
    @agensi_ns.response(int(HTTPStatus.NOT_FOUND), "Feedback List Not Found")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Get Feedback List """
        return getFeedbackList()

@agensi_ns.route("/deleteFeedbackList", endpoint="delete_feedback_list")
class DeleteFeedbackList(Resource):
    """ Handles HTTP requests to URL: /public/deleteFeedbackList. """

    @agensi_ns.doc(security="Bearer")
    @agensi_ns.expect(deleteFeedbackList_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "List of Feedback Deleted Successfully")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def delete(self):
        """ Delete list of Feedback."""
        request_data=deleteFeedbackList_reqparser.parse_args() 
        return deleteFeedbackList(request_data)
    
@agensi_ns.route("/getFeedback/<feedback_id>", endpoint="get_feedback")
class GetFeedback(Resource):
    """  Handles HTTP request to URL: /agensi/getFeedback """
    @agensi_ns.doc(security="Bearer")
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
    @agensi_ns.doc(security="Bearer")
    @agensi_ns.expect(createFeedback_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "Feedback Created")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ create Feedback """
        request_data = createFeedback_reqparser.parse_args()
        return createFeedback(request_data)

@agensi_ns.route("/getLastFeedback", endpoint="get_last_feedback")
class GetLastFeedback(Resource):
    """  Handles HTTP request to URL: /agensi/getLastFeedback """
    @agensi_ns.doc(security="Bearer")
    @agensi_ns.response(int(HTTPStatus.OK), "Last Feedback Fetched")
    @agensi_ns.response(int(HTTPStatus.NOT_FOUND), "Feedback not found ! Please try again.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Search for Last Feedback """
        feedback_result = getLastFeedback()
        return feedback_result
    
@agensi_ns.route("/updateFeedback/<feedback_id>", endpoint="update_feedback")
class UpdateFeedback(Resource):
    """  Handles HTTP request to URL: /agensi/updateFeedback """
    @agensi_ns.doc(security="Bearer")
    @agensi_ns.expect(updateFeedback_reqparser)
    @agensi_ns.response(int(HTTPStatus.CREATED), "Feedback Updated")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def put(self,feedback_id):
        """ create Feedback """
        request_data = updateFeedback_reqparser.parse_args()
        return updateFeedback(feedback_id,request_data)
 
@agensi_ns.route("/logout", endpoint="agensi_auth_logout")
class AgensiLogout(Resource):
    """Handles HTTP requests to URL: /agensi/logout."""
    @agensi_ns.doc(security="Bearer")
    @agensi_ns.response(int(HTTPStatus.OK), "Log out succeeded, token is no longer valid.")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Add token to blacklist, deauthenticating the current user."""
        return logout()
    
@agensi_ns.route("/getContractorList", endpoint="get_contractor_list")
class GetContractorList(Resource):
    """Handles HTTP requests to URL: /agensi/getContractorList."""

    @agensi_ns.response(int(HTTPStatus.OK), "Contractor List Fetched")
    @agensi_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @agensi_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Get Contractor List"""
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
