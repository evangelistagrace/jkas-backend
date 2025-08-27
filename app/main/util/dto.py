"""Parsers and serializers for /auth API endpoints."""
from flask_restx import Model
from flask_restx.fields import String, Boolean, DateTime, Date
from datetime import datetime, time

# from werkzeug import FileStorage
from flask_restx import inputs
from flask_restx.inputs import email
from flask_restx.reqparse import RequestParser
import werkzeug

MasterUser = RequestParser(bundle_errors=True)
createAnnouncement_reqparser = RequestParser(bundle_errors=True)
updateAnnouncement_reqparser = RequestParser(bundle_errors=True)
deleteAnnouncement_reqparser = RequestParser(bundle_errors=True)
createManual_reqparser = RequestParser(bundle_errors=True)
updateManual_reqparser = RequestParser(bundle_errors=True)
deleteManual_reqparser = RequestParser(bundle_errors=True)
addGalleryPhoto_reqparser = RequestParser(bundle_errors=True)
deleteGalleryPhoto_reqparser = RequestParser(bundle_errors=True)
public_login_reqparser = RequestParser(bundle_errors=True)
changePassword_reqparser = RequestParser(bundle_errors=True)
forgot_reqparser = RequestParser(bundle_errors=True)
public_register_reqparser = RequestParser(bundle_errors=True)
public_otp_reqparser = RequestParser(bundle_errors=True)
updatePhone_reqparser = RequestParser(bundle_errors=True)
newPassword_reqparser = RequestParser(bundle_errors=True)
submitApplication_reqparser = RequestParser(bundle_errors=True)
updatePublicApplicationList_reqparser = RequestParser(bundle_errors=True)
deleteApplication_reqparser = RequestParser(bundle_errors=True)
updatesiteVisitInformation_reqparser = RequestParser(bundle_errors=True)
deleteSiteVisitInformation_reqparser = RequestParser(bundle_errors=True)
deleteSitevisitPDF_reqparser = RequestParser(bundle_errors=True)
submitRating_reqparser = RequestParser(bundle_errors=True)
addNonComplianceForm_reqparser = RequestParser(bundle_errors=True)
updateNonComplianceForm_reqparser = RequestParser(bundle_errors=True)
uploadFile_reqparser = RequestParser(bundle_errors=True)
getCoordinates_reqparser = RequestParser(bundle_errors=True)
mapKawasanPerkhidmatan_reqparser = RequestParser(bundle_errors=True)
updateUserInfo_reqparser = RequestParser(bundle_errors=True)

createFeedback_reqparser = RequestParser(bundle_errors=True)
deleteFeedbackList_reqparser = RequestParser(bundle_errors=True)
updateFeedback_reqparser = RequestParser(bundle_errors=True)
getInvoice_reqparser = RequestParser(bundle_errors=True)
createInvoice_reqparser = RequestParser(bundle_errors=True)
updateInvoice_reqparser = RequestParser(bundle_errors=True)

dbkl_register_reqparser  = RequestParser(bundle_errors=True)
dbkl_otp_reqparser  = RequestParser(bundle_errors=True)
dbkl_login_reqparser  = RequestParser(bundle_errors=True)
dbkl_forgot_reqparser  = RequestParser(bundle_errors=True)
addComplaintInvestigation_reqparser  = RequestParser(bundle_errors=True)
updateComplaintInvestigation_reqparser  = RequestParser(bundle_errors=True)
add2ndComplaintInvestigation_reqparser  = RequestParser(bundle_errors=True)
updateComplaintComments_reqparser = RequestParser(bundle_errors=True)
add3rdComplaintInvestigation_reqparser  = RequestParser(bundle_errors=True)
getComplaintInvestigation_reqparser  = RequestParser(bundle_errors=True)
assignRole_reqparser = RequestParser(bundle_errors=True)
addMeeting_reqparser = RequestParser(bundle_errors=True)
updateMeeting_reqparser = RequestParser(bundle_errors=True)
addDetailedMeeting_reqparser = RequestParser(bundle_errors=True)
listDetailedMeeting_reqparser = RequestParser(bundle_errors=True)
updateDetailedMeeting_reqparser = RequestParser(bundle_errors=True)
updateEMeeting_reqparser = RequestParser(bundle_errors=True)
deleteMeeting_reqparser = RequestParser(bundle_errors=True)
updateInventoriPengguna_reqparser = RequestParser(bundle_errors=True)
deleteInventoriPengguna_reqparser = RequestParser(bundle_errors=True)
update_status_details = RequestParser(bundle_errors=True)
updateSiteVisit_reqparser = RequestParser(bundle_errors=True)
deleteSitevisitInformation_reqparser = RequestParser(bundle_errors=True)
updateStatusSemakanDokumen_reqparser = RequestParser(bundle_errors=True)
updateApplication_reqparser = RequestParser(bundle_errors=True)
updateApplicationList_reqparser = RequestParser(bundle_errors=True)
deleteApplicationList_reqparser = RequestParser(bundle_errors=True)
updateJobPaymentClaimByInbois_reqparser = RequestParser(bundle_errors=True)
deleteJobPaymentClaim_reqparser = RequestParser(bundle_errors=True)
getSapuanCucianCoordinates_reqparser = RequestParser(bundle_errors=True)
mtbInquiry_reqparser = RequestParser(bundle_errors=True)
getMTBOfficersTarikh_reqparser = RequestParser(bundle_errors=True)
mtbCompoundInformation_reqparser = RequestParser(bundle_errors=True)
mtbCompoundInfoByMTB_reqparser = RequestParser(bundle_errors=True)
addMTBCompoundForm_reqparser = RequestParser(bundle_errors=True)
getFilteredLokasi_reqparser = RequestParser(bundle_errors=True)
sendNotice_reqparser = RequestParser(bundle_errors=True)
grafPrestasiBulanan_reqparser = RequestParser(bundle_errors=True)
getBorangParlimen_reqparser = RequestParser(bundle_errors=True)
grafAnalisisDanStatistik_reqparser = RequestParser(bundle_errors=True)
createOmpBaru_reqparser = RequestParser(bundle_errors=True)
lapisanFitur_reqparser = RequestParser(bundle_errors=True)
grafPerkhidmatanPusatTong_reqparser = RequestParser(bundle_errors=True)
getKategori_reqparser = RequestParser(bundle_errors=True)
getMonthlyPerformance_reqparser = RequestParser(bundle_errors=True)
getNamaMTK_reqparser = RequestParser(bundle_errors=True)
fetchMapCoordinates_reqparser = RequestParser(bundle_errors=True)
getNamaTaman_reqparser = RequestParser(bundle_errors=True)
getNamaKawasan_reqparser = RequestParser(bundle_errors=True)
getMapLapisanFitur_reqparser = RequestParser(bundle_errors=True)
getPetaKawasan_reqparser = RequestParser(bundle_errors=True)
getJadualKutipan_reqparser = RequestParser(bundle_errors=True)
get2ndPetaKawasan_reqparser = RequestParser(bundle_errors=True)
getjadualPembersihan_reqparser = RequestParser(bundle_errors=True)
randomSearch_reqparser = RequestParser(bundle_errors=True)
getOmpBaru_reqparser = RequestParser(bundle_errors=True)
updateOmpBaru_reqparser = RequestParser(bundle_errors=True)
addTextInPublicApplicationList_reqparser = RequestParser(bundle_errors=True)
getMTB_reqparser = RequestParser(bundle_errors=True)
getMTBOfficer_reqparser = RequestParser(bundle_errors=True)
getDailyMTBInquiryInforByMTB_reqparser = RequestParser(bundle_errors=True)
""" ============================= PUBLIC reqparser ============================= """

