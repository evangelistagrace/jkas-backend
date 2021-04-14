""" Business logic for /auth API endpoints."""
from http import HTTPStatus
import os
import json 
import sys, re
from random import randint 
from datetime import datetime, date
from time import strftime
from flask import current_app, jsonify, session
from flask_restx import abort
from twilio.rest import Client
import requests
import itertools
import logging
from applogger import logger
from app.main import db
from .decorators import token_required
from app.main.models.token_blacklist import BlacklistedToken
from app.main.models.models import (
    MasterUser, PublicAnnouncement, PublicManual, PhotoGallery, PublicApplicationList, PublicApplicationDetails, MeetingArea, MeetingPdfPath, 
    PublicSiteVisitInfo, NonComplianceForm, SiteVisitPdfPath, PublicRating, AgensiFeedback, AgencyJobPaymentClaim)
from app.main.util.datetime_util import (
    remaining_fromtimestamp,
    format_timespan_digits,
)


""" ===============================<< get Agensi starts >>=============================== """

def getAgensi(np_number):
    np_number = np_number.upper()
    if MasterUser.find_by_id_card(np_number):
        try:
            agensi_info = []
            for agensi in MasterUser.query.filter_by(no_kad_pengenalan=np_number, active=1):
                agensi_info.append({
                "no_kad_pengenalan":agensi.no_kad_pengenalan,
                "lokasi":agensi.lokasi,
                "nama_pegawai_merinyu":agensi.nama_pegawai_merinyu,
                "parlimen":agensi.parlimen,
                "status_tindakan":agensi.status_tindakan 
            })
            logger.info("Agensi fetched")
            return jsonify(agensi_info)
        except:
            logger.exception("Agensi could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Agensi could not be fetched',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': f'No Agensi is registered with NP id {np_number}',
        }
        return response_object, 404

""" ===============================<< get Agensi ends >>=============================== """
""" ===============================<< get Feedback List starts >>=============================== """

def getFeedbackList(np_number):
    np_number = np_number.upper()
    if AgensiFeedback.find_by_np(np_number):
        try:
            feedback_list = []
            for feed in AgensiFeedback.query.filter_by(no_siri_notis_pemberitahuan=np_number, active=1):
                feedback_list.append({
                "feedback_id":feed.feedback_id,
                "no_siri_notis_pemberitahuan":feed.no_siri_notis_pemberitahuan,
                "organisasi":feed.organisasi,
                "nama_pegawai_merinyu":feed.nama_pegawai_merinyu,
                "maklum_balas":feed.maklum_balas,
                "gambar_sebelum":feed.gambar_sebelum, 
                "gambar_selepas":feed.gambar_selepas, 
                "sebelum_tarikh_masa":feed.sebelum_tarikh_masa, 
                "selepas_tarikh_masa":feed.selepas_tarikh_masa, 
                "gambar_laporan":feed.gambar_laporan,
                "laporan_tarikh_masa":feed.laporan_tarikh_masa,
                "kerja_selesail":feed.kerja_selesail, 
            })
            logger.info("Feedbcak list fetched")
            return jsonify(feedback_list)
        except:
            logger.exception("Feedback list could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Feedback list could not be fetched',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': f'No Feedback is registered with NP id {np_number}',
        }
        return response_object, 404

""" ===============================<< get Feedback List ends >>=============================== """
""" ===============================<< Delete Feedback List starts >>===============================  """

def deleteFeedbackList(data):
    feedback_id_list = data.feedback_id_list.split(",")
    try:
        for i in feedback_id_list:
            if AgensiFeedback.query.filter_by(feedback_id=i).first():
                AgensiFeedback.query.filter_by(feedback_id=i).first().active = 0
                    
        db.session.commit()
        logger.info("Feedback list Deleted successfully")
            
        response_object = {
            "status": "success",
            "message": "Feedback list Deleted successfully"
        }
        return response_object, 200
    except:
        logger.exception("Feedback list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Feedback list could not be Deleted"
        }
        return response_object, 400
            
""" ===============================<< Delete Feedback List ends >>===============================  """
""" ===============================<< get Feedback starts >>=============================== """

