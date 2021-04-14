"""API endpoint definitions for /auth namespace."""
from http import HTTPStatus
from flask_restx import Namespace, Resource
from app.main.util.dto import (
    masterUser_model, dbkl_register_reqparser, dbkl_otp_reqparser, dbkl_login_reqparser, newPassword_reqparser, assignRole_reqparser,
    updateMeeting_reqparser, addDetailedMeeting_reqparser, updateDetailedMeeting_reqparser, deleteMeeting_reqparser,
    updateInventoriPengguna_reqparser, deleteInventoriPengguna_reqparser, updateApplication_reqparser, deleteApplicationList_reqparser, 
    updateSiteVisit_reqparser, deleteSitevisitInformation_reqparser,
    updateStatusSemakanDokumen_reqparser, updateAgencyJobPaymentClaimByInbois_reqparser, deleteAgencyJobPaymentClaim_reqparser, addComplaintInvestigation_reqparser, getComplaintInvestigation_reqparser, 
    mtbInquiry_reqparser, mtbCompoundInformation_reqparser, mtbCompoundInfoByMTB_reqparser, addMTBCompoundForm_reqparser,
    sendNotice_reqparser, grafPrestasiBulanan_reqparser, grafAnalisisDanStatistik_reqparser
    )

from app.main.service.dbkl_service import (
    registerDbklUser, completeRegistration, get_logged_in_user, assignRole,
    addDetailedMeeting, getMeeting, listOfDetailedMeeting, listOfMeeting, updateMeeting, deleteListOfMeeting, 
    deleteInventoriPengguna, fetchPublicApplicationDetails, getAgencyJobPaymentClaim, getAgencyJobPaymentClaimByInbois, deleteAgencyJobPaymentClaim, 
    addComplaintInvestigation, getComplaintInvestigation, updateComplaintInvestigation, getInventoriPengguna, deleteInventoriPengguna, getLogPengguna, 
    getMTBCompoundInformation, getMTBCompoundInfoByMTB, addMTBCompoundForm, getCompoundForm, getOmpBaru,getOmpLama, 
    getPublicApplicationList, deletePublicApplicationList, grafAnalisisDanStatistik, grafPrestasiBulanan, 
    login, logout, getMTBOfficersList, getMTBOfficerInfo, getDailyMTBInquiryInforByMTK, getDailyMTBInquiryInforByMTB, sendNotice, updateAgencyJobPaymentClaimByInbois,
    updateDetailedMeeting, updateInventoriPengguna, updatePublicApplicationDetails, updateSiteVisitApplicationList, deletelistOfsitevisitInformation, updateStatusSemakanDokumen, 
    grafJumlahKutipan, grafJumlahPembersihanAwam, getIdPegawai, getLokasi
    )
dbkl_ns = Namespace(name="dbkl", validate=True)

@dbkl_ns.route("/registerDbklUser", endpoint="dbkl_trigger_registration")
class RegisterDbklUser(Resource):
    """Handles HTTP requests to URL: /dbkl/registerDbklUser."""

    @dbkl_ns.expect(dbkl_register_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "OTP sent Successfully")
    @dbkl_ns.response(int(HTTPStatus.CONFLICT), "alamat_emel address is already registered.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.NOT_ACCEPTABLE), "OTP can't be sent to this region")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Initiate Registration from here"""
        request_data = dbkl_register_reqparser.parse_args()
        return registerDbklUser(request_data)

@dbkl_ns.route("/completeRegistration", endpoint="dbkl_completeRegistration")
class CompleteRegistration(Resource):
    """Handles HTTP requests to URL: /dbkl/completeRegistration."""
    
    @dbkl_ns.expect(dbkl_otp_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "OTP validated!")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        """ OTP verification and Register public user """
        request_data = dbkl_otp_reqparser.parse_args()
        return completeRegistration(request_data)

@dbkl_ns.route("/login", endpoint="dbkl_login")
class LoginUser(Resource):
    """Handles HTTP requests to URL: /dbkl/login."""

    @dbkl_ns.expect(dbkl_login_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Login succeeded.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "email or password does not match")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Authenticate an existing user and return an access token."""
        request_data = dbkl_login_reqparser.parse_args()
        return login(request_data)

@dbkl_ns.route("/logout", endpoint="dbkl_logout")
class LogoutUser(Resource):
    """Handles HTTP requests to URL: /dbkl/logout."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Log out succeeded, token is no longer valid.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Add token to blacklist, deauthenticating the current user."""
        return logout()

@dbkl_ns.route("/profileInformation", endpoint="dbkl_profile_information")
class ProfileInformation(Resource):
    """Handles HTTP requests to URL: /public/profileInformation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Token is currently valid.", masterUser_model)
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @dbkl_ns.marshal_with(masterUser_model)
    def get(self):
        """Validate access token and return user info."""
        return get_logged_in_user()

@dbkl_ns.route("/assignRole", endpoint="assign_role")
class AssignRole(Resource):
    """Handles HTTP requests to URL: /dbkl/assignRole."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(assignRole_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "OTP validated!")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self):
        """ Assigning role to dbkl user """
        request_data = assignRole_reqparser.parse_args()
        return assignRole(request_data)

@dbkl_ns.route("/updateMeeting/<no_siri_permohonan>", endpoint="update_meeting")
class UpdateMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/updateMeeting."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateMeeting_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Meeting form updated")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,no_siri_permohonan):
        
        request_data = updateMeeting_reqparser.parse_args()
        return updateMeeting(no_siri_permohonan, request_data)

