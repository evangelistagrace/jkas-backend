"""API endpoint definitions for /auth namespace."""
from http import HTTPStatus
import logging
from flask_restx import Namespace, Resource
from app.main.util.dto import (
    masterUser_model, dbkl_register_reqparser, dbkl_otp_reqparser, dbkl_login_reqparser, changePassword_reqparser, dbkl_forgot_reqparser, newPassword_reqparser, assignRole_reqparser,
    updateMeeting_reqparser, addDetailedMeeting_reqparser, listDetailedMeeting_reqparser, updateEMeeting_reqparser, updateDetailedMeeting_reqparser, deleteMeeting_reqparser, getOmpBaru_reqparser, updateOmpBaru_reqparser,
    updateInventoriPengguna_reqparser, deleteInventoriPengguna_reqparser, updateApplicationList_reqparser, updateApplication_reqparser, deleteApplicationList_reqparser, 
    updateSiteVisit_reqparser, deleteSitevisitInformation_reqparser, deleteSitevisitPDF_reqparser, updateStatusSemakanDokumen_reqparser, updateJobPaymentClaimByInbois_reqparser, deleteJobPaymentClaim_reqparser, getSapuanCucianCoordinates_reqparser,
    addComplaintInvestigation_reqparser, updateComplaintInvestigation_reqparser, add2ndComplaintInvestigation_reqparser, updateComplaintComments_reqparser, add3rdComplaintInvestigation_reqparser, getComplaintInvestigation_reqparser, mtbInquiry_reqparser,getMTBOfficersTarikh_reqparser, mtbCompoundInformation_reqparser, mtbCompoundInfoByMTB_reqparser, addMTBCompoundForm_reqparser,
    getFilteredLokasi_reqparser, sendNotice_reqparser, grafPrestasiBulanan_reqparser, grafAnalisisDanStatistik_reqparser, createOmpBaru_reqparser, lapisanFitur_reqparser, getKategori_reqparser, grafPerkhidmatanPusatTong_reqparser, 
    getMonthlyPerformance_reqparser, getNamaMTK_reqparser, fetchMapCoordinates_reqparser, getNamaTaman_reqparser, getNamaKawasan_reqparser, getMapLapisanFitur_reqparser, getPetaKawasan_reqparser, getJadualKutipan_reqparser, get2ndPetaKawasan_reqparser, getjadualPembersihan_reqparser, randomSearch_reqparser,
    addTextInPublicApplicationList_reqparser, getMTB_reqparser, getMTBOfficer_reqparser, getDailyMTBInquiryInforByMTB_reqparser,
    )