createAnnouncement_reqparser.add_argument(
    name="announcement_heading", type=str, location="json", required=True, nullable=False
)
createAnnouncement_reqparser.add_argument(
    name="announcement", type=str, location="json", required=True, nullable=False
)
createAnnouncement_reqparser.add_argument(
    name="announcement_path", type=str, location="json", required=True, nullable=False
)
createAnnouncement_reqparser.add_argument(
    name="language", type=str, location="json", required=True, nullable=False
)
deleteAnnouncement_reqparser.add_argument(
    name="announcement_id", type=str, location="json", required=False, nullable=True
)

updateAnnouncement_reqparser.add_argument(
    name="announcement_heading", type=str, location="json", required=True, nullable=False
)
updateAnnouncement_reqparser.add_argument(
    name="announcement", type=str, location="json", required=True, nullable=False
)
updateAnnouncement_reqparser.add_argument(
    name="announcement_path", type=str, location="json", required=True, nullable=False
)

createManual_reqparser.add_argument(
    name="manual_heading", type=str, location="json", required=True, nullable=False
)
createManual_reqparser.add_argument(
    name="manual_body", type=str, location="json", required=True, nullable=False
)
createManual_reqparser.add_argument(
    name="manual_path", type=str, location="json", required=True, nullable=False
)
createManual_reqparser.add_argument(
    name="language", type=str, location="json", required=True, nullable=False
)

updateManual_reqparser.add_argument(
    name="manual_heading", type=str, location="json", required=True, nullable=False
)
updateManual_reqparser.add_argument(
    name="manual_body", type=str, location="json", required=True, nullable=False
)
updateManual_reqparser.add_argument(
    name="manual_path", type=str, location="json", required=True, nullable=False
)

deleteManual_reqparser.add_argument(
    name="manual_id", type=int, location="json", required=False, nullable=True
)

addGalleryPhoto_reqparser.add_argument(
    name="photo_path", type=str, location="json", required=False, nullable=True
)

deleteGalleryPhoto_reqparser.add_argument(
    name="photo_id", type=int, location="json", required=False, nullable=True
)

changePassword_reqparser.add_argument(
    name="new_password", type=str, location="json", required=True, nullable=False
)
public_login_reqparser.add_argument(
    name="id_card_no", type=str, location="json", required=True, nullable=False
)
public_login_reqparser.add_argument(
    name="password", type=str, location="json", required=True, nullable=False
)

public_login_reqparser.add_argument(
    name="lock_flag", type=bool, location="json", required=True, nullable=False
)



public_register_reqparser.add_argument(
    name="name", type=str, location="json", required=True, nullable=False
)
public_register_reqparser.add_argument(
    name="id_card_no", type=str, location="json", required=True, nullable=False
)
public_register_reqparser.add_argument(
    name="email", type=str, location="json", required=True, nullable=False
)
public_register_reqparser.add_argument(
    name="password", type=str, location="json", required=True, nullable=False
)

public_otp_reqparser.add_argument(
    name="otp", type=str, location="json", required=True, nullable=False
)
public_otp_reqparser.add_argument(
    name="id_card_no", type=str, location="json", required=True, nullable=False
)


forgot_reqparser.add_argument(
    name="id_card_no", type=str, location="json", required=True
)
forgot_reqparser.add_argument(
    name="lang", type=str, location="json", required=True
)

updatePhone_reqparser.add_argument(
    name="otp", type=str, location="json", required=True
)

newPassword_reqparser.add_argument(
    name="token", type=str, location="json", required=False
)
newPassword_reqparser.add_argument(
    name="password", type=str, location="json", required=False
)
submitApplication_reqparser.add_argument(
    name="kutipan_sampah", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="sapuan_jalan", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="cucian_longkang", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="pemotongan_rumput", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="dinyatakan_nama_bangunan", type=str, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="strata_title", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="hak_milik_kekal", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="nama_jalan", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="panjang_jalan_mengikut_nama_jalan", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="panjang_longkang", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="luas_kawasan_berumput", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="luas_kawasan_TPKK", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="parkir_area", type=bool, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="surat_permohonan_perkhidmatan_pembersihan_dokumen", type=str, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="surat_salinan_CF_dokumen", type=str, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="salinan_status_pembanginan_dokumen", type=str, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="bagi_status_pembangunan_dokumen", type=str, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="dinyatakan_jenis_sistem", type=str, location="json", required=False, nullable=True
)
submitApplication_reqparser.add_argument(
    name="confirm", type=bool, location="json", required=False, nullable=True
)
updatePublicApplicationList_reqparser.add_argument(
    name="surat_penyerahan_kawasan", type=str, location="json", required=False, nullable=True
)