@dbkl_ns.route("/listOfMeeting", endpoint="list_of_meeting")
class ListOfMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/listOfMeeting."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "list of meeting.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return listOfMeeting()

@dbkl_ns.route("/getMeeting/<meeting_id>", endpoint="get_meeting")
class GetMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/getMeeting/<meeting_id>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "get meeting by meetingId.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self,meeting_id):
        return getMeeting(meeting_id)
    
@dbkl_ns.route("/addDetailedMeeting", endpoint="add_detailed_meeting")
class AddDetailedMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/addDetailedMeeting."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(addDetailedMeeting_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "detailed meeting added")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        request_data = addDetailedMeeting_reqparser.parse_args()
        return addDetailedMeeting(request_data)

@dbkl_ns.route("/listOfDetailedMeeting", endpoint="list_of_detailed_meeting")
class ListOfDetailedMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/listOfDetailedMeeting."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "list of detailed meeting.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return listOfDetailedMeeting()

@dbkl_ns.route("/updateDetailedMeeting/<detailed_meeting_id>", endpoint="update_detailed_meeting")
class UpdateDetailedMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/updateDetailedMeeting."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateDetailedMeeting_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Detailed Meeting Form Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,detailed_meeting_id):
        
        request_data = updateDetailedMeeting_reqparser.parse_args()
        return updateDetailedMeeting(request_data)

@dbkl_ns.route("/deleteListOfMeeting", endpoint="delete_list_of_meeting")
class DeleteListOfMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/deleteListOfMeeting."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteMeeting_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "delete list of meeting.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def delete(self):
        request_data = deleteMeeting_reqparser.parse_args()
        return deleteListOfMeeting(request_data)
    
@dbkl_ns.route("/getInventoriPengguna", endpoint="get_inventori_pengguna")
class GetInventoriPengguna(Resource):
    """Handles HTTP requests to URL: /dbkl/getInventoriPengguna."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "get inventori pengguna")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getInventoriPengguna()

@dbkl_ns.route("/deleteInventoriPengguna", endpoint="delete_inventori_pengguna")
class DeleteInventoriPengguna(Resource):
    """Handles HTTP requests to URL: /dbkl/deleteInventoriPengguna."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteInventoriPengguna_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "get inventori pengguna")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def delete(self):
        request_data = deleteInventoriPengguna_reqparser.parse_args()
        return deleteInventoriPengguna(request_data)
    
@dbkl_ns.route("/getLogPengguna", endpoint="get_log_pengguna")
class GetLogPengguna(Resource):
    """Handles HTTP requests to URL: /dbkl/getLogPengguna."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "get log pengguna")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getLogPengguna()


@dbkl_ns.route("/updateInventoriPengguna/<id_pengguna>", endpoint="update_inventori_pengguna")
class UpdateInventoriPengguna(Resource):
    """Handles HTTP requests to URL: /dbkl/updateInventoriPengguna/<id_pengguna>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateInventoriPengguna_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Detailed Meeting Form Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,id_pengguna):
        request_data = updateInventoriPengguna_reqparser.parse_args()
        return updateInventoriPengguna(id_pengguna,request_data)