from app.main.service.dbkl_service import (
    registerDbklUser, completeRegistration, get_logged_in_user, login, getProfileInformation, changePassword, logout, assignRole, forgotPassword, resetPassword, getCommitteeList, getDepartmentList,
    getJumlahKawasanPerkhidmatan, getJumlahPermis, getJumlahPembersihanAwam, getJumlahKutipanSampah,
    addDetailedMeeting, getMeeting, listOfDetailedMeeting, getAllDetailedMeeting, getDetailedMeeting, listOfMeeting, updateComplaintComments, updateMeeting, deleteListOfMeeting, 
    deleteInventoriPengguna, fetchPublicApplicationDetails, getJobPaymentClaim, getJobPaymentClaimByInbois, updateJobPaymentClaimByInbois, deleteJobPaymentClaim, 
    addComplaintInvestigation, add2ndComplaintInvestigation, add3rdComplaintInvestigation, getComplaintInvestigation, updateComplaintInvestigation, getLogPengguna, 
    getMTBCompoundInformation, getMTBCompoundInfoByMTB, addMTBCompoundForm, getMTBCompoundList, getCompoundForm, getOmpSubArea, getOmpBaru, getSingleOmpBaru, updateOmpBaru, deleteOmpBaru, getFilteredLokasi, getOmpLama, getOmpLamaSubArea,
    getPublicApplicationList, getPublicApplicationList2, deletePublicApplicationList, undeletePublicApplicationList, addTextInPublicApplicationList, getSapuanCucianCoordinates,
    getMTKList, getMTBOfficersList, listPegawai, getMTBOfficersTarikh, listComplaintDate, getMTBCompoundsTarikh, getMTBOfficerInfo, getDailyMTBInquiryInforByMTK, getDailyMTBInquiryInforByMTB, sendNotice,
    updateDetailedMeeting, updateEMeeting, getInventoriPenggunaById, getInventoriPengguna, deleteInventoriPengguna, updateInventoriPengguna, updateApplicationList, updateApplicationList2,
    updatePublicApplicationDetails, updateSiteVisitApplicationList, updateSiteVisitApplicationList2, deletelistOfsitevisitInformation, undeletelistOfsitevisitInformation, deleteSitevisitPDF, updateStatusSemakanDokumen, 
    grafJumlahKutipan, grafJumlahPembersihanAwam, createOmpBaru, getIdPegawai, getLokasi, getLapisanFitur, getKategori, grafPerkhidmatanPusatTong, grafAnalisisDanStatistik, grafPrestasiBulanan,getBorangZon, getBorangParlimen,
    getGoogleAnalyticsReport, dailyViewReport, getMonthlyPerformance, getNamaMTK, fetchMapCoordinates, adminUserAdd, compoundAnalysis, getCompoundCount,
    getParlimen, getNamaTaman, getNamaJalan, getNamaKawasan, getMapLapisanFitur, getPetaKawasan, getJadualKutipan, get2ndPetaKawasan, getJadualPembersihan, randomSearch, getMTB, getMTBOfficer, get_mtk_list
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
        """ OTP verification and Register DBKL user """
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

@dbkl_ns.route("/getProfileInformation", endpoint="dbkl_get_profile_information")
class GetProfileInformation(Resource):
    """Handles HTTP requests to URL: /dbkl/getProfileInformation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Profile Information fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def get(self):
        """Get Profile Information of DBKL User"""
        return getProfileInformation()
 
@dbkl_ns.route("/changePassword", endpoint="dbkl_change_password")
class ChangePassword(Resource):
    """Handles HTTP requests to URL: /dbkl/changePassword."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(changePassword_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Password Changed Successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Change Password of a Logged User."""
        request_data = changePassword_reqparser.parse_args()
        return changePassword(request_data)
        
@dbkl_ns.route("/logout", endpoint="dbkl_logout")
class DbklLogout(Resource):
    """Handles HTTP requests to URL: /dbkl/logout."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Log out succeeded, token is no longer valid.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Add token to blacklist, deauthenticating the current user."""
        return logout()

@dbkl_ns.route("/forgotPassword", endpoint="dbkl_forgot_password")
class ForgotPassword(Resource):
    """  Handles HTTP request to URL: /public/forgotPassword """
    @dbkl_ns.expect(dbkl_forgot_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Reset password link sent successfully")
    @dbkl_ns.response(int(HTTPStatus.NOT_FOUND), "id_card_no or email not registered ! Please try again.")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """ Enter email or nama_pengguna of the user who's password is forgotten """
        request_data = dbkl_forgot_reqparser.parse_args()
        return forgotPassword(request_data)

@dbkl_ns.route("/resetPassword", endpoint="dbkl_reset_password")
class ResetPassword(Resource):
    """ Handles HTTP request to URL: /public/resetPassword """
    @dbkl_ns.expect(newPassword_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "kata_laluan updated successfully!")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Bad request! Please try again.")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def put(self):
        """ Reset password for an User who has forgotten his password """
        request_data = newPassword_reqparser.parse_args()
        return resetPassword(request_data)

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


@dbkl_ns.route("/getJumlahKawasanPerkhidmatan", endpoint="get_jumlah_kawasan_perkhidmatan")
class GetJumlahKawasanPerkhidmatan(Resource):
    """Handles HTTP requests to URL: /dbkl/getJumlahKawasanPerkhidmatan."""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "JumlahKawasanPerkhidmatan fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ Return JumlahKawasanPerkhidmatan """
        return getJumlahKawasanPerkhidmatan()
    
@dbkl_ns.route("/getJumlahPermis", endpoint="get_jumlah_permis")
class GetJumlahPermis(Resource):
    """Handles HTTP requests to URL: /dbkl/getJumlahPermis."""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "JumlahPermis fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ Return JumlahPermis """
        return getJumlahPermis()
    
@dbkl_ns.route("/getJumlahPembersihanAwam", endpoint="get_jumlah_pembersihan_awam")
class GetJumlahPembersihanAwam(Resource):
    """Handles HTTP requests to URL: /dbkl/getJumlahPembersihanAwam."""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "JumlahPembersihanAwam fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ Return JumlahPembersihanAwam """
        return getJumlahPembersihanAwam()
    
@dbkl_ns.route("/getJumlahKutipanSampah", endpoint="get_jumlah_kutipan_sampah")
class GetJumlahKutipanSampah(Resource):
    """Handles HTTP requests to URL: /dbkl/getJumlahKutipanSampah."""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "JumlahKutipanSampah fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ Return JumlahKutipanSampah """
        return getJumlahKutipanSampah()
    
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

@dbkl_ns.route("/getMeeting/<int:meeting_id>", endpoint="get_meeting")
class GetMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/getMeeting/<meeting_id>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "get meeting by meetingId.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self,meeting_id):
        return getMeeting(meeting_id)

@dbkl_ns.route("/getCommitteeList", endpoint="get_committee_list")
class GetCommitteeList(Resource):
    """Handles HTTP requests to URL: /dbkl/getCommitteeList"""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "get committee list")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getCommitteeList()

@dbkl_ns.route("/getDepartmentList", endpoint="get_department_list")
class GetDepartmentList(Resource):
    """Handles HTTP requests to URL: /dbkl/getDepartmentList"""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "get committee list")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getDepartmentList()
    
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
    @dbkl_ns.expect(listDetailedMeeting_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "list of detailed meeting.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        request_data = listDetailedMeeting_reqparser.parse_args()
        return listOfDetailedMeeting(request_data)

@dbkl_ns.route("/getAllDetailedMeeting", endpoint="get_all_detailed_meeting")
class GetAllDetailedMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/getAllDetailedMeeting."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "list of detailed meeting.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getAllDetailedMeeting()

@dbkl_ns.route("/getDetailedMeeting/<int:detailed_meeting_id>", endpoint="get_detailed_meeting")
class GetDetailedMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/getDetailedMeeting/<detailed_meeting_id>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Get Detailed meeting.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self,detailed_meeting_id):
        return getDetailedMeeting(detailed_meeting_id)