deleteApplication_reqparser.add_argument(
    name="app_id_list", type=str, location="json", required=False, nullable=True
)

updatesiteVisitInformation_reqparser.add_argument(
    name="tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=False
)
updatesiteVisitInformation_reqparser.add_argument(
    name="lawatan_tapak", type=str, location="json", required=False, nullable=False
)
updatesiteVisitInformation_reqparser.add_argument(
    name="tarikh_lawatan_tapak", type=inputs.date_from_iso8601, location="json", required=False, nullable=False
)
updatesiteVisitInformation_reqparser.add_argument(
    name="keputusan_lawatan_tapak", type=str, location="json", required=False, nullable=False
)
updatesiteVisitInformation_reqparser.add_argument(
    name="makalumat_ketidakpatuhan", type=str, location="json", required=False, nullable=False
)
updatesiteVisitInformation_reqparser.add_argument(
    name="maklum_balas_ketidakpatuhan", type=str, location="json", required=False, nullable=False
)
updatesiteVisitInformation_reqparser.add_argument(
    name="maklumbalas_ketidakpatuhan_filename", type=str, location="json", required=False, nullable=False
)
deleteSiteVisitInformation_reqparser.add_argument(
    name="site_visit_id_list", type=str, location="json", required=False, nullable=False
)
deleteSitevisitPDF_reqparser.add_argument(
    name="site_id", type=int, location="json", required=False, nullable=False
)

addNonComplianceForm_reqparser.add_argument(
    name="site_id", type=str, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="pengesahan_peneriman", type=str, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="nama", type=str, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="alamat", type=str, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=True #2012-01-01T23:30:00
)
addNonComplianceForm_reqparser.add_argument(
    name="lawatan_tapak_tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=True #2012-01-01T23:30:00
)
addNonComplianceForm_reqparser.add_argument(
    name="bertempat_di", type=str, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="wakil", type=str, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="kad_pengenalan", type=str, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="peratusan_permis_adalah_kurang_daripada_50", type=bool, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="kawasan_itu_kotor_dan_perlu_dibersihkan", type=bool, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="tiada_kemudahan_stopper_untuk_tayar_trak", type=bool, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah", type=bool, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="tiada_garisan_kuning_di_hadapan_rumah_sampah", type=bool, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="tong_sampah_tidak_mencukupi_mengikut_spesifikasi", type=bool, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="turning_point_tidak_mengikut_spesifikasi", type=bool, location="json", required=False, nullable=True
)
addNonComplianceForm_reqparser.add_argument(
    name="mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai", type=bool, location="json", required=False, nullable=True
)

updateNonComplianceForm_reqparser.add_argument(
    name="pengesahan_peneriman", type=str, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="nama", type=str, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="alamat", type=str, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=True #2012-01-01T23:30:00
)
updateNonComplianceForm_reqparser.add_argument(
    name="lawatan_tapak_tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=True #2012-01-01T23:30:00
)
updateNonComplianceForm_reqparser.add_argument(
    name="bertempat_di", type=str, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="wakil", type=str, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="peratusan_permis_adalah_kurang_daripada_50", type=bool, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="kawasan_itu_kotor_dan_perlu_dibersihkan", type=bool, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="tiada_kemudahan_stopper_untuk_tayar_trak", type=bool, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah", type=bool, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="tiada_garisan_kuning_di_hadapan_rumah_sampah", type=bool, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="tong_sampah_tidak_mencukupi_mengikut_spesifikasi", type=bool, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="turning_point_tidak_mengikut_spesifikasi", type=bool, location="json", required=False, nullable=True
)
updateNonComplianceForm_reqparser.add_argument(
    name="mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai", type=bool, location="json", required=False, nullable=True
)

submitRating_reqparser.add_argument(
    name="star", type=float, location="json", required=False, nullable=True
)
submitRating_reqparser.add_argument(
    name="feedback", type=str, location="json", required=False, nullable=True
)
uploadFile_reqparser.add_argument(
    name="file", type=werkzeug.datastructures.FileStorage, location='files', required=False, nullable=True
)

getCoordinates_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=True, nullable=True
)
getCoordinates_reqparser.add_argument(
    name="taman", type=str, location="json", required=True, nullable=True
)

mapKawasanPerkhidmatan_reqparser.add_argument(
    name="parlimen", type=str, location='json', required=False, nullable=True
)

updateUserInfo_reqparser.add_argument(
    name="username", type=str, location="json", required=True, nullable=False
)
updateUserInfo_reqparser.add_argument(
    name="email", type=str, location="json", required=True, nullable=False
)
updateUserInfo_reqparser.add_argument(
    name="password", type=str, location="json", required=True, nullable=False
)

""" ============================= AGENSI reqparser ============================= """

deleteFeedbackList_reqparser.add_argument(
    name="feedback_id_list", type=str, location="json", required=False, nullable=True
)
createFeedback_reqparser.add_argument(
    name="np_number", type=str, location="json", required=False, nullable=True
)
createFeedback_reqparser.add_argument(
    name="organization", type=str, location="json", required=False, nullable=True
)
createFeedback_reqparser.add_argument(
    name="merinyu_officer_name", type=str, location="json", required=False, nullable=True
)
createFeedback_reqparser.add_argument(
    name="feedback", type=str, location="json", required=False, nullable=True
)
createFeedback_reqparser.add_argument(
    name="picture_before", type=str, location="json", required=False, nullable=True
)
createFeedback_reqparser.add_argument(
    name="picture_after", type=str, location="json", required=False, nullable=True
)
createFeedback_reqparser.add_argument(
    name="notes", type=str, location="json", required=False, nullable=True
)
updateFeedback_reqparser.add_argument(
    name="organization", type=str, location="json", required=False, nullable=True
)
updateFeedback_reqparser.add_argument(
    name="merinyu_officer_name", type=str, location="json", required=False, nullable=True
)
updateFeedback_reqparser.add_argument(
    name="feedback", type=str, location="json", required=False, nullable=True
)
updateFeedback_reqparser.add_argument(
    name="picture_before", type=str, location="json", required=False, nullable=True
)
updateFeedback_reqparser.add_argument(
    name="picture_after", type=str, location="json", required=False, nullable=True
)
updateFeedback_reqparser.add_argument(
    name="report_image", type=str, location="json", required=False, nullable=True
)
updateFeedback_reqparser.add_argument(
    name="work_done_status", type=bool, location="json", required=False, nullable=True
)