def getFeedback(feedback_id):
    try:
        feedback_content = db.session.query(AgensiFeedback).filter_by(feedback_id=feedback_id, active=1).one()
    except:
        response_object = {
            'status': 'fail',
            'message': f'No Feedback is registered with feedback_id {feedback_id}',
        }
        return response_object, 404
    if feedback_content:
        try:
            feedback_info = []
            for feed in AgensiFeedback.query.filter_by(feedback_id=feedback_id, active=1):
                feedback_info.append({
                "feedback_id":feed.feedback_id,
                "no_siri_notis_pemberitahuan":feed.no_siri_notis_pemberitahuan,
                "organisasi":feed.organisasi,
                "nama_pegawai_merinyu":feed.nama_pegawai_merinyu,
                "maklum_balas":feed.maklum_balas,
                "gambar_sebelum":feed.gambar_sebelum, 
                "gambar_selepas":feed.gambar_selepas, 
                "sebelum_tarikh_masa": feed.sebelum_tarikh_masa, 
                "selepas_tarikh_masa": feed.selepas_tarikh_masa, 
                "gambar_laporan":feed.gambar_laporan,
                "laporan_tarikh_masa":feed.laporan_tarikh_masa,
                "kerja_selesail":feed.kerja_selesail, 
            })
            logger.info("Feedbcak fetched")
            return jsonify(feedback_info)
        except:
            logger.exception("Feedback could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Feedback could not be fetched',
            }
            return response_object, 400
        
""" ===============================<< get Feedback ends >>=============================== """

""" ===============================<< Ceate Feedback starts >>=============================== """

def createFeedback(data):
    np_number = data.np_number.upper()
    organization = data.organization
    merinyu_officer_name = data.merinyu_officer_name
    feedback = data.feedback
    picture_before = data.picture_before
    picture_after = data.picture_after
    if picture_before:
        picture_before = re.sub('[^a-zA-Z0-9.]', '', picture_before)
        picture_before = '/jkas_resourses/public/images/'+picture_before
        before_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        before_date = None
        before_time = None
    if picture_after:
        picture_after = re.sub('[^a-zA-Z0-9.]', '', picture_after)
        picture_after = '/jkas_resourses/public/images/'+picture_after
        after_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        after_date = None
        after_time = None
    today = date.today()

    try:
        if MasterUser.find_by_id_card(np_number):
            new_feedback = AgensiFeedback(no_siri_notis_pemberitahuan=np_number, organisasi=organization, nama_pegawai_merinyu=merinyu_officer_name, maklum_balas=feedback,
                                        gambar_sebelum=picture_before, gambar_selepas=picture_after, sebelum_tarikh_masa=before_date,selepas_tarikh_masa=after_date
                                        ,inserted_by=np_number,inserted_date=today, active=1)
            db.session.add(new_feedback)
            db.session.commit()
            logger.info("Feedback Created Successfully")
            response_object = {
                'status': 'success',
                'message': 'Feedback Added.',
            }
            logger.info("Feedback Added")
            return response_object, 201
        else:
            logger.exception("Feedback could not be added")
            response_object = {
                'status': 'fail',
                'message': f'No Agensi with NP id {np_number} found',
            }
        return response_object, 409 
    except:
        logger.exception("Feedback could not be added")
        response_object = {
            'status': 'fail',
            'message': 'Feedback not added.',
        }
        return response_object, 409
    
""" ===============================<< Create Feedback ends >>=============================== """

""" ===============================<< Update Feedback starts >>=============================== """