@dbkl_ns.route("/updateDetailedMeeting/<int:detailed_meeting_id>", endpoint="update_detailed_meeting")
class UpdateDetailedMeeting(Resource):
    """Handles HTTP requests to URL: /dbkl/updateDetailedMeeting."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateDetailedMeeting_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Detailed Meeting Form Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,detailed_meeting_id):
        
        request_data = updateDetailedMeeting_reqparser.parse_args()
        return updateDetailedMeeting(detailed_meeting_id, request_data)

@dbkl_ns.route("/updateEMeeting/<int:detailed_meeting_id>", endpoint="updateEMeeting")
class UpdateEMeeting(Resource):
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateEMeeting_reqparser)
    def put(self,detailed_meeting_id):
        request_data = updateEMeeting_reqparser.parse_args()
        return updateEMeeting(detailed_meeting_id, request_data)

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

@dbkl_ns.route("/getInventoriPenggunaById/<id_pengguna>", endpoint="get_inventori_pengguna_by_id")
class GetInventoriPenggunaById(Resource):
    """Handles HTTP requests to URL: /dbkl/getInventoriPenggunaById/<id_pengguna>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Detailed Meeting Form Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self,id_pengguna):
        return getInventoriPenggunaById(id_pengguna)
        
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
    @dbkl_ns.response(int(HTTPStatus.OK), "Application list fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getPublicApplicationList()

@dbkl_ns.route("/getPublicApplicationList2", endpoint="get_public_application_list_2")
class GetPublicApplicationList2(Resource):
    """Handles HTTP requests to URL: /dbkl/getPublicApplicationList2."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Application list fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getPublicApplicationList2()


@dbkl_ns.route("/updateApplicationList/<no_siri_permohonan>", endpoint="update_dbkl_application_list")
class UpdateApplicationList(Resource):
    """Handles HTTP requests to URL: /dbkl/updateApplicationList/<no_siri_permohonan>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateApplicationList_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Application List Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,no_siri_permohonan):
        request_data = updateApplicationList_reqparser.parse_args()
        return updateApplicationList(no_siri_permohonan,request_data)
    
@dbkl_ns.route("/updateApplicationList2/<no_siri_permohonan>", endpoint="update_dbkl_application_list2")
class UpdateApplicationList(Resource):
    """Handles HTTP requests to URL: /dbkl/updateApplicationList2/<no_siri_permohonan>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateApplicationList_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Application List Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,no_siri_permohonan):
        request_data = updateApplicationList_reqparser.parse_args()
        return updateApplicationList2(no_siri_permohonan,request_data)
    
@dbkl_ns.route("/updatePublicApplicationDetails/<no_siri_permohonan>", endpoint="update_public_application_details")
class UpdatePublicApplicationDetails(Resource):
    """Handles HTTP requests to URL: /dbkl/updatePublicApplicationDetails/<no_siri_permohonan>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateApplication_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Application Details Form Updated.")
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
    