getInvoice_reqparser.add_argument(
    name="invoice_no", type=str, location="json", required=False, nullable=True
)
getInvoice_reqparser.add_argument(
    name="contractor", type=str, location="json", required=False, nullable=True
)


createInvoice_reqparser.add_argument(
    name="invoice_no", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="bulan", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="tahun", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="contractor", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="applicant_name", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="e_mei", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="amount_claim", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="invoice_document", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="summary_document", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="attachment", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="bd44", type=str, location="json", required=False, nullable=True
)
createInvoice_reqparser.add_argument(
    name="laporan_tuntutan", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="invoice_no", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="contractor", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="applicant_name", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="e_mei", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="amount_claim", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="invoice_document", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="summary_document", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="attachment", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="status", type=str, location="json", required=False, nullable=True
)
updateInvoice_reqparser.add_argument(
    name="employee_review", type=str, location="json", required=False, nullable=True
)




""" ============================= DBKL reqparser ============================= """
dbkl_register_reqparser.add_argument(
    name="name", type=str, location="json", required=True, nullable=False
)
dbkl_register_reqparser.add_argument(
    name="nama_pengguna", type=str, location="json", required=True, nullable=False
)
dbkl_register_reqparser.add_argument(
    name="email", type=str, location="json", required=True, nullable=False
)
dbkl_register_reqparser.add_argument(
    name="password", type=str, location="json", required=True, nullable=False
)
dbkl_otp_reqparser.add_argument(
    name="otp", type=str, location="json", required=True, nullable=False
)
dbkl_otp_reqparser.add_argument(
    name="nama_pengguna", type=str, location="json", required=True, nullable=False
)

dbkl_login_reqparser.add_argument(
    name="nama_pengguna", type=str, location="json", required=True, nullable=False
)
dbkl_login_reqparser.add_argument(
    name="password", type=str, location="json", required=True, nullable=False
)

dbkl_forgot_reqparser.add_argument(
    name="nama_pengguna", type=str, location="json", required=True
)
dbkl_forgot_reqparser.add_argument(
    name="lang", type=str, location="json", required=True
)
assignRole_reqparser.add_argument(
    name="id_card_number", type=str, location="json", required=False, nullable=True
)
assignRole_reqparser.add_argument(
    name="role", type=str, location="json", required=True, nullable=False
)
assignRole_reqparser.add_argument(
    name="role", type=str, location="json", required=True, nullable=False
)
assignRole_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)



addMeeting_reqparser.add_argument(
    name="tarikh", type=inputs.datetime_from_iso8601, location="json", required=False, nullable=True
)
addMeeting_reqparser.add_argument(
    name="masa", type=str, location="json", required=False, nullable=True
)
addMeeting_reqparser.add_argument(
    name="tempat", type=str, location="json", required=False, nullable=True
)

updateMeeting_reqparser.add_argument(
    name="tarikh", type=inputs.datetime_from_iso8601, location="json", required=False, nullable=True
)
updateMeeting_reqparser.add_argument(
    name="masa", type=str, location="json", required=False, nullable=True
)
updateMeeting_reqparser.add_argument(
    name="tempat", type=str, location="json", required=False, nullable=True
)

addDetailedMeeting_reqparser.add_argument(
    name="jenis_jawatankuasa", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="jenis_mesyuarat", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="jabatan_terlibat", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="tarikh_mesyuarat", type=str, location="json", required=True, nullable=False
)
addDetailedMeeting_reqparser.add_argument(
    name="masa_mesyuarat", type=str, location="json", required=True, nullable=False
)
addDetailedMeeting_reqparser.add_argument(
    name="hingga", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="pengerusi", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="bill_mesyuarat", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="tajuk_mesyuarat", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="setiausaha", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="tempat_mesyuarat", type=str, location="json", required=True, nullable=False
)
addDetailedMeeting_reqparser.add_argument(
    name="agenda_dan_minit", type=str, location="json", required=False, nullable=True
)
addDetailedMeeting_reqparser.add_argument(
    name="meeting_dokumen", type=str, location="json", required=False, nullable=True
)

listDetailedMeeting_reqparser.add_argument(
    name="jenis_mesyuarat", type=str, location="json", required=False, nullable=True
)
listDetailedMeeting_reqparser.add_argument(
    name="jawatankuasa_mesurat", type=str, location="json", required=False, nullable=True
)

updateEMeeting_reqparser.add_argument(
    name="jenis_jawatankuasa", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="jenis_mesyuarat", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="jabatan_terlibat", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="tarikh_mesyuarat", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="masa_mesyuarat", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="hingga", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="pengerusi", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="bill_mesyuarat", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="tajuk_mesyuarat", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="setiausaha", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="tempat_mesyuarat", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="agenda_dan_minit", type=str, location="json", required=False, nullable=True
)
updateEMeeting_reqparser.add_argument(
    name="meeting_dokumen", type=str, location="json", required=False, nullable=True
)


updateDetailedMeeting_reqparser.add_argument(
    name="tarikh_mesyuarat", type=str, location="json", required=False, nullable=True
)
updateDetailedMeeting_reqparser.add_argument(
    name="masa_mesyuarat", type=str, location="json", required=False, nullable=True
)
updateDetailedMeeting_reqparser.add_argument(
    name="tempat_mesyuarat", type=str, location="json", required=False, nullable=True
)


deleteMeeting_reqparser.add_argument(
    name="meeting_id_list", type=str, location="json", required=False, nullable=True
)