def updateFeedback(feedback_id,data):
    feedback_details = db.session.query(AgensiFeedback).filter_by(feedback_id=feedback_id, active=1).one()
    if feedback_details:   
        try:                                       
            organization = data.organization
            merinyu_officer_name = data.merinyu_officer_name
            feedback = data.feedback
            picture_before = data.picture_before
            picture_after = data.picture_after
            report_image = data.report_image
            work_done_status = data.work_done_status
            today = date.today()
            
            if picture_before:
                picture_before = re.sub('[^a-zA-Z0-9.]', '', picture_before)
                feedback_details.gambar_sebelum='/jkas_resourses/public/images/'+picture_before
                feedback_details.sebelum_tarikh_masa = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                feedback_details.gambar_sebelum=feedback_details.gambar_sebelum
                feedback_details.sebelum_tarikh_masa = feedback_details.sebelum_tarikh_masa
            if picture_after:
                picture_after = re.sub('[^a-zA-Z0-9.]', '', picture_after)
                feedback_details.gambar_selepas='/jkas_resourses/public/images/'+picture_after
                feedback_details.selepas_tarikh_masa = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                feedback_details.gambar_selepas=feedback_details.gambar_selepas
                feedback_details.selepas_tarikh_masa = feedback_details.selepas_tarikh_masa
    
            feedback_details.organisasi=organization
            feedback_details.nama_pegawai_merinyu=merinyu_officer_name
            feedback_details.maklum_balas=feedback            
            if report_image:
                report_image = re.sub('[^a-zA-Z0-9.]', '', report_image)
                feedback_details.gambar_laporan='/jkas_resourses/public/images/'+report_image
                feedback_details.laporan_tarikh_masa = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                feedback_details.laporan_tarikh_masa = feedback_details.laporan_tarikh_masa
                   
            feedback_details.kerja_selesail=work_done_status
            feedback_details.updated_by=feedback_details.no_siri_notis_pemberitahuan
            feedback_details.updated_date=today
            db.session.commit()
            logger.info("Feedback Updated Successfully")
            
            response_object = {
                'status': 'success',
                'message': 'Feedback Updated.',
            }
            return response_object, 201
        except:
            logger.exception("Feedback could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'Feedback not updated.',
            }
            return response_object, 409
    else:
        response_object = {
                'status': 'fail',
                'message': 'Feedback not found with feedback_id.',
            }
        return response_object, 404
    
    
""" ===============================<< Update Feedback ends >>=============================== """
""" ===============================<< Get Contractor List starts >>=============================== """
def getContractorList():
    try:
        contractor = AgencyJobPaymentClaim.query.with_entities(AgencyJobPaymentClaim.kontraktor).all()
        contractor_list = list(itertools.chain(*contractor))
        logger.info("Contractor List fetched")
        return contractor_list
    except:
        logger.exception("Contractor List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Contractor List could not be fetched"
        }
        
""" ===============================<< Get Contractor List ends >>=============================== """

""" ===============================<< Get Invoice starts >>=============================== """
def getInvoice(data):
    invoice_no = data.invoice_no
    contractor = data.contractor
    invoice_info = AgencyJobPaymentClaim.find_by_invoice_no(invoice_no)
    if AgencyJobPaymentClaim.find_by_invoice_no(invoice_no):
        if invoice_info.kontraktor == contractor:
            try:
                invoice_list = []
                for invoice in AgencyJobPaymentClaim.query.filter_by(no_inbois=invoice_no, active=1):
                    invoice_list.append({
                        'no_inbois': invoice.no_inbois,
                        'kontraktor': invoice.kontraktor,
                        'nama_pemohon': invoice.nama_pemohon,
                        'e_mei': invoice.e_mei,
                        'jumlah_tuntutan': invoice.jumlah_tuntutan,
                        'inbois_dokumen': invoice.inbois_dokumen,
                        'ringkasan_dokumen': invoice.ringkasan_dokumen,            
                        'lampiran': invoice.lampiran,                 
                        'status': invoice.status,            
                        'ulasan_pegawai': invoice.ulasan_pegawai,            
                        })
                logger.info("Invoice data fetched successfully")
                return jsonify(invoice_list)
            except:
                logger.exception("Invoice data could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': f'Invoice Details for Invoice no. {invoice_no} could not be be fetched',
                }
                return response_object, 404
        else:
            response_object = {
                    'status': 'fail',
                    'message': f'Invoice no. {invoice_no} and feedback {contractor} doesnot contains any infomation',
                }
            return response_object, 409
    else:
        response_object = {
                'status': 'fail',
                'message': f'No data containing Invoice no. {invoice_no} ',
            }
        return response_object, 404
    
"""===============================<< Get Invoice ends >>=============================== """
""" ===============================<< Create Invoice starts >>=============================== """