@dbkl_ns.route("/undeletePublicApplicationList", endpoint="undelete_public_applicationList")
class UndeletePublicApplicationList(Resource):
    """Handles HTTP requests to URL: /dbkl/undeletePublicApplicationList."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteApplicationList_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "undelete PublicApplicationList")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self):
        request_data = deleteApplicationList_reqparser.parse_args()
        return undeletePublicApplicationList(request_data)

@dbkl_ns.route("/addTextInPublicApplicationList", endpoint="addTextInPublicApplicationList")
class AddTextInPublicApplicationList(Resource):
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(addTextInPublicApplicationList_reqparser)
    def put(self):
        request_data = addTextInPublicApplicationList_reqparser.parse_args()
        return addTextInPublicApplicationList(request_data)

@dbkl_ns.route("/fetchPublicApplicationDetails/<no_siri_permohonan>", endpoint="fetch_public_application_details")
class FetchPublicApplicationDetails(Resource):
    """Handles HTTP requests to URL: /dbkl/updatePublicApplicationDetails/<no_siri_permohonan>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Application Details Form Updated.")
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

@dbkl_ns.route("/updateSiteVisitApplicationList/<int:site_id>", endpoint="update_sitevisit_application_list")
class UpdateSiteVisitApplicationList(Resource):
    """Handles HTTP requests to URL: /dbkl/updateSiteVisitApplicationList/<site_id>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateSiteVisit_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Site Visit Info Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,site_id):

        request_data = updateSiteVisit_reqparser.parse_args()
        return updateSiteVisitApplicationList(site_id,request_data)
    
@dbkl_ns.route("/updateSiteVisitApplicationList2/<int:site_id>", endpoint="update_sitevisit_application_list2")
class UpdateSiteVisitApplicationList(Resource):
    """Handles HTTP requests to URL: /dbkl/updateSiteVisitApplicationList/<site_id>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateSiteVisit_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Site Visit Info Updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,site_id):

        request_data = updateSiteVisit_reqparser.parse_args()
        return updateSiteVisitApplicationList2(site_id,request_data)

@dbkl_ns.route("/deletelistOfsitevisitInformation", endpoint="delete_list_of_sitevisitInformation")
class DeletelistOfsitevisitInformation(Resource):
    """Handles HTTP requests to URL: /dbkl/deletelistOfsitevisitInformation."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteSitevisitInformation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Site visit info list deleted successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def delete(self):
        request_data = deleteSitevisitInformation_reqparser.parse_args()
        return deletelistOfsitevisitInformation(request_data)
    
@dbkl_ns.route("/undeletelistOfsitevisitInformation", endpoint="undelete_list_of_sitevisitInformation")
class UndeletelistOfsitevisitInformation(Resource):
    """Handles HTTP requests to URL: /dbkl/undeletelistOfsitevisitInformation."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteSitevisitInformation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Site visit info list undeleted successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self):
        request_data = deleteSitevisitInformation_reqparser.parse_args()
        return undeletelistOfsitevisitInformation(request_data)
    
@dbkl_ns.route("/deleteSitevisitPDF", endpoint="delete_site_visit_pdf")
class DeleteSitevisitPDF(Resource):
    """Handles HTTP requests to URL: /dbkl/deleteSitevisitPDF."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteSitevisitPDF_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Site visit info list deleted successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def delete(self):
        request_data = deleteSitevisitPDF_reqparser.parse_args()
        return deleteSitevisitPDF(request_data)
    
@dbkl_ns.route("/getAgencyJobPaymentClaim", endpoint="get_job_payment_claim")
class GetJobPaymentClaim(Resource):
    """Handles HTTP requests to URL: /dbkl/getAgencyJobPaymentClaim."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Job payment claim fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        return getJobPaymentClaim()

@dbkl_ns.route("/getAgencyJobPaymentClaimByInbois/<no_inbois>", endpoint="get_job_payment_claim_by_inbois")
class GetJobPaymentClaimByInbois(Resource):
    """Handles HTTP requests to URL: /dbkl/getAgencyJobPaymentClaimByInbois/<no_inbois>."""
    
    # @dbkl_ns.expect(search_detailed_meeting_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Job payment claim by inbois fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self,no_inbois):
        return getJobPaymentClaimByInbois(no_inbois)