updateInventoriPengguna_reqparser.add_argument(
    name="nama_pengguna", type=str, location="json", required=False, nullable=True
)
updateInventoriPengguna_reqparser.add_argument(
    name="peranan", type=str, location="json", required=False, nullable=True
)
updateInventoriPengguna_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
deleteInventoriPengguna_reqparser.add_argument(
    name="id_pengguna_list", type=str, location="json", required=False, nullable=True
)

updateApplicationList_reqparser.add_argument(
   name="status_semakan_dokumen", type=bool, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="catatan", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="status_semakan_dokumen", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="status_keputusan_permohonan", type=str, location="json", required=False, nullable=True,
)


updateApplicationList_reqparser.add_argument(
   name="tarikh_keputusan_permohonan", type=inputs.date_from_iso8601, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="filename_keputusan_permohonan", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="catatan", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="emesy_bil_no", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="emesy_tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="emesy_filename", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="senarai_kwsn_bil_no", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="senarai_kwsn_tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="senarai_kwsn_tempat", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="senarai_kwsn_filename", type=str, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="senarai_kwsn_minit_msyrt_tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=True,
)

updateApplicationList_reqparser.add_argument(
   name="senarai_kwsn_minit_msyrt_filename", type=str, location="json", required=False, nullable=True,
)


updateApplication_reqparser.add_argument(
   name="kutipan_sampah", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="sapuan_jalan", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="cucian_longkang", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="pemotongan_rumput", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="dinyatakan_nama_bangunan", type=str, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="strata_title", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="hak_milik_kekal", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="nama_jalan", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="panjang_jalan_mengikut_nama_jalan", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="panjang_longkang", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="luas_kawasan_berumput", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="luas_kawasan_TPKK", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="parkir_area", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="surat_permohonan_perkhidmatan_pembersihan_dokumen", type=str, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="surat_salinan_CF_dokumen", type=str, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="salinan_status_pembanginan_dokumen", type=str, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="bagi_status_pembangunan_dokumen", type=str, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="surat_permohonan_perkhidmatan_pembersihan_status", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="surat_salinan_CF_status", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="salinan_status_pembanginan_status", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="bagi_status_pembangunan_status", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
    name="surat_permohonan_perkhidmatan_pembersihan_catatan", type=str, location="json", required=False, nullable=True
)
updateApplication_reqparser.add_argument(
    name="surat_salinan_CF_catatan", type=str, location="json", required=False, nullable=True
)
updateApplication_reqparser.add_argument(
    name="salinan_status_pembanginan_catatan", type=str, location="json", required=False, nullable=True
)
updateApplication_reqparser.add_argument(
    name="bagi_status_pembangunan_catatan", type=str, location="json", required=False, nullable=True
)
updateApplication_reqparser.add_argument(
   name="status_dokumen_keseluruhan", type=bool, location="json", required=False, nullable=True 
)
updateApplication_reqparser.add_argument(
   name="dinyatakan_jenis_sistem", type=str, location="json", required=False, nullable=True 
)


deleteApplicationList_reqparser.add_argument(
    name="application_id_list", type=str, location="json", required=False, nullable=True
)

updateStatusSemakanDokumen_reqparser.add_argument(
   name="status_semakan_dokumen", type=bool, location="json", required=False, nullable=True 
)
updateStatusSemakanDokumen_reqparser.add_argument(
   name="surat_penyerahan_kawasan", type=str, location="json", required=False, nullable=True 
)

updateSiteVisit_reqparser.add_argument(
   name="tarikh", type=inputs.date_from_iso8601, location="json", required=False, nullable=True 
)
updateSiteVisit_reqparser.add_argument(
   name="lawatan_tapak", type=str, location="json", required=False, nullable=True 
)
updateSiteVisit_reqparser.add_argument(
   name="tarikh_lawatan_tapak", type=inputs.date_from_iso8601, location="json", required=False, nullable=True 
)
updateSiteVisit_reqparser.add_argument(
   name="keputusan_lawatan_tapak", type=str, location="json", required=False, nullable=True 
)
updateSiteVisit_reqparser.add_argument(
   name="makalumat_ketidakpatuhan", type=str, location="json", required=False, nullable=True 
)
updateSiteVisit_reqparser.add_argument(
   name="maklum_balas_ketidakpatuhan", type=str, location="json", required=False, nullable=True 
)
updateSiteVisit_reqparser.add_argument('tarikh_datetime', type=str, required=False, help='Date and time for site visit')

updateSiteVisit_reqparser.add_argument(
   name="tetapan_lawatan_tapak_filename", type=str, location="json", required=False, nullable=True 
)

updateSiteVisit_reqparser.add_argument(
   name="keputusan_lawatan_tapak_filename", type=str, location="json", required=False, nullable=True 
)

updateSiteVisit_reqparser.add_argument(
   name="status_maklumbalas_ketidakpatuhan", type=str, location="json", required=False, nullable=True 
)

updateSiteVisit_reqparser.add_argument(
   name="maklumbalas_ketidakpatuhan_filename", type=str, location="json", required=False, nullable=True 
)

deleteSitevisitInformation_reqparser.add_argument(
    name="site_id_list", type=str, location="json", required=False, nullable=True
)

updateJobPaymentClaimByInbois_reqparser.add_argument(
   name="nama_pemohon", type=str, location="json", required=False, nullable=True 
)
updateJobPaymentClaimByInbois_reqparser.add_argument(
   name="e_mei", type=str, location="json", required=False, nullable=True 
)
updateJobPaymentClaimByInbois_reqparser.add_argument(
   name="jumlah_tuntutan", type=str, location="json", required=False, nullable=True 
)
updateJobPaymentClaimByInbois_reqparser.add_argument(
   name="inbois_dokumen", type=str, location="json", required=False, nullable=True 
)
updateJobPaymentClaimByInbois_reqparser.add_argument(
   name="ringkasan_dokumen", type=str, location="json", required=False, nullable=True 
)
updateJobPaymentClaimByInbois_reqparser.add_argument(
   name="lampiran", type=str, location="json", required=False, nullable=True 
)
updateJobPaymentClaimByInbois_reqparser.add_argument(
   name="status", type=str, location="json", required=False, nullable=True 
)
updateJobPaymentClaimByInbois_reqparser.add_argument(
   name="ulasan_pegawai", type=str, location="json", required=False, nullable=True 
)
deleteJobPaymentClaim_reqparser.add_argument(
    name="agensi_id_list", type=str, location="json", required=False, nullable=True
)
getSapuanCucianCoordinates_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=True, nullable=False
)
getSapuanCucianCoordinates_reqparser.add_argument(
    name="lokasi", type=str, location="json", required=True, nullable=False
)
# getSapuanCucianCoordinates_reqparser.add_argument(
#     name="service_list", type=str, location="json", required=True, nullable=False
# )