def createInvoice(data):
    invoice_no = data.invoice_no
    
    if db.session.query(AgencyJobPaymentClaim).filter_by(no_inbois=invoice_no).first():
        abort(HTTPStatus.CONFLICT, f"invoice no {invoice_no} is already registered", status="fail")
            
    feedback =  data.feedback
    applicant_name = data.applicant_name
    e_mei = data.e_mei
    amount_claim = data.amount_claim
    invoice_document = data.invoice_document
    if invoice_document:
        invoice_document = re.sub('[^a-zA-Z0-9.]', '', invoice_document)
        invoice_document = '/jkas_resourses/public/pdfs/'+invoice_document
    summary_document = data.summary_document
    if summary_document:
        summary_document = re.sub('[^a-zA-Z0-9.]', '', summary_document)
        summary_document = '/jkas_resourses/public/pdfs/'+summary_document
    attachment = data.attachment
    if attachment:
        attachment = re.sub('[^a-zA-Z0-9.]', '', attachment)
        attachment = '/jkas_resourses/public/pdfs/'+attachment
    today = date.today()
    
    try:
        new_claim = AgencyJobPaymentClaim(no_inbois=invoice_no,kontraktor=feedback,nama_pemohon=applicant_name,e_mei=e_mei,
                                          jumlah_tuntutan=amount_claim,inbois_dokumen=invoice_document,ringkasan_dokumen=summary_document,
                                          lampiran=attachment, tarikh=today, inserted_by = invoice_no, inserted_date = today, active=1)
        db.session.add(new_claim)
        db.session.commit()
        logger.info("Invoice added")
        response_object = {
            'status': 'success',
            'message': 'Invoice Added.',
        }
        return response_object, 201
    except:
        logger.exception("Invoice not added")
        response_object = {
            'status': 'fail',
            'message': 'Payment Claim not added.',
        }
        return response_object, 400

""" ===============================<< Create Invoice ends >>=============================== """
""" ===============================<< Update Invoice starts >>=============================== """

def updateInvoice(data):
    invoice_no = data.invoice_no
    feedback = data.feedback
    e_mei = data.e_mei
    amount_claim = data.amount_claim
    invoice_document = data.invoice_document
    summary_document = data.summary_document
    attachment = data.attachment
    status = data.status
    employee_review = data.employee_review
    today = date.today()
    invoice_details = db.session.query(AgencyJobPaymentClaim).filter_by(no_inbois=invoice_no, active=1).one()
    if invoice_details:
        try:
            invoice_details.no_inbois=invoice_no
            invoice_details.kontraktor=feedback
            invoice_details.e_mei=e_mei
            invoice_details.jumlah_tuntutan=amount_claim
           
            if invoice_document:
                invoice_document = re.sub('[^a-zA-Z0-9.]', '', invoice_document)
                invoice_details.inbois_dokumen='/jkas_resourses/public/pdfs/'+invoice_document
            else:
                invoice_details.inbois_dokumen=invoice_details.inbois_dokumen
            if summary_document:
                summary_document = re.sub('[^a-zA-Z0-9.]', '', summary_document)
                invoice_details.ringkasan_dokumen='/jkas_resourses/public/pdfs/'+summary_document
            else:
                invoice_details.ringkasan_dokumen=invoice_details.ringkasan_dokumen
            if attachment:
                attachment = re.sub('[^a-zA-Z0-9.]', '', attachment)
                invoice_details.lampiran='/jkas_resourses/public/pdfs/'+attachment
            else:
                invoice_details.lampiran=invoice_details.lampiran
            
            invoice_details.status=status
            invoice_details.ulasan_pegawai=employee_review
            invoice_details.updated_by = invoice_no
            invoice_details.updated_date = today
            db.session.commit()
            response_object = {
                'status': 'success',
                'message': 'Invoice updated',
            }
            logger.info("Invoice Updated")
            return response_object, 201
        except:
            logger.exception("Invoice could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'modified failed',
            }
            return response_object, 409
    else:
        response_object = {
                'status': 'fail',
                'message': 'Invoice not found with invoice_no.',
            }
        return response_object, 404

""" ===============================<< Update Invoice ends >>=============================== """