@dbkl_ns.route("/updateAgencyJobPaymentClaimByInbois/<no_inbois>", endpoint="update_job_payment_claim_by_inbois")
class UpdateJobPaymentClaimByInbois(Resource):
    """Handles HTTP requests to URL: /dbkl/updateAgencyJobPaymentClaimByInbois/<no_inbois>."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateJobPaymentClaimByInbois_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Job payment claim by inbois updated")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def put(self,no_inbois):
        request_data = updateJobPaymentClaimByInbois_reqparser.parse_args()
        
        return updateJobPaymentClaimByInbois(no_inbois,request_data)

@dbkl_ns.route("/deleteAgencyJobPaymentClaim", endpoint="delete_job_payment_claim")
class DeleteJobPaymentClaim(Resource):
    """Handles HTTP requests to URL: /dbkl/deleteAgencyJobPaymentClaim."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(deleteJobPaymentClaim_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Job payment claim list deleted successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def delete(self):
        request_data = deleteJobPaymentClaim_reqparser.parse_args()
        return deleteJobPaymentClaim(request_data)

@dbkl_ns.route("/getOmpSubArea/<parliament_name>", endpoint="getOmpSubArea")
class GetOmpSubArea(Resource):
    def get(self, parliament_name):
        return getOmpSubArea(parliament_name)

@dbkl_ns.route("/getOmpBaru", endpoint="get_jkasOmp")
class GetJkasOmp(Resource):
    
    @dbkl_ns.expect(getOmpBaru_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "OMP baru list fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        request_data = getOmpBaru_reqparser.parse_args()
        return getOmpBaru(request_data)

@dbkl_ns.route("/getSingleOmpBaru/<omp_id>", endpoint="getSingleOmpBaru")
class GetSingleOmpBaru(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self,omp_id):
        return getSingleOmpBaru(omp_id)


@dbkl_ns.route("/updateOmpBaru/<omp_id>", endpoint="updateOmpBaru")
class UpdateOmpBaru(Resource):
    
    @dbkl_ns.expect(createOmpBaru_reqparser)
    @dbkl_ns.doc(security="Bearer")
    def put(self,omp_id):
        request_data = createOmpBaru_reqparser.parse_args()
        return updateOmpBaru(request_data,omp_id)

@dbkl_ns.route("/deleteOmpBaru/<omp_id>", endpoint="deleteOmpBaru")
class DeleteOmpBaru(Resource):
    @dbkl_ns.doc(security="Bearer")
    def delete(self,omp_id):
        return deleteOmpBaru(omp_id)

@dbkl_ns.route("/getFilteredLokasi", endpoint="get_filtered_lokasi")
class GetFilteredLokasi(Resource):
    """Handles HTTP requests to URL: /dbkl/getFilteredLokasi."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getFilteredLokasi_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "OMP baru list fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        request_data = getFilteredLokasi_reqparser.parse_args()
        return getFilteredLokasi(request_data)

@dbkl_ns.route("/getOmpLamaSubArea/<parliament_name>", endpoint="getOmpLamaSubArea")
class GetOmpLamaSubArea(Resource):
    def get(self, parliament_name):
        return getOmpLamaSubArea(parliament_name)


@dbkl_ns.route("/getOmpLama", endpoint="get_ompLama")
class GetOmpLama(Resource):
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getOmpBaru_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Omp Lama details fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        request_data = getOmpBaru_reqparser.parse_args()
        return getOmpBaru(request_data)

@dbkl_ns.route("/getMTKList", endpoint="getMTKList")
class GetMTKList(Resource):
    def get(self):
        return getMTKList()

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

@dbkl_ns.route("/listPegawai", endpoint="listPegawai")
class ListPegawai(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self):
        return listPegawai()

@dbkl_ns.route("/listMtk", endpoint="listMtk")
class ListPegawai(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self):
        return get_mtk_list()

@dbkl_ns.route("/getMTBOfficersTarikh", endpoint="getMTBOfficersTarikh")
class GetMTBOfficersTarikh(Resource):
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getMTBOfficersTarikh_reqparser)
    def post(self):
        request_data = getMTBOfficersTarikh_reqparser.parse_args()
        officer_name = request_data.get("officer_name")
        return getMTBOfficersTarikh(officer_name)

@dbkl_ns.route("/getMTBCompoundsTarikh", endpoint="getMTBCompoundsTarikh")
class GetMTBCompoundsTarikh(Resource):
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getMTBOfficersTarikh_reqparser)
    def post(self):
        request_data = getMTBOfficersTarikh_reqparser.parse_args()
        officer_name = request_data.get("officer_name")
        return getMTBCompoundsTarikh(officer_name)


@dbkl_ns.route("/listComplaintDate", endpoint="listComplaintDate")
class ListComplaintDate(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self):
        return listComplaintDate()

@dbkl_ns.route("/getSapuanCucianCoordinates", endpoint="get_sapuan_cucian_coordinates")
class GetSapuanCucianCoordinates(Resource):
    """Handles HTTP requests to URL: /dbkl/getSapuanCucianCoordinates."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getSapuanCucianCoordinates_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Sapuan Cucian Coordinates fetched")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """Fetch Sapuan Cucian Coordinates List."""
        request_data = getSapuanCucianCoordinates_reqparser.parse_args()
        return getSapuanCucianCoordinates(request_data)
    
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
    