@dbkl_ns.route("/getPublicApplicationList", endpoint="get_public_application_list")
class GetPublicApplicationList(Resource):
    """Handles HTTP requests to URL: /dbkl/getLogPengguna."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Public application list fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getPublicApplicationList()

@dbkl_ns.route("/updatePublicApplicationDetails/<no_siri_permohonan>", endpoint="update_public_application_details")
class UpdatePublicApplicationDetails(Resource):
    """Handles HTTP requests to URL: /dbkl/updatePublicApplicationDetails/<no_siri_permohonan>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateApplication_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Public Application Details Form Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,no_siri_permohonan):
        request_data = updateApplication_reqparser.parse_args()
        return updatePublicApplicationDetails(no_siri_permohonan,request_data)

@dbkl_ns.route("/deletePublicApplicationList", endpoint="delete_public_applicationList")
class DeletePublicApplicationList(Resource):
    """Handles HTTP requests to URL: /dbkl/deletePublicApplicationList."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteApplicationList_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "delete PublicApplicationList")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def delete(self):
        request_data = deleteApplicationList_reqparser.parse_args()
        return deletePublicApplicationList(request_data)
    
@dbkl_ns.route("/fetchPublicApplicationDetails/<no_siri_permohonan>", endpoint="fetch_public_application_details")
class FetchPublicApplicationDetails(Resource):
    """Handles HTTP requests to URL: /dbkl/updatePublicApplicationDetails/<no_siri_permohonan>."""
    
    # @dbkl_ns.expect(updateApplication_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Public Application Details Form Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self,no_siri_permohonan):
        
        return fetchPublicApplicationDetails(no_siri_permohonan)

@dbkl_ns.route("/updateStatusSemakanDokumen/<no_siri_permohonan>", endpoint="update_status_semakanDokumen")
class UpdateStatusSemakanDokumen(Resource):
    """Handles HTTP requests to URL: /dbkl/updateStatusSemakanDokumen/<no_siri_permohonan>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateStatusSemakanDokumen_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Status Semakan Dokumen Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,no_siri_permohonan):
        request_data = updateStatusSemakanDokumen_reqparser.parse_args()
        return updateStatusSemakanDokumen(no_siri_permohonan,request_data)

@dbkl_ns.route("/updateSiteVisitApplicationList/<site_id>", endpoint="update_sitevisit_application_list")
class UpdateSiteVisitApplicationList(Resource):
    """Handles HTTP requests to URL: /dbkl/updateSiteVisitApplicationList/<site_id>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateSiteVisit_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Public Site Visit Info Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,site_id):

        request_data = updateSiteVisit_reqparser.parse_args()
        return updateSiteVisitApplicationList(site_id,request_data)

@dbkl_ns.route("/deletelistOfsitevisitInformation", endpoint="delete_list_of_sitevisitInformation")
class DeletelistOfsitevisitInformation(Resource):
    """Handles HTTP requests to URL: /dbkl/deletelistOfsitevisitInformation."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteSitevisitInformation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Public application list fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def delete(self):
        request_data = deleteSitevisitInformation_reqparser.parse_args()
        return deletelistOfsitevisitInformation(request_data)
    
@dbkl_ns.route("/getAgencyJobPaymentClaim", endpoint="fetch_agency_jobPaymentClaim")
class GetAgencyJobPaymentClaim(Resource):
    """Handles HTTP requests to URL: /dbkl/getAgencyJobPaymentClaim."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Agency job payment claim fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getAgencyJobPaymentClaim()

@dbkl_ns.route("/getAgencyJobPaymentClaimByInbois/<no_inbois>", endpoint="get_agency_jobPaymentClaim_by_inbois")
class GetAgencyJobPaymentClaimByInbois(Resource):
    """Handles HTTP requests to URL: /dbkl/getAgencyJobPaymentClaimByInbois/<no_inbois>."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Agency job payment claim by inbois fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self,no_inbois):
        return getAgencyJobPaymentClaimByInbois(no_inbois)