addComplaintInvestigation_reqparser.add_argument(
    name="id_pegawai", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="jenis_kawasan", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="pengadu_nama", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="pengadu_alamat", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="no_telefon", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="no_rujukan", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="emel", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="no_faksimili", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="sumber_aduan", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="lain_lain", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="tarikh_aduan", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="tarikh_terima", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="lokasi_aduan", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="keterangan_aduan", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="zon", type=str, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="tarikh_siasatan", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
addComplaintInvestigation_reqparser.add_argument(
    name="nama_pegawai", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="lokasi_siasatan", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="laporan_siasatan", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="tindakan", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="susulan", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="ullasan_penyelia", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="ullasan_ketua_seksyen", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="ulasanKetua_unitf1", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="gambar", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="cause", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="no_ic_pegawai_mtk", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="picture1", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="picture2", type=str, location="json", required=False, nullable=True
)
addComplaintInvestigation_reqparser.add_argument(
    name="picture3", type=str, location="json", required=False, nullable=True
)
updateComplaintInvestigation_reqparser.add_argument(
    name="pengadu_nama", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="pengadu_alamat", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="no_telefon", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="no_rujukan", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="tarikh_terima_aduan", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="emel", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="no_faksimili", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="sumber_aduan", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="lain_lain", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="tarikh_aduan", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="tarikh_terima", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="lokasi_aduan", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="keterangan_aduan", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="zon", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="tarikh_siasatan", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="nama_pegawai", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="lokasi_siasatan", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="laporan_siasatan", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="tindakan", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="susulan", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="ullasan_penyelia", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="ullasan_ketua_seksyen", type=str, location="json", required=True, nullable=False
)
updateComplaintInvestigation_reqparser.add_argument(
    name="ulasan_timbalan", type=str, location="json", required=True, nullable=False
)
updateComplaintComments_reqparser.add_argument(
    name="formId", type=int, location="json", required=True, nullable=False
)
updateComplaintComments_reqparser.add_argument(
    name="ulasanPenyelia", type=str, location="json", required=False, nullable=True
)
updateComplaintComments_reqparser.add_argument(
    name="ulasanKetuaSeksyen", type=str, location="json", required=False, nullable=True
)
updateComplaintComments_reqparser.add_argument(
    name="ulasanKetuaUnit", type=str, location="json", required=False, nullable=True
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="id_pegawai", type=str, location="json", required=True, nullable=False
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="parlimenA", type=str, location="json", required=True, nullable=False
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="zon", type=str, location="json", required=True, nullable=False
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="tarikh_siasatan", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="lokasi_siasatan", type=str, location="json", required=True, nullable=False
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="picture1", type=str, location="json", required=False, nullable=True
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="picture2", type=str, location="json", required=False, nullable=True
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="picture3", type=str, location="json", required=False, nullable=True
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="laporan_siasatan", type=str, location="json", required=True, nullable=False
)
add2ndComplaintInvestigation_reqparser.add_argument(
    name="tindakan", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="pengadu_nama", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="pengadu_alamat", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="no_telefon", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="no_rujukan", type=str, location="json", required=True, nullable=False
)

add3rdComplaintInvestigation_reqparser.add_argument(
    name="emel", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="no_faksimili", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="sumber_aduan", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="lain_lain", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="tarikh_aduan", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="tarikh_terima", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="lokasi_aduan", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="keterangan_aduan", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="ullasan_penyelia", type=str, location="json", required=False, nullable=True
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="ullasan_ketua_seksyen", type=str, location="json", required=False, nullable=True
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="gambar", type=str, location="json", required=True, nullable=False
)
add3rdComplaintInvestigation_reqparser.add_argument(
    name="cause", type=str, location="json", required=True, nullable=False
)
getComplaintInvestigation_reqparser.add_argument(
    name="id_mtb", type=str, location="json", required=False, nullable=True
)
getComplaintInvestigation_reqparser.add_argument(
    name="masa_siasatan", type=str, location="json", required=False, nullable=True
)
getComplaintInvestigation_reqparser.add_argument(
    name="tarikh_siasatan", type=inputs.date_from_iso8601, location="json", required=False, nullable=True
)
getComplaintInvestigation_reqparser.add_argument(
    name="complaint_id", type=str, location="json", required=False, nullable=True
)
getComplaintInvestigation_reqparser.add_argument(
    name="inquiry_id", type=str, location="json", required=False, nullable=True
)

mtbInquiry_reqparser.add_argument(
    name="tarikh", type=str, location="json", required=True, nullable=False
)
mtbInquiry_reqparser.add_argument(
    name="officer_name", type=str, location="json", required=False, nullable=True
)
getMTBOfficersTarikh_reqparser.add_argument(
    name="officer_name", type=str, location="json", required=False, nullable=True
)


mtbCompoundInformation_reqparser.add_argument(
    name="tarikh", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
mtbCompoundInformation_reqparser.add_argument(
    name="id_mtb", type=str, location="json", required=True, nullable=False
)
mtbCompoundInformation_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=True, nullable=False
)

mtbCompoundInfoByMTB_reqparser.add_argument(
    name="tarikh", type=str, location="json", required=True, nullable=False
)


addMTBCompoundForm_reqparser.add_argument(
    name="id_pegawai", type=str, location="json", required=False, nullable=True
)
addMTBCompoundForm_reqparser.add_argument(
    name="no_notis_bas", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="kepada", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="company_no", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="alamat", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="id_mtb", type=str, location="json", required=False, nullable=True
)
addMTBCompoundForm_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="addSeksyen", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="butir_butir_kesalahan", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="tarikh", type=inputs.date_from_iso8601, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="waktu", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="tempat", type=str, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek47_1a", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek47_1c", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek47_1d", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek47_1e", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek47_1g", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek47_2a", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek47_2b", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk8", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk9", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk3", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek46_1b", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek46_1c", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek46_1d", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek46_1e", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek46_1f", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="sek46_1g", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk5_a", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk5_a", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk5_b", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk5_c", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk33", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk34", type=bool, location="json", required=True, nullable=False
)
addMTBCompoundForm_reqparser.add_argument(
    name="uuk35", type=bool, location="json", required=True, nullable=False
)
sendNotice_reqparser.add_argument(
    name="id_mtb", type=str, location="json", required=True, nullable=False
)
sendNotice_reqparser.add_argument(
    name="nama_pegawai_merinyu", type=str, location="json", required=True, nullable=False
)
sendNotice_reqparser.add_argument(
    name="lokasi_merinyu", type=str, location="json", required=True, nullable=False
)
sendNotice_reqparser.add_argument(
    name="gambar_lokasi_kerja_photo1", type=str, location="json", required=True, nullable=False
)
sendNotice_reqparser.add_argument(
    name="gambar_lokasi_kerja_photo2", type=str, location="json", required=True, nullable=False
)
sendNotice_reqparser.add_argument(
    name="gambar_lokasi_kerja_photo3", type=str, location="json", required=True, nullable=False
)
sendNotice_reqparser.add_argument(
    name="status_tindakan", type=str, location="json", required=True, nullable=False
)