@dbkl_ns.route("/getDailyMTBInquiryInforByMTB", endpoint="get_daily_mtb_inquiry_infor_by_mtb")
class GetDailyMTBInquiryInforByMTKB(Resource):
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getDailyMTBInquiryInforByMTB_reqparser)
    def post(self):
        request_data = getDailyMTBInquiryInforByMTB_reqparser.parse_args()
        return getDailyMTBInquiryInforByMTB(request_data)

    
@dbkl_ns.route("/addComplaintInvestigation", endpoint="add_complaint_investigation")
class AddComplaintInvestigationn(Resource):
    """Handles HTTP requests to URL: /dbkl/addComplaintInvestigation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(addComplaintInvestigation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Complaint Investigation Added")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ Add Complaint Investigation."""
        request_data = addComplaintInvestigation_reqparser.parse_args()
        return addComplaintInvestigation(request_data)
    
@dbkl_ns.route("/add2ndComplaintInvestigation", endpoint="add_2nd_complaint_investigation")
class Add2ndComplaintInvestigation(Resource):
    """Handles HTTP requests to URL: /dbkl/add2ndComplaintInvestigation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(add2ndComplaintInvestigation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Complaint Investigation Added")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ Add Complaint Investigation."""
        request_data = add2ndComplaintInvestigation_reqparser.parse_args()
        return add2ndComplaintInvestigation(request_data)

@dbkl_ns.route("/updateComplaintComments", endpoint="updateComplaintCommments")
class UpdateComplaintComments(Resource):
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateComplaintComments_reqparser)
    @dbkl_ns.response(int(HTTPStatus.NO_CONTENT), "Complaint comments updated.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation errors.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Unauthorized access.")
    def put(self):
        request_data=updateComplaintComments_reqparser.parse_args()
        return updateComplaintComments(request_data)

@dbkl_ns.route("/add3rdComplaintInvestigation", endpoint="add_3rd_complaint_investigation")
class Add3rdComplaintInvestigation(Resource):
    """Handles HTTP requests to URL: /dbkl/add3rdComplaintInvestigation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(add3rdComplaintInvestigation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.CREATED), "Complaint Investigation Added")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self):
        """ Add Complaint Investigation """
        request_data = add3rdComplaintInvestigation_reqparser.parse_args()
        return add3rdComplaintInvestigation(request_data)
    
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

@dbkl_ns.route("/updateComplaintInvestigation/<int:form_id>", endpoint="update_complaint_investigation")
class UpdateComplaintInvestigation(Resource):
    """Handles HTTP requests to URL: /dbkl/getMTBComplaintInvestigation."""

    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(updateComplaintInvestigation_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Complaint Investigation updated")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.UNAUTHORIZED), "Token is invalid or expired.")
    def post(self, form_id):
        """ View MTB Complaint Investigation"""
        request_data = updateComplaintInvestigation_reqparser.parse_args()
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

@dbkl_ns.route("/getMTBCompoundList", endpoint="getMTBCompoundList")
class GetMTBCompoundList(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self):
        return getMTBCompoundList()

@dbkl_ns.route("/getCompoundForm/<int:no_notis_bas>", endpoint="get_compound_form")
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

@dbkl_ns.route("/getBorangZon", endpoint="getBorangZon")
class GetBorangZon(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self):
        return getBorangZon()

@dbkl_ns.route("/getBorangParlimen", endpoint="getBorangParlimen")
class GetBorangParlimen(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self):
        return getBorangParlimen()

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

@dbkl_ns.route("/createOmpBaru", endpoint="create_omp_baru")
class CreateOmpBaru(Resource):
    """Handles HTTP requests to URL: /dbkl/createOmpBaru."""
    
    @dbkl_ns.expect(createOmpBaru_reqparser)
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "jkas baru created successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        request_data = createOmpBaru_reqparser.parse_args()
        return createOmpBaru(request_data)
    
@dbkl_ns.route("/getIdPegawai", endpoint="get_Id_Pegawai")
class GetIdPegawai(Resource):
    """Handles HTTP requests to URL: /dbkl/getIdPegawai."""
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Id_Pegawai and parlimen fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ returns id_Pegawai"""
        return getIdPegawai()
    
