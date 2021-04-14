"""API endpoint definitions for /auth namespace."""
from http import HTTPStatus
from flask import jsonify
from flask_restx import Namespace, Resource
from app.main.util.dto import (
    masterUser_model, createAnnouncement_reqparser, updateAnnouncement_reqparser, deleteAnnouncement_reqparser, createManual_reqparser, updateManual_reqparser, deleteManual_reqparser, public_login_reqparser, public_register_reqparser, public_otp_reqparser, public_edit_reqparser, 
    forgot_reqparser, validateotp_reqparser, newPassword_reqparser, submitApplication_reqparser, deleteApplication_reqparser, 
    updatesiteVisitInformation_reqparser, deleteSiteVisitInformation_reqparser, addNonComplianceForm_reqparser, updateNonComplianceForm_reqparser, submitRating_reqparser, uploadFile_reqparser, getCoordinates_reqparser, mapKawasanPerkhidmatan_reqparser)
from app.main.service.public_service import (
    getAnnouncement, createAnnouncement, updateAnnouncement, deleteAnnouncementList, getManual, createManual, updateManual, deleteManualList, getGalleryPhoto, triggerRegistration, completeRegistration, login, logout, forgotPassword, resetPassword, viewApplicationList, deleteApplicationList,
    submitApplication, viewApplicationDetails, sitevisitInformation, updateSiteVisitInformation, deleteSiteVisitInformation, addNonComplianceForm, getNonComplianceForm, updateNonComplianceForm, submitRating, uploadFile, getCoordinates, mapKawasanPerkhidmatan)

public_ns = Namespace(name="public", validate=True)
public_ns.models[masterUser_model.name] = masterUser_model