sendNotice_reqparser.add_argument(
    name="kontraktor_emel", type=str, location="json", required=True, nullable=False
)

getFilteredLokasi_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=True, nullable=False
)
getFilteredLokasi_reqparser.add_argument(
    name="lokasi", type=str, location="json", required=True, nullable=False
)

grafPrestasiBulanan_reqparser.add_argument(
    name="id_pegawai_merinyu", type=str, location="json", required=False, nullable=True
)
grafPrestasiBulanan_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
grafPrestasiBulanan_reqparser.add_argument(
    name="nama_pegawai", type=str, location="json", required=False, nullable=True
)
grafPrestasiBulanan_reqparser.add_argument(
    name="sub_area", type=str, location="json", required=False, nullable=True
)

grafAnalisisDanStatistik_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)

createOmpBaru_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="lokasi", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="kordinat", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="jumlah_unit_premis", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sisa_domestik", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sampah_pukal", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="domestic_category", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="domestic_total", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="domestic_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="domestic_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="pukal_category", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="pukal_total", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="pukal_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="pukal_freq", type=str, location="json", required=False, nullable=True
)


createOmpBaru_reqparser.add_argument(
    name="sapuan_domestic_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_domestic_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_domestic_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_komersial_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_komersial_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_komersial_freq", type=str, location="json", required=False, nullable=True
)


createOmpBaru_reqparser.add_argument(
    name="cucian_domestic_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_domestic_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_domestic_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_komersial_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_komersial_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_komersial_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_drain_domestic_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_drain_domestic_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_drain_domestic_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_drain_komersial_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_drain_komersial_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_drain_komersial_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_jejantas_dalam_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_jejantas_dalam_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_jejantas_dalam_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_jejantas_atas_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_jejantas_atas_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_jejantas_atas_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_roof_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_roof_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_roof_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_gulam1_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_gulam1_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_gulam1_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_gulam2_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_gulam2_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siar_gulam2_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_tandas_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_tandas_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_tandas_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_teksi_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_teksi_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_teksi_total", type=str, location="json", required=False, nullable=True
)

createOmpBaru_reqparser.add_argument(
    name="bersih_lapang_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_lapang_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_lapang_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_tpkk_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_tpkk_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_tpkk_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_penjaja_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_penjaja_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_penjaja_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_pasar_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_pasar_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_pasar_freq", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_pasar_mlm_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_pasar_mlm_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="bersih_pasar_mlm_freq", type=str, location="json", required=False, nullable=True
)

createOmpBaru_reqparser.add_argument(
    name="rumput_unit", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="rumput_rate", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="rumput_freq", type=str, location="json", required=False, nullable=True
)


createOmpBaru_reqparser.add_argument(
    name="sampah_haram", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_jalan", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_TPKK", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_parkir", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sapuan_jejantas", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_jejantas", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siarkaki", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_siarkaki_berbumbung", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_stesenbas_teksi", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="cucian_longkang", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="potong_rumput", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="sampah_kebun", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="catatan", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="rujukan_tarikh_serahan", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="tarikh_semakandi_lapangant_keadeansemata_ada", type=str, location="json", required=True, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="surat_serahan", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="kadar", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="frekuensi", type=str, location="json", required=False, nullable=True
)
createOmpBaru_reqparser.add_argument(
    name="tarikh_semakandi_lapangant_keadeansemata_tiada", type=str, location="json", required=True, nullable=True
)
lapisanFitur_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
grafPerkhidmatanPusatTong_reqparser.add_argument(
    name="lapisan_fitur", type=str, location="json", required=False, nullable=True
)

getKategori_reqparser.add_argument(
    name="lapisan_fitur", type=str, location="json", required=False, nullable=True
)

getMonthlyPerformance_reqparser.add_argument(
    name="bulan", type=str, location="json", required=False, nullable=True
)
getMonthlyPerformance_reqparser.add_argument(
    name="tahun", type=int, location="json", required=False, nullable=True
)
getMonthlyPerformance_reqparser.add_argument(
    name="zon", type=str, location="json", required=False, nullable=True
)
getMonthlyPerformance_reqparser.add_argument(
    name="nama_mtk", type=str, location="json", required=False, nullable=True
)
getNamaMTK_reqparser.add_argument(
    name="zon", type=str, location="json", required=False, nullable=True
)