@dbkl_ns.route("/updateAgencyJobPaymentClaimByInbois/<no_inbois>", endpoint="update_agency_jobPaymentClaim_by_inbois")
class UpdateAgencyJobPaymentClaimByInbois(Resource):
    """Handles HTTP requests to URL: /dbkl/updateAgencyJobPaymentClaimByInbois/<no_inbois>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateAgencyJobPaymentClaimByInbois_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "agency job payment claim by inbois updated")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,no_inbois):
        request_data = updateAgencyJobPaymentClaimByInbois_reqparser.parse_args()
        
        return updateAgencyJobPaymentClaimByInbois(no_inbois,request_data)

@dbkl_ns.route("/deleteAgencyJobPaymentClaim", endpoint="delete_agency_JobPaymentClaim")
class DeleteAgencyJobPaymentClaim(Resource):
    """Handles HTTP requests to URL: /dbkl/deleteAgencyJobPaymentClaim."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteAgencyJobPaymentClaim_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Agency job payment claim list deleted successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def delete(self):
        request_data = deleteAgencyJobPaymentClaim_reqparser.parse_args()
        return deleteAgencyJobPaymentClaim(request_data)

@dbkl_ns.route("/getOmpBaru", endpoint="get_jkasOmp")
class GetJkasOmp(Resource):
    """Handles HTTP requests to URL: /dbkl/getOmpBaru."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "jkas baru content fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getOmpBaru()

@dbkl_ns.route("/getOmpLama/<parilament_name>", endpoint="get_ompLama")
class GetOmpLama(Resource):
    """Handles HTTP requests to URL: /dbkl/getOmpBaru."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Omp Lama details fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self, parilament_name):
        return getOmpLama(parilament_name)

    
@dbkl_ns.route("/getMTBOfficersList", endpoint="get_mtb_officers_list")
class GetMTBOfficersList(Resource):
    """Handles HTTP requests to URL: /dbkl/getMTBOfficersList."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "MTB Officers List fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def get(self):
        """Fetch MTB Officers Information List."""
        return getMTBOfficersList()
    
@dbkl_ns.route("/getMTBOfficerInfo", endpoint="get_mtb_officers_info")
class GetMTBOfficerInfo(Resource):
    """Handles HTTP requests to URL: /dbkl/getMTBOfficerInfo."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "MTB Officers Info fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def get(self):
        """Fetch MTB Officers Information."""
        return getMTBOfficerInfo()
       
@dbkl_ns.route("/getDailyMTBInquiryInforByMTK", endpoint="get_daily_mtb_inquiry_infor_by_mtk")
class GetDailyMTBInquiryInforByMTK(Resource):
    """Handles HTTP requests to URL: /dbkl/getDailyMTBInquiryInforByMTK."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(mtbInquiry_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "MTB Inquiry Information List fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """Fetch Daily Work log against MTB id."""
        request_data = mtbInquiry_reqparser.parse_args()
        return getDailyMTBInquiryInforByMTK(request_data)
    
@dbkl_ns.route("/getDailyMTBInquiryInforByMTB/<tarikh>", endpoint="get_daily_mtb_inquiry_infor_by_mtb")
class GetDailyMTBInquiryInforByMTKB(Resource):
    """Handles HTTP requests to URL: /dbkl/getDailyMTBInquiryInforByMTB."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "MTB Inquiry Information List fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self,tarikh):
        """Fetch Daily Work log against tarikh"""
        return getDailyMTBInquiryInforByMTB(tarikh)

    
@dbkl_ns.route("/addComplaintInvestigation", endpoint="add_complaint_investigation")
class AddComplaintInvestigationn(Resource):
    """Handles HTTP requests to URL: /dbkl/addInquiryInformation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(addComplaintInvestigation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Inquiry Infdormation Added")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ Add Inquiry Information."""
        request_data = addComplaintInvestigation_reqparser.parse_args()
        return addComplaintInvestigation(request_data)
    