@public_ns.route("/getAnnouncement", endpoint="get_announcement")
class GetAnnouncement(Resource):
    """ Handles HTTP requests to URL: /public/getAnnouncement. """

    # #@public_ns.doc(security="Bearer")
    @public_ns.response(int(HTTPStatus.OK), "List of public announcement Fetched Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Reutrn list of Announcement."""
        return getAnnouncement()

@public_ns.route("/createAnnouncement", endpoint="create_announcement")
class CreateAnnouncement(Resource):
    """ Handles HTTP requests to URL: /public/createAnnouncement. """

    @public_ns.doc(security="Bearer")
    @public_ns.expect(createAnnouncement_reqparser)
    @public_ns.response(int(HTTPStatus.CREATED), "List of public announcement updated Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Create list of Announcement."""
        request_data = createAnnouncement_reqparser.parse_args()
        return createAnnouncement(request_data)

@public_ns.route("/updateAnnouncement/<announcement_id>", endpoint="update_announcement")
class UpdateAnnouncement(Resource):
    """ Handles HTTP requests to URL: /public/updateAnnouncement. """
    @public_ns.doc(security="Bearer")
    @public_ns.expect(updateAnnouncement_reqparser)
    @public_ns.response(int(HTTPStatus.CREATED), "public announcement updated Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def put(self, announcement_id):
        """ Create list of Announcement."""
        request_data = updateAnnouncement_reqparser.parse_args()
        return updateAnnouncement(request_data, announcement_id)


@public_ns.route("/deleteAnnouncementList", endpoint="delete_announcement_list")
class DeleteAnnouncementList(Resource):
    """ Handles HTTP requests to URL: /public/deleteAnnouncementList. """

    @public_ns.doc(security="Bearer")
    @public_ns.expect(deleteAnnouncement_reqparser)
    @public_ns.response(int(HTTPStatus.CREATED), "List of Announcement Deleted Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def delete(self):
        """ Delete list of Applications."""
        request_data = deleteAnnouncement_reqparser.parse_args() 
        return deleteAnnouncementList(request_data)
    
@public_ns.route("/getManual", endpoint="get_manual")
class GetManual(Resource):
    """ Handles HTTP requests to URL: /public/getManual. """

    # #@public_ns.doc(security="Bearer")
    @public_ns.response(int(HTTPStatus.OK), "List of Manual Fetched Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Reutrn list of Manual Pdf Paths."""
        return getManual()

@public_ns.route("/createManual", endpoint="create_manual")
class CreateManual(Resource):
    """ Handles HTTP requests to URL: /public/CreateManual. """

    @public_ns.doc(security="Bearer")
    @public_ns.expect(createManual_reqparser)
    @public_ns.response(int(HTTPStatus.CREATED), "Manual Created Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Create Manual."""
        request_data = createManual_reqparser.parse_args()
        return createManual(request_data)

@public_ns.route("/updateManual/<mannual_id>", endpoint="update_manual")
class UpdateManual(Resource):
    """ Handles HTTP requests to URL: /public/updateManual. """
    @public_ns.doc(security="Bearer")
    @public_ns.expect(updateManual_reqparser)
    @public_ns.response(int(HTTPStatus.CREATED), "Manual updated Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def put(self, mannual_id):
        """ Update Manual."""
        request_data = updateManual_reqparser.parse_args()
        return updateManual(request_data,mannual_id)
    
@public_ns.route("/deleteManualList", endpoint="delete_manual_list")
class DeleteManualList(Resource):
    """ Handles HTTP requests to URL: /public/deleteManualList. """

    @public_ns.doc(security="Bearer")
    @public_ns.expect(deleteManual_reqparser)
    @public_ns.response(int(HTTPStatus.CREATED), "List of Announcement Deleted Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def delete(self):
        """ Delete list of Applications."""
        request_data = deleteManual_reqparser.parse_args() 
        return deleteManualList(request_data)
        
@public_ns.route("/getGalleryPhoto", endpoint="get_gallery_photo")
class GetGalleryPhoto(Resource):
    """ Handles HTTP requests to URL: /public/getGalleryPhoto. """

    #@public_ns.doc(security="Bearer")
    @public_ns.response(int(HTTPStatus.OK), "Photo Gallery List Fetched Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    # @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Reutrn list of Photo Paths."""
        return getGalleryPhoto()
    
@public_ns.route("/triggerRegistration", endpoint="public_trigger_registration")
class TriggerRegistration(Resource):
    """Handles HTTP requests to URL: /public/triggerRegistration."""

    @public_ns.expect(public_register_reqparser)
    @public_ns.response(int(HTTPStatus.OK), "OTP sent Successfully")
    @public_ns.response(int(HTTPStatus.CONFLICT), "alamat_emel address is already registered.")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.NOT_ACCEPTABLE), "OTP can't be sent to this region")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Initiate Registration from here"""
        request_data = public_register_reqparser.parse_args()
        return triggerRegistration(request_data)

@public_ns.route("/completeRegistration", endpoint="public_completeRegistration")
class CompleteRegistration(Resource):
    """Handles HTTP requests to URL: /public/completeRegistration."""
    
    @public_ns.expect(public_otp_reqparser)
    @public_ns.response(int(HTTPStatus.OK), "OTP validated!")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        """ OTP verification and Register public user """
        request_data = public_otp_reqparser.parse_args()
        return completeRegistration(request_data)

@public_ns.route("/login", endpoint="public_login")
class LoginUser(Resource):
    """Handles HTTP requests to URL: /public/login."""

    @public_ns.expect(public_login_reqparser)
    @public_ns.response(int(HTTPStatus.OK), "Login succeeded.")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "email or password does not match")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Authenticate an existing user and return an access token."""
        request_data = public_login_reqparser.parse_args()
        return login(request_data)

@public_ns.route("/logout", endpoint="public_auth_logout")
class LogoutUser(Resource):
    """Handles HTTP requests to URL: /public/logout."""

    @public_ns.doc(security="Bearer")
    @public_ns.response(int(HTTPStatus.OK), "Log out succeeded, token is no longer valid.")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Add token to blacklist, deauthenticating the current user."""
        return logout()


@public_ns.route("/forgotPassword", endpoint="forgot_password")
class ForgotPassword(Resource):
    """  Handles HTTP request to URL: /public/forgotPassword """
    @public_ns.expect(forgot_reqparser)
    @public_ns.response(int(HTTPStatus.OK), "Reset password link sent successfully")
    @public_ns.response(int(HTTPStatus.NOT_FOUND), "id_card_no or email not registered ! Please try again.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Enter email of the User who's password is forgotten """
        request_data = forgot_reqparser.parse_args()
        return forgotPassword(request_data)

@public_ns.route("/resetPassword", endpoint="reset_password")
class ResetPassword(Resource):
    """ Handles HTTP request to URL: /public/resetPassword """
    @public_ns.expect(newPassword_reqparser)
    @public_ns.response(int(HTTPStatus.OK), "kata_laluan updated successfully!")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Bad request! Please try again.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def put(self):
        """ Change password for an User who has forgotten his password """
        request_data = newPassword_reqparser.parse_args()
        return resetPassword(request_data)

@public_ns.route("/viewApplicationList", endpoint="view_application_list")
class ViewApplicationList(Resource):
    """ Handles HTTP requests to URL: /public/listApplication. """

    @public_ns.doc(security="Bearer")
    @public_ns.response(int(HTTPStatus.OK), "List of Application Fetched Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Reutrn list of Applications."""
        return viewApplicationList()
    
@public_ns.route("/deleteApplicationList", endpoint="delete_application_list")
class DeleteApplicationList(Resource):
    """ Handles HTTP requests to URL: /public/deleteApplicationList. """

    @public_ns.doc(security="Bearer")
    @public_ns.expect(deleteApplication_reqparser)
    @public_ns.response(int(HTTPStatus.CREATED), "List of Application Deleted Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def delete(self):
        """ Delete list of Applications."""
        request_data = deleteApplication_reqparser.parse_args() 
        return deleteApplicationList(request_data)
    
@public_ns.route("/submitApplication", endpoint="submit_application")
class SubmitApplication(Resource):
    """ Handles HTTP requests to URL: /public/submitApplication. """
    
    @public_ns.doc(security="Bearer")
    @public_ns.expect(submitApplication_reqparser) 
    @public_ns.response(int(HTTPStatus.CREATED), "Application added successfully!")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Bad request! Please try again.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Create New Application Form"""
        request_data = submitApplication_reqparser.parse_args() 
        
        return submitApplication(request_data)

@public_ns.route("/viewApplicationDetails", endpoint="view_application_details")
class ViewApplicationDetails(Resource):
    """ Handles HTTP requests to URL: /public/viewApplicationDetails. """

    @public_ns.doc(security="Bearer")
    @public_ns.response(int(HTTPStatus.OK), "List of Application Fetched Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """ Reutrn list of Applications."""
        return viewApplicationDetails()

@public_ns.route("/siteVisitInformation/<no_siri_permohonan>", endpoint="site_visit_information")
class SiteVisitInformation(Resource):
    """ Handles HTTP requests to URL: /public/siteVisitInformation. """

    @public_ns.doc(security="Bearer")
    @public_ns.response(int(HTTPStatus.OK), "Site Visit Information Fetched Successfully")
    @public_ns.response(int(HTTPStatus.NOT_FOUND), "Site Visit Information not found")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def get(self,no_siri_permohonan):
        """ Return Site Visit Information."""
        site_info_list = sitevisitInformation(no_siri_permohonan)
        return site_info_list

@public_ns.route("/updateSiteVisitInformation/<site_id>", endpoint="update_site_visit_information")
class UpdateSiteVisitInformation(Resource):
    """Handles HTTP requests to URL: /public/updatesiteVisitInformation/<site_id>."""
    
    @public_ns.doc(security="Bearer")
    @public_ns.expect(updatesiteVisitInformation_reqparser)
    @public_ns.response(int(HTTPStatus.OK), "Detailed Meeting Form Updated.")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,site_id):
        """ Update Site Visit Information."""
        request_data = updatesiteVisitInformation_reqparser.parse_args()
        return updateSiteVisitInformation(site_id,request_data)

@public_ns.route("/deleteSiteVisitInformation", endpoint="delete_site_visit_information")
class DeleteSiteVisitInformation(Resource):
    """ Handles HTTP requests to URL: /public/deleteSiteVisitInformation. """

    @public_ns.doc(security="Bearer")
    @public_ns.expect(deleteSiteVisitInformation_reqparser)
    @public_ns.response(int(HTTPStatus.CREATED), "List of Site Visit Information Deleted Successfully")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def delete(self):
        """ Delete list of Site Visit Information."""
        request_data =deleteSiteVisitInformation_reqparser.parse_args() 
        return deleteSiteVisitInformation(request_data)
    
@public_ns.route("/addNonComplianceForm", endpoint="add_non_compliance_form")
class AddNonComplianceForm(Resource):
    """ Handles HTTP requests to URL: /public/submitRating. """
    
    @public_ns.doc(security="Bearer")
    @public_ns.expect(addNonComplianceForm_reqparser) 
    @public_ns.response(int(HTTPStatus.CREATED), "Non-compliance form added successfully!")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Bad request! Please try again.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Create New Non Compliance Form"""
        request_data = addNonComplianceForm_reqparser.parse_args() 
        
        return addNonComplianceForm(request_data)

@public_ns.route("/getNonComplianceForm/<no_siri_permohonan>", endpoint="get_noncompliance_form")
class GetNonComplianceForm(Resource):
    """ Handles HTTP requests to URL: /public/siteVisitInformation. """

    @public_ns.doc(security="Bearer")
    @public_ns.response(int(HTTPStatus.OK), "Non Compliance Form Info Fetched Successfully")
    @public_ns.response(int(HTTPStatus.NOT_FOUND), "Non Compliance Form Info not found")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def get(self,no_siri_permohonan):
        """ Return Non Compliance Form Info."""
        non_compliance_info_list = getNonComplianceForm(no_siri_permohonan)
        return non_compliance_info_list

@public_ns.route("/updateNonComplianceForm/<non_compliance_id>", endpoint="update_non_compliance_form")
class UpdateNonComplianceForm(Resource):
    """ Handles HTTP requests to URL: /public/submitRating. """
    
    @public_ns.doc(security="Bearer")
    @public_ns.expect(updateNonComplianceForm_reqparser) 
    @public_ns.response(int(HTTPStatus.CREATED), "Non-compliance form updated successfully!")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Bad request! Please try again.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def put(self,non_compliance_id):
        """ Update Non-Compliance Form"""
        request_data = updateNonComplianceForm_reqparser.parse_args() 
        
        return updateNonComplianceForm(non_compliance_id,request_data)
    
@public_ns.route("/submitRating", endpoint="submit_rating")
class SubmitRating(Resource):
    """ Handles HTTP requests to URL: /public/submitRating. """

    @public_ns.doc(security="Bearer")
    @public_ns.expect(submitRating_reqparser) 
    @public_ns.response(int(HTTPStatus.CREATED), "Rating Submitted Successfully")
    @public_ns.response(int(HTTPStatus.NOT_FOUND), "Site Visit Information not found")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ Feedback and Rating Submission."""
        request_data = submitRating_reqparser.parse_args()
        return submitRating(request_data)
    
@public_ns.route("/uploadFile", endpoint="upload_file")    
class UploadFile(Resource):
    """ Handles HTTP requests to URL: /public/uploadFile. """
    @public_ns.expect(uploadFile_reqparser) 
    @public_ns.response(int(HTTPStatus.CREATED), "Rating Submitted Successfully")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ Upload files to sever """
        request_data = uploadFile_reqparser.parse_args()
        files = request_data.get("file")
        return uploadFile(files)

@public_ns.route("/getCoordinates", endpoint="get_coordinates")
class GetCoordinates(Resource):
    """ Handles HTTP request to URL: /public/getCoordinates """
    @public_ns.expect(getCoordinates_reqparser)
    @public_ns.response(int(HTTPStatus.OK), "Cordinates Fetched successfully!")
    @public_ns.response(int(HTTPStatus.BAD_REQUEST), "Bad request! Please try again.")
    @public_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Get Coordinates of All Lokasi of a Parlimen and Taman """
        request_data = getCoordinates_reqparser.parse_args()
        return getCoordinates(request_data)
    
@public_ns.route("/mapKawasanPerkhidmatan", endpoint="map_kawasan_perkhidmatan")    
class MapKawasanPerkhidmatan(Resource):
    """ Handles HTTP requests to URL: /public/mapKawasanPerkhidmatan. """
    @public_ns.expect(mapKawasanPerkhidmatan_reqparser) 
    @public_ns.response(int(HTTPStatus.CREATED), "map kawasan perkhidmatan fetched Successfully")
    @public_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """fetch map kawasan perkhidmatan  """
        request_data = mapKawasanPerkhidmatan_reqparser.parse_args()
        return mapKawasanPerkhidmatan(request_data)