fetchMapCoordinates_reqparser.add_argument(
    name="id_mtk", type=str, location="json", required=False, nullable=True
)
fetchMapCoordinates_reqparser.add_argument(
    name="zon", type=str, location="json", required=False, nullable=True
)




getNamaTaman_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
getNamaTaman_reqparser.add_argument(
    name="nama_jalan", type=str, location="json", required=False, nullable=True
)

getNamaKawasan_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
getNamaKawasan_reqparser.add_argument(
    name="nama_jalan", type=str, location="json", required=False, nullable=True
)
getNamaKawasan_reqparser.add_argument(
    name="nama_taman", type=str, location="json", required=False, nullable=True
)

getMapLapisanFitur_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
getMapLapisanFitur_reqparser.add_argument(
    name="nama_jalan", type=str, location="json", required=False, nullable=True
)
getMapLapisanFitur_reqparser.add_argument(
    name="nama_taman", type=str, location="json", required=False, nullable=True
)
getMapLapisanFitur_reqparser.add_argument(
    name="nama_kawasan", type=str, location="json", required=False, nullable=True
)

getPetaKawasan_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
getPetaKawasan_reqparser.add_argument(
    name="nama_jalan", type=str, location="json", required=False, nullable=True
)
getPetaKawasan_reqparser.add_argument(
    name="nama_taman", type=str, location="json", required=False, nullable=True
)
getPetaKawasan_reqparser.add_argument(
    name="nama_kawasan", type=str, location="json", required=False, nullable=True
)
getPetaKawasan_reqparser.add_argument(
    name="lapisan_fitur", type=str, location="json", required=False, nullable=True
)
getPetaKawasan_reqparser.add_argument(
    name="servis_perkhidmatan_jkas", type=str, location="json", required=False, nullable=True
)

getJadualKutipan_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
getJadualKutipan_reqparser.add_argument(
    name="nama_jalan", type=str, location="json", required=False, nullable=True
)
getJadualKutipan_reqparser.add_argument(
    name="nama_taman", type=str, location="json", required=False, nullable=True
)
getJadualKutipan_reqparser.add_argument(
    name="nama_kawasan", type=str, location="json", required=False, nullable=True
)
getJadualKutipan_reqparser.add_argument(
    name="lapisan_fitur", type=str, location="json", required=False, nullable=True
)
getJadualKutipan_reqparser.add_argument(
    name="kekerapan", type=str, location="json", required=False, nullable=True
)

get2ndPetaKawasan_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
get2ndPetaKawasan_reqparser.add_argument(
    name="nama_jalan", type=str, location="json", required=False, nullable=True
)
get2ndPetaKawasan_reqparser.add_argument(
    name="nama_taman", type=str, location="json", required=False, nullable=True
)
get2ndPetaKawasan_reqparser.add_argument(
    name="nama_kawasan", type=str, location="json", required=False, nullable=True
)
get2ndPetaKawasan_reqparser.add_argument(
    name="lapisan_fitur", type=str, location="json", required=False, nullable=True
)
get2ndPetaKawasan_reqparser.add_argument(
    name="servis_perkhidmatan_jkas", type=str, location="json", required=False, nullable=True
)

getjadualPembersihan_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
getjadualPembersihan_reqparser.add_argument(
    name="nama_jalan", type=str, location="json", required=False, nullable=True
)
getjadualPembersihan_reqparser.add_argument(
    name="nama_taman", type=str, location="json", required=False, nullable=True
)
getjadualPembersihan_reqparser.add_argument(
    name="nama_kawasan", type=str, location="json", required=False, nullable=True
)
getjadualPembersihan_reqparser.add_argument(
    name="lapisan_fitur", type=str, location="json", required=False, nullable=True
)
getjadualPembersihan_reqparser.add_argument(
    name="aktiviti", type=str, location="json", required=False, nullable=True
)

randomSearch_reqparser.add_argument(
    name="search_body", type=str, location="json", required=False, nullable=True
)

getOmpBaru_reqparser.add_argument(
    name="parliament_name", type=str, location="json", required=False, nullable=True
)
getOmpBaru_reqparser.add_argument(
    name="parliament_subarea", type=str, location="json", required=False, nullable=True
)

updateOmpBaru_reqparser.add_argument(
    name="kodarea", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="lokasi", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="parlimen", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="parlimen_subarea", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="kordinat", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="jumlah_unit_premis", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="kekerapan_kutipan_sisa_domestik", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="kekerapan_kutipan_sampah_pukal", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="kekerapan_kutipan_sampah_haram", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_sapuan_jalan", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_sapuan_TPKK", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_sapuan_kaw_lapang_parkir", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_sapuan_jejantas", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_cucian_jejantas", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_cucian_siarkaki", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_cucian_siarkaki_berbumbung", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_cucian_stesenbas_teksi", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_cucian_longkang", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_potongrumput", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="ukuran_panjang_sampahkebun", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="catatan", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="rujuken_tarikh_serahan", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="tarikh_semakandi_lapangant_keadeansemata_ada", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="tarikh_semakandi_lapangant_keadeansemata_tiada", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="kadar", type=str, location="json", required=False, nullable=True
)
updateOmpBaru_reqparser.add_argument(
    name="frekuensi", type=str, location="json", required=False, nullable=True
)
addTextInPublicApplicationList_reqparser.add_argument(
    name="application_id", type=int, location="json", required=False, nullable=True
)
addTextInPublicApplicationList_reqparser.add_argument(
    name="text", type=str, location="json", required=False, nullable=True
)

getMTB_reqparser.add_argument(
    name="officer_name", type=str, location="json", required=False, nullable=True
)


getMTBOfficer_reqparser.add_argument(
    name="id_mtb", type=str, location="json", required=False, nullable=True
)
getDailyMTBInquiryInforByMTB_reqparser.add_argument(
    name="tarikh", type=str, location="json", required=False, nullable=True
)
getDailyMTBInquiryInforByMTB_reqparser.add_argument(
    name="id_mtb", type=str, location="json", required=False, nullable=True
)
masterUser_model = Model(
    "MasterUser",
    {
        "id": String,
        "nama": String,
        "no_kad_pengenalan": String,
        "alamat_emel": String,
        
    },
)