@dbkl_ns.route("/getComplaintInvestigation", endpoint="get_complaint_investigation")
class GetComplaintInvestigation(Resource):
    """Handles HTTP requests to URL: /dbkl/getComplaintInvestigation."""
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getComplaintInvestigation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Complaint Investigation fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ View Complaint Investigation"""
        request_data = getComplaintInvestigation_reqparser.parse_args()
        return getComplaintInvestigation(request_data)
    
@dbkl_ns.route("/updateComplaintInvestigation/<form_id>", endpoint="update_complaint_investigation")
class UpdateComplaintInvestigation(Resource):
    """Handles HTTP requests to URL: /dbkl/getMTBComplaintInvestigation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(addComplaintInvestigation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Complaint Investigation updated")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self, form_id):
        """ View MTB Complaint Investigation"""
        request_data = addComplaintInvestigation_reqparser.parse_args()
        return updateComplaintInvestigation(form_id,request_data)
    
@dbkl_ns.route("/getMTBCompoundInformation", endpoint="get_mtb_compound_information")
class GetMTBCompoundInformation(Resource):
    """Handles HTTP requests to URL: /dbkl/getCompoundInformation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(mtbCompoundInformation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "MTB Compound Information fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ View MTB Compound Information"""
        request_data = mtbCompoundInformation_reqparser.parse_args()
        return getMTBCompoundInformation(request_data)

@dbkl_ns.route("/getMTBCompoundInfoByMTB", endpoint="get_mtb_compound_info_by_mtb")
class GetMTBCompoundInfoByMTB(Resource):
    """Handles HTTP requests to URL: /dbkl/getMTBCompoundInfoByMTB."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(mtbCompoundInfoByMTB_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "MTB Compound Information fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ View MTB Compound Information"""
        request_data = mtbCompoundInfoByMTB_reqparser.parse_args()
        return getMTBCompoundInfoByMTB(request_data)

@dbkl_ns.route("/addMTBCompoundForm", endpoint="add_mtb_compound_form")
class AddMTBCompoundForm(Resource):
    """Handles HTTP requests to URL: /dbkl/addMTBCompoundForm."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(addMTBCompoundForm_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Compound Form Added Successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ Create MTB Compound Form """
        request_data = addMTBCompoundForm_reqparser.parse_args()
        return addMTBCompoundForm(request_data)


@dbkl_ns.route("/getCompoundForm/<no_notis_bas>", endpoint="get_compound_form")
class GetCompoundForm(Resource):
    """Handles HTTP requests to URL: /dbkl/getCompoundForm."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "MTB Compound Form fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self, no_notis_bas):
        """ View MTB Compound Form"""
        return getCompoundForm(no_notis_bas)

    
@dbkl_ns.route("/sendNotice", endpoint="send_notice")
class SendNotice(Resource):
    """Handles HTTP requests to URL: /dbkl/sendNotice."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(sendNotice_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Inquiry Information fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ Send Notice """
        request_data = sendNotice_reqparser.parse_args()
        return sendNotice(request_data)
    
@dbkl_ns.route("/grafPrestasiBulanan", endpoint="graf_prestasi_bulanan")
class GrafPrestasiBulanan(Resource):
    """Handles HTTP requests to URL: /dbkl/grafPrestasiBulanan."""
 
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(grafPrestasiBulanan_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "graf prestasi bulanan fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """Fetch graf prestasi bulanan."""
        request_data = grafPrestasiBulanan_reqparser.parse_args()
        return grafPrestasiBulanan(request_data)
@dbkl_ns.route("/grafAnalisisDanStatistik", endpoint="graf_analisis_dan_statistik")
class GrafAnalisisDanStatistik(Resource):
    """Handles HTTP requests to URL: /dbkl/grafPrestasiBulanan."""
 
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(grafAnalisisDanStatistik_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "graf analisis dan statistik fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """Fetch graf analisis dan statistik."""
        request_data = grafAnalisisDanStatistik_reqparser.parse_args()
        return grafAnalisisDanStatistik(request_data)

@dbkl_ns.route("/grafJumlahKutipan", endpoint="graf_jumlah_kutipan")
class GrafJumlahKutipan(Resource):
    """Handles HTTP requests to URL: /dbkl/grafJumlahKutipan."""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "JumlahKutipan graph fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ return JumlahKutipan graph """
        return grafJumlahKutipan()
@dbkl_ns.route("/grafJumlahPembersihanAwam", endpoint="graf_jumlah_pembersihan_awam")
class GrafJumlahPembersihanAwam(Resource):
    """Handles HTTP requests to URL: /dbkl/grafJumlahPembersihanAwam."""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "JumlahPembersihanAwam graph fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ return list of number_of_citations_graph """
        return grafJumlahPembersihanAwam()
    
@dbkl_ns.route("/getIdPegawai", endpoint="get_Id_Pegawai")
class GetIdPegawai(Resource):
    """Handles HTTP requests to URL: /dbkl/getIdPegawai."""
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Id_Pegawai and parlimen fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ returns id_Pegawai and parlimen"""
        return getIdPegawai()
    
@dbkl_ns.route("/getLokasi/<parlimen>", endpoint="get_lokasi")
class GetLokasi(Resource):
    """Handles HTTP requests to URL: /dbkl/getLokasi."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "lokasi fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self, parlimen):
        """ return list of lokasi """
        return getLokasi(parlimen)