@dbkl_ns.route("/getLokasi/<parlimen>", endpoint="get_lokasi")
class GetLokasi(Resource):
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "lokasi fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self, parlimen):
        """ return list of lokasi """
        return getLokasi(parlimen)

@dbkl_ns.route("/getLapisanFitur", endpoint="get_lapisan_fitur")
class GetLapisanFitur(Resource):
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.response(int(HTTPStatus.OK), "Lapisan Fitur fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        """ return list of Lapisan Fitur """
        return getLapisanFitur()

@dbkl_ns.route("/grafPerkhidmatanPusatTong", endpoint="grafPerkhidmatanPusatTong")
class GrafPerkhidmatanPusatTong(Resource):
    """Handles HTTP requests to URL: /dbkl/grafPerkhidmatanPusatTong."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(grafPerkhidmatanPusatTong_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "YA, TIDAK Count for every parlimen fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        """ return list of Lapisan Fitur """
        request_data = grafPerkhidmatanPusatTong_reqparser.parse_args()
        return grafPerkhidmatanPusatTong(request_data)

@dbkl_ns.route("/getKategori", endpoint="get_kategori")
class GetKategori(Resource):
    """Handles HTTP requests to URL: /dbkl/getKategori."""
    
    @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getKategori_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Kategori fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        """ return list of Kategori """
        request_data = getKategori_reqparser.parse_args()
        return getKategori(request_data)
        
@dbkl_ns.route("/getGoogleAnalyticsReport", endpoint="get_google_analytics_report")
class GetGoogleAnalyticsReport(Resource):
    """Handles HTTP requests to URL: /dbkl/getGoogleAnalyticsReport."""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "Google Analytics Report fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ Return Google Analytics Report """
        import requests, json
        response = requests.get("https://jkashelper.azurewebsites.net/api/jkasgoogleanalytics", verify=False)
        if response.status_code != 200:
            logging.exception("Failed to get analytics: Code" + str(response.status_code) + ", Reason: " + str(response.content))
            return []
        return json.loads(response.content)
    
@dbkl_ns.route("/dailyViewReport", endpoint="daily_view_report")
class DailyViewReport(Resource):
    """Handles HTTP requests to URL: /dbkl/dailyViewReport."""
    
    @dbkl_ns.response(int(HTTPStatus.OK), "Daily View Report fetched successfully")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def get(self):
        """ Returns Daily View Report """
        return dailyViewReport()
  
@dbkl_ns.route("/getMonthlyPerformance", endpoint="get_monthly_performance")
class GetMonthlyPerformance(Resource):
    """Handles HTTP requests to URL: /dbkl/getMonthlyPerformance."""
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getMonthlyPerformance_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Monthly Performance fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        """ Fetch Monthly Performance """
        request_data = getMonthlyPerformance_reqparser.parse_args()
        return getMonthlyPerformance(request_data)
    
@dbkl_ns.route("/getNamaMTK", endpoint="get_nama_MTK")
class GetNamaMTK(Resource):
    """Handles HTTP requests to URL: /dbkl/getNamaMTK."""
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getNamaMTK_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "Nama MTK fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        """ Fetch Nama MTK """
        request_data = getNamaMTK_reqparser.parse_args()
        return getNamaMTK(request_data)
    
@dbkl_ns.route("/fetchMapCoordinates", endpoint="fetch_map_coordinates")
class FetchMapCoordinates(Resource):
    """Handles HTTP requests to URL: /dbkl/fetchMapCoordinates."""
    
    @dbkl_ns.expect(fetchMapCoordinates_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "map coordinates fetched successfully.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    def post(self):
        """ map coordinates fetched successfully """
        request_data = fetchMapCoordinates_reqparser.parse_args()
        return fetchMapCoordinates(request_data)
    
    
@dbkl_ns.route("/adminUserAdd", endpoint="adminUserAdd")
class AdminUserAdd(Resource):
    """Handles HTTP requests to URL: /dbkl/adminUserAdd."""

    @dbkl_ns.expect(dbkl_register_reqparser)
    @dbkl_ns.response(int(HTTPStatus.OK), "OTP sent Successfully")
    @dbkl_ns.response(int(HTTPStatus.CONFLICT), "alamat_emel address is already registered.")
    @dbkl_ns.response(int(HTTPStatus.BAD_REQUEST), "Validation error.")
    @dbkl_ns.response(int(HTTPStatus.NOT_ACCEPTABLE), "OTP can't be sent to this region")
    @dbkl_ns.response(int(HTTPStatus.INTERNAL_SERVER_ERROR), "Internal server error.")
    def post(self):
        """Initiate Registration from here"""
        request_data = dbkl_register_reqparser.parse_args()
        return adminUserAdd(request_data)

@dbkl_ns.route("/compoundAnalysis", endpoint="compoundAnalysis")
class CompoundAnalysis(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self):
        return compoundAnalysis()

@dbkl_ns.route("/getCompoundCount", endpoint="getCompoundCount")
class GetCompoundCount(Resource):
    @dbkl_ns.doc(security="Bearer")
    def get(self):
        return getCompoundCount()

@dbkl_ns.route("/getParlimen", endpoint="getParlimen")
class GetParlimen(Resource):
    # @dbkl_ns.doc(security="Bearer")
    def get(self):
        return getParlimen()

@dbkl_ns.route("/getNamaJalan/<parlimen>", endpoint="get_nama_jalan")
class GetNamaJalan(Resource):
    # @dbkl_ns.doc(security="Bearer")
    def post(self, parlimen):
        return getNamaJalan(parlimen)

@dbkl_ns.route("/getNamaTaman", endpoint="get_nama_taman")
class GetNamaTaman(Resource):
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getNamaTaman_reqparser)
    def post(self):
        request_data = getNamaTaman_reqparser.parse_args()
        return getNamaTaman(request_data)

@dbkl_ns.route("/getNamaKawasan", endpoint="get_nama_kawasan")
class GetNamaKawasan(Resource):
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getNamaKawasan_reqparser)
    def post(self):
        request_data = getNamaKawasan_reqparser.parse_args()
        return getNamaKawasan(request_data)

@dbkl_ns.route("/getMapLapisanFitur", endpoint="get_map_lapisan_fitur")
class GetMapLapisanFitur(Resource):
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getMapLapisanFitur_reqparser)
    def post(self):
        request_data = getMapLapisanFitur_reqparser.parse_args()
        return getMapLapisanFitur(request_data)

@dbkl_ns.route("/getPetaKawasan", endpoint="get_peta_kawasan")
class GetPetaKawasan(Resource):
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getPetaKawasan_reqparser)
    def post(self):
        request_data = getPetaKawasan_reqparser.parse_args()
        return getPetaKawasan(request_data)

@dbkl_ns.route("/getJadualKutipan", endpoint="get_jadual_kutipan")
class GetJadualKutipan(Resource):
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getJadualKutipan_reqparser)
    def post(self):
        request_data = getJadualKutipan_reqparser.parse_args()
        return getJadualKutipan(request_data)

@dbkl_ns.route("/get2ndPetaKawasan", endpoint="get_2nd_peta_kawasan")
class GetPetaKawasan(Resource):
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(get2ndPetaKawasan_reqparser)
    def post(self):
        request_data = get2ndPetaKawasan_reqparser.parse_args()
        return get2ndPetaKawasan(request_data)

@dbkl_ns.route("/getJadualPembersihan", endpoint="get_jadual_pembersihan")
class GetJadualPembersihan(Resource):
    # @dbkl_ns.doc(security="Bearer")
    @dbkl_ns.expect(getjadualPembersihan_reqparser)
    def post(self):
        request_data = getjadualPembersihan_reqparser.parse_args()
        return getJadualPembersihan(request_data)


@dbkl_ns.route("/randomSearch", endpoint="random_search")
class RandomSearch(Resource):
    @dbkl_ns.expect(randomSearch_reqparser)
    def post(self):
        request_data = randomSearch_reqparser.parse_args()
        return randomSearch(request_data)

@dbkl_ns.route("/getMTB", endpoint="getMTB")
class GetMTB(Resource):
    @dbkl_ns.expect(getMTB_reqparser)
    def post(self):
        request_data = getMTB_reqparser.parse_args()
        return getMTB(request_data)

@dbkl_ns.route("/getMTBOfficer", endpoint="getMTBOfficer")
class GetMTBOfficer(Resource):
    @dbkl_ns.expect(getMTBOfficer_reqparser)
    def post(self):
        request_data = getMTBOfficer_reqparser.parse_args()
        return getMTBOfficer(request_data)