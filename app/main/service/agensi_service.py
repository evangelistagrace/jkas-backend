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
import pytz
import requests
import itertools
import logging
from sqlalchemy import desc
from applogger import logger
from app.main import db
from .decorators import token_required
from app.main.models.models import (
    MasterUser, AgenciFeedback, JobPaymentClaim, Organisasi, LogPengguna, BlacklistedToken)
from app.main.util.datetime_util import (
    remaining_fromtimestamp,
    format_timespan_digits,
)

tz = pytz.timezone('Asia/Kuala_Lumpur')
# PRIVATE_PHOTO_FOLDER = os.environ.get('PRIVATE_PHOTO_FOLDER')
# PRIVATE_DOC_FOLDER = os.environ.get('PRIVATE_DOC_FOLDER')

""" ===============================<< get Agensi starts >>=============================== """
def getAgensi(np_number):
    np_number = np_number.upper()
    if db.session.query(MasterUser).filter_by(no_kad_pengenalan = np_number, active=1).first() == None:
        abort(HTTPStatus.CONFLICT, "invalid_agency_id", status="fail")
        
    user = db.session.query(MasterUser).filter_by(no_kad_pengenalan = np_number, active=1).first()
    if user.user_type == 'agenci' or user.user_type == 'SuperAdmin':
        try:
            access_token = user.encode_access_token()
            logger.info("Agensi Login Successfull")
            token=access_token.decode()
            
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            user_type = user.user_type
            role = user.role
            
            statement = "Log masuk berjaya"
            log_info = LogPengguna(id_pengguna=np_number, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit() 
            agensi_info = []
            for agensi in MasterUser.query.filter_by(no_kad_pengenalan=np_number, active=1):
                agensi_info.append({
                "no_kad_pengenalan":agensi.no_kad_pengenalan,
                "lokasi":agensi.lokasi,
                "nama_pegawai_merinyu":agensi.nama_pegawai_merinyu,
                "parlimen":agensi.parlimen,
                "status_tindakan":agensi.status_tindakan,
                "access_token": token,
                "expires_in": _get_token_expire_time(),
            })
            logger.info("Agensi fetched")
            return jsonify(agensi_info)
        except:
            logger.exception("Agensi could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'invalid_agency_id',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'invalid_agency_id',
        }
        return response_object, 404

def _get_token_expire_time():
    token_age_h = current_app.config.get("TOKEN_EXPIRE_HOURS")
    token_age_m = current_app.config.get("TOKEN_EXPIRE_MINUTES")
    expires_in_seconds = token_age_h * 3600 + token_age_m * 60
    return expires_in_seconds if not current_app.config["TESTING"] else 5

""" ===============================<< get Agensi ends >>=============================== """
""" ===============================<< Get Profile Information starts >>=============================== """
@token_required
def getProfileInformation():
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        user_type = user.user_type
        role = user.role
        email = user.alamat_emel
        log_list = []
        for logs in LogPengguna.query.filter_by(id_pengguna=id_card_no).order_by(desc(LogPengguna.tarikh)):
            log_list.append({
                'id_card_no': id_card_no,
                'role': role,
                'time': logs.tarikh,
                'action': logs.aktiviti,
            })
        logger.info("Profile Information fetched.")
        return jsonify(log_list)
    except:
        logger.exception("Profile Information could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Profile Information could not be fetched',
        }
        return response_object, 400

""" ===============================<< Get Profile Information ends >>=============================== """
""" ===============================<< Get Organisation List Starts >>=============================== """

def getOrganisationList():
    try:
        organisation = Organisasi.query.with_entities(Organisasi.organisasi).all()
        organisation_list = list(itertools.chain(*organisation))
        logger.info("Organisation List fetched")
        return organisation_list
    except:
        logger.exception("Organisation List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Organisation List could not be fetched"
        }
         
""" ===============================<< Get Organisation List Ends >>=============================== """   
""" ===============================<< Get User Information process starts >>=============================== """

@token_required
def get_logged_in_user():
    id = get_logged_in_user.id
    user = MasterUser.find_by_id(id)
    expires_at = get_logged_in_user.expires_at
    user.token_expires_in = format_timespan_digits(
        remaining_fromtimestamp(expires_at))
    return user

""" ===============================<< Get User Information process ends >>=============================== """
""" ===============================<< get Feedback List starts >>=============================== """
@token_required
def getFeedbackList():
    user = get_logged_in_user()
    np_number = user.no_kad_pengenalan
    if user.user_type == 'agenci':
        try:
            feedback_info = db.session.query(AgenciFeedback).filter_by(no_siri_notis_pemberitahuan=np_number, active=1).first()
        except:
            logger.exception("Feedback List not exist")
            response_object = {
                "status": "fail",
                "message": "feedback_not_exists"
            }
        if feedback_info: 
            
            try:
                feedback_list = []
                for feed in AgenciFeedback.query.filter_by(no_siri_notis_pemberitahuan=np_number, active=1):
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
                logger.exception("Feedback list not exist")
                response_object = {
                    'status': 'fail',
                    'message': 'feedback_not_exists',
                }
                return response_object, 400
        else:
            response_object = {
                "status": "fail",
                "message": "feedback_not_exists"
            }
            return response_object, 404
        
    if user.user_type == 'SuperAdmin':
        try:
            feedback_info = db.session.query(AgenciFeedback).first()
        except:
            logger.exception("Feedback List not exist")
            response_object = {
                "status": "fail",
                "message": "feedback_not_exists"
            }
        if feedback_info:
            try:
                feedback_list = []
                for feed in db.session.query(AgenciFeedback):
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
                logger.exception("Feedback list not exists")
                response_object = {
                    'status': 'fail',
                    'message': 'feedback_not_exists',
                }
                return response_object, 400
        else:
            response_object = {
                "status": "fail",
                "message": "feedback_not_exists"
            }
            return response_object, 404
        
""" ===============================<< get Feedback List ends >>=============================== """
""" ===============================<< Delete Feedback List starts >>===============================  """
@token_required
def deleteFeedbackList(data):
    feedback_id_list = data.feedback_id_list.split(",")
    try:
        user = get_logged_in_user()
        np_id = user.no_kad_pengenalan
        user_type = user.user_type
        role = user.role
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")    
        for i in feedback_id_list:
            if AgenciFeedback.query.filter_by(feedback_id=i).first():
                AgenciFeedback.query.filter_by(feedback_id=i).first().active = 0
                    
        db.session.commit()
        statement = f"Senarai maklum balas berjaya dipadamkan"
        log_info = LogPengguna(id_pengguna=np_id, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        logger.info("Feedback list Deleted successfully")
        
        response_object = {
            "status": "success",
            "message": "feedback_deleted"
        }
        return response_object, 200
    except:
        logger.exception("Feedback list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "feedback_not_exists"
        }
        return response_object, 400
            
""" ===============================<< Delete Feedback List ends >>===============================  """
""" ===============================<< get Feedback starts >>=============================== """
@token_required
def getFeedback(feedback_id):
    try:
        feedback_content = db.session.query(AgenciFeedback).filter_by(feedback_id=feedback_id, active=1).first()
    except:
        logger.exception("Feedback not exist")
        response_object = {
            'status': 'fail',
            'message': 'feedback_not_exists',
        }
        return response_object, 404
    if feedback_content:
        try:
            feedback_info = []
            for feed in AgenciFeedback.query.filter_by(feedback_id=feedback_id, active=1):
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
            logger.exception("Feedback not exists")
            response_object = {
                'status': 'fail',
                'message': 'feedback_not_exists',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'feedback_not_exists',
        }
        return response_object, 404
        
""" ===============================<< get Feedback ends >>=============================== """
""" ===============================<< Ceate Feedback starts >>=============================== """
@token_required
def createFeedback(data):
    np_number = data.np_number.upper()
    organization = data.organization
    merinyu_officer_name = data.merinyu_officer_name
    feedback = data.feedback
    picture_before = data.picture_before
    picture_after = data.picture_after
    notes = data.notes
    if picture_before:
        picture_before = re.sub('[^a-zA-Z0-9.]', '', picture_before)
        picture_before = picture_before
        before_date = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    else:
        before_date = None
        before_time = None
    if picture_after:
        picture_after = re.sub('[^a-zA-Z0-9.]', '', picture_after)
        after_date = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    else:
        after_date = None
        after_time = None
    user = get_logged_in_user()
    np_id = user.no_kad_pengenalan
    user_type = user.user_type
    role = user.role
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")  

    try:
          
        if MasterUser.find_by_id_card(np_number):
            new_feedback = AgenciFeedback(no_siri_notis_pemberitahuan=np_number, organisasi=organization, nama_pegawai_merinyu=merinyu_officer_name, maklum_balas=feedback,
                                        gambar_sebelum=picture_before, gambar_selepas=picture_after, sebelum_tarikh_masa=before_date,selepas_tarikh_masa=after_date,katatan=notes
                                        ,inserted_by=np_number,inserted_date=today, active=1)
            db.session.add(new_feedback)
            db.session.commit()

            statement = "Borang maklum balas berjaya dibuat."
            log_info = LogPengguna(id_pengguna=np_id, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            logger.info("Feedback Created Successfully")
            feedback_id = new_feedback.feedback_id
            response_object = {
                'status': 'success',
                'message': 'feedback_added',
                'feedback_id': f'{feedback_id}',
            }
            logger.info("Feedback Added")
            return response_object, 201
        else:
            logger.exception("feedback_not_added")
            response_object = {
                'status': 'fail',
                'message': f'No Agensi with NP id {np_number} found',
            }
        return response_object, 409 
    except:
        logger.exception("Feedback could not be added")
        response_object = {
            'status': 'fail',
            'message': 'feedback_not_added',
        }
        return response_object, 409
    
""" ===============================<< Create Feedback ends >>=============================== """
""" ===============================<< Get Last Feedback starts >>=============================== """
@token_required
def getLastFeedback():
    user = get_logged_in_user()
    no_kad_pengenalan = user.no_kad_pengenalan
    feedback_content = db.session.query(AgenciFeedback).filter_by(no_siri_notis_pemberitahuan=no_kad_pengenalan, active=1).first()
    if feedback_content != []:
        try:
            feedback_info = []
            feed_data = db.session.query(AgenciFeedback).filter_by(no_siri_notis_pemberitahuan=no_kad_pengenalan, active=1).order_by(AgenciFeedback.feedback_id.desc()).first()
            
            feedback_info.append({
            "feedback_id":feed_data.feedback_id,
            "no_siri_notis_pemberitahuan":feed_data.no_siri_notis_pemberitahuan,
            "organisasi":feed_data.organisasi,
            "nama_pegawai_merinyu":feed_data.nama_pegawai_merinyu,
            "maklum_balas":feed_data.maklum_balas,
            "gambar_sebelum":feed_data.gambar_sebelum, 
            "gambar_selepas":feed_data.gambar_selepas, 
            "sebelum_tarikh_masa": feed_data.sebelum_tarikh_masa, 
            "selepas_tarikh_masa": feed_data.selepas_tarikh_masa, 
            "gambar_laporan":feed_data.gambar_laporan,
            "laporan_tarikh_masa":feed_data.laporan_tarikh_masa,
            "kerja_selesail":feed_data.kerja_selesail,
            "katatan":feed_data.katatan,
            })
            logger.info("Feedbcak fetched")
            return jsonify(feedback_info)
        except:
            logger.exception("Feedback not exists")
            response_object = {
                'status': 'fail',
                'message': 'feedback_not_exists',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'feedback_not_exists',
        }
        return response_object, 404
    
""" ===============================<< Get Last Feedback ends >>=============================== """
""" ===============================<< Update Feedback starts >>=============================== """
@token_required
def updateFeedback(feedback_id,data):
    if db.session.query(AgenciFeedback).filter_by(feedback_id=feedback_id, active=1).first() == None:
        abort(HTTPStatus.CONFLICT, f"No Feedback found with feedback id {feedback_id}")
        
    feedback_details = db.session.query(AgenciFeedback).filter_by(feedback_id=feedback_id, active=1).first()
    try:                                          
        organization = data.organization
        merinyu_officer_name = data.merinyu_officer_name
        feedback = data.feedback
        picture_before = data.picture_before
        picture_after = data.picture_after
        report_image = data.report_image
        work_done_status = data.work_done_status
        user = get_logged_in_user()
        np_id = user.no_kad_pengenalan
        user_type = user.user_type
        role = user.role
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")  

        
        if picture_before:
            picture_before = re.sub('[^a-zA-Z0-9.]', '', picture_before)
            feedback_details.gambar_sebelum=picture_before
            feedback_details.sebelum_tarikh_masa = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        else:
            feedback_details.gambar_sebelum=feedback_details.gambar_sebelum
            feedback_details.sebelum_tarikh_masa = feedback_details.sebelum_tarikh_masa
        if picture_after:
            picture_after = re.sub('[^a-zA-Z0-9.]', '', picture_after)
            feedback_details.gambar_selepas=picture_after
            feedback_details.selepas_tarikh_masa = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        else:
            feedback_details.gambar_selepas=feedback_details.gambar_selepas
            feedback_details.selepas_tarikh_masa = feedback_details.selepas_tarikh_masa

        feedback_details.organisasi=organization
        feedback_details.nama_pegawai_merinyu=merinyu_officer_name
        feedback_details.maklum_balas=feedback            
        if report_image:
            report_image = re.sub('[^a-zA-Z0-9.]', '', report_image)
            feedback_details.gambar_laporan=report_image
            feedback_details.laporan_tarikh_masa = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        else:
            feedback_details.laporan_tarikh_masa = feedback_details.laporan_tarikh_masa
                
        feedback_details.kerja_selesail=work_done_status
        feedback_details.updated_by=np_id
        feedback_details.updated_date=today
        db.session.commit()
        
        statement = "Borang maklum balas berjaya dikemas kini."
        log_info = LogPengguna(id_pengguna=np_id, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        
        logger.info("Feedback Updated Successfully")

        response_object = {
            'status': 'success',
            'message': 'feedback_updated.',
        }
        return response_object, 201
    except:
        logger.exception("Feedback could not be updated")
        response_object = {
            'status': 'fail',
            'message': 'feedback_not_updated.',
        }
        return response_object, 409
    
""" ===============================<< Update Feedback ends >>=============================== """
""" ===============================<< Agensi logout process starts >>=============================== """

@token_required
def logout():
    access_token = logout.token
    expires_at = logout.expires_at
    blacklisted_token = BlacklistedToken(access_token, expires_at)
    db.session.add(blacklisted_token)
    db.session.commit()
    
    response_dict = dict(status="success", message="Successfully Logged Out")
    return response_dict, HTTPStatus.OK

""" ===============================<< Agensi logout process ends >>=============================== """
""" ===============================<< Get Contractor List starts >>=============================== """
def getContractorList():
    try:
        contractor = JobPaymentClaim.query.with_entities(JobPaymentClaim.kontraktor).distinct().all()
        contractor_list = list(itertools.chain(*contractor))
        contractor_list = sorted(contractor_list)
        contractor_list = contractor_list[::-1]
        logger.info("Contractor List fetched")
        return contractor_list
    except:
        logger.exception("Contractor List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Contractor List could not be fetched"
        }
        return response_object, HTTPStatus.BAD_REQUEST
        
""" ===============================<< Get Contractor List ends >>=============================== """

""" ===============================<< Get Invoice starts >>=============================== """
def getInvoice(data):
    invoice_no = data.invoice_no
    contractor = data.contractor
    invoice_info = JobPaymentClaim.find_by_invoice_no(invoice_no)
    if JobPaymentClaim.find_by_invoice_no(invoice_no):
        if invoice_info.kontraktor == contractor:
            try:
                invoice_list = []
                for invoice in JobPaymentClaim.query.filter_by(no_inbois=invoice_no, active=1):
                    invoice_list.append({
                        'id': invoice.id,
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
                    'message': 'invalid_invoice_id',
                }
                return response_object, 404
        else:
            response_object = {
                    'status': 'fail',
                    'message': 'invalid_invoice_id',
                }
            return response_object, 409
    else:
        response_object = {
                'status': 'fail',
                'message': 'invalid_invoice_id',
            }
        return response_object, 404
    
"""===============================<< Get Invoice ends >>=============================== """
""" ===============================<< Create Invoice starts >>=============================== """

def createInvoice(data):
    invoice_no = data.invoice_no
    
    if db.session.query(JobPaymentClaim).filter_by(no_inbois=invoice_no).first():
        abort(HTTPStatus.CONFLICT, "invoice_exists", status="fail")
            
    contractor =  data.contractor
    applicant_name = data.applicant_name
    e_mei = data.e_mei
    amount_claim = data.amount_claim
            
    invoice_document_temp = data.invoice_document
    if invoice_document_temp:
        invoice_document_list = invoice_document_temp.split(",")
        invoice_document_temp_list = []
        for i in invoice_document_list:
            invoice_document_temp = re.sub('[^a-zA-Z0-9.]', '', i)
            invoice_document_temp_list.append(invoice_document_temp)
        invoice_document_temp = ""
        for i in invoice_document_temp_list:
            invoice_document_temp += i+','
            
    summary_document_temp = data.summary_document
    if summary_document_temp:
        summary_document_list = summary_document_temp.split(",")
        summary_document_temp_list = []
        for i in summary_document_list:
            summary_document_temp = re.sub('[^a-zA-Z0-9.]', '', i)
            summary_document_temp_list.append(summary_document_temp)
        summary_document_temp = ""
        for i in summary_document_temp_list:
            summary_document_temp += i+','
            
    attachment_temp = data.attachment
    if attachment_temp:
        attachment_list = attachment_temp.split(",")
        attachment_temp_list = []
        for i in attachment_list:
            attachment_temp = re.sub('[^a-zA-Z0-9.]', '', i)
            attachment_temp_list.append(attachment_temp)
        attachment_temp = ""
        for i in attachment_temp_list:
            attachment_temp += i+','
            
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")  

    try:
        new_claim = JobPaymentClaim(no_inbois=invoice_no,kontraktor=contractor,nama_pemohon=applicant_name,e_mei=e_mei,
                                          jumlah_tuntutan=amount_claim,inbois_dokumen=invoice_document_temp[:-1],ringkasan_dokumen=summary_document_temp[:-1],
                                          lampiran=attachment_temp[:-1], tarikh=today, inserted_by = invoice_no, inserted_date = now, active=1)
        db.session.add(new_claim)
        db.session.commit()

        statement = "Tuntutan Pembayaran berjaya ditambahkan."
        log_info = LogPengguna(tarikh=now, aktiviti=statement)
        db.session.add(log_info)
        db.session.commit()
        logger.info("Payment Claim added")
        response_object = {
            'status': 'success',
            'message': 'payment_claim_added',
        }
        return response_object, 201
    except:
        logger.exception("Payment Claim could not be added")
        response_object = {
            'status': 'fail',
            'message': 'payment_claim_not_added',
        }
        return response_object, 400

""" ===============================<< Create Invoice ends >>=============================== """
""" ===============================<< Update Invoice starts >>=============================== """

def updateInvoice(data):
    invoice_no = data.invoice_no
    contractor = data.contractor
    applicant_name = data.applicant_name
    e_mei = data.e_mei
    amount_claim = data.amount_claim
    invoice_document = data.invoice_document
    summary_document = data.summary_document
    attachment = data.attachment
    status = data.status
    employee_review = data.employee_review

    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")  
    
    if db.session.query(JobPaymentClaim).filter_by(no_inbois=invoice_no, active=1).first() == None:
        abort(HTTPStatus.CONFLICT, "invalid_invoice_id", status="fail")
        
    invoice_details = db.session.query(JobPaymentClaim).filter_by(no_inbois=invoice_no, active=1).first()
    
    try:
        invoice_details.no_inbois=invoice_no
        invoice_details.kontraktor=contractor
        invoice_details.nama_pemohon=applicant_name
        invoice_details.e_mei=e_mei
        invoice_details.jumlah_tuntutan=amount_claim
    
        
        invoice_document_temp = data.invoice_document
        if invoice_document_temp:
            invoice_document_list = invoice_document_temp.split(",")
            invoice_document_temp_list = []
            for i in invoice_document_list:
                invoice_document_temp = re.sub('[^a-zA-Z0-9.]', '', i)
                invoice_document_temp_list.append(invoice_document_temp)
            invoice_document_temp = ""
            for i in invoice_document_temp_list:
                invoice_document_temp += i+','
            invoice_details.inbois_dokumen = invoice_document_temp[:-1]
        else:
            invoice_details.inbois_dokumen=""
                    
        summary_document_temp = data.summary_document
        if summary_document_temp:
            summary_document_list = summary_document_temp.split(",")
            summary_document_temp_list = []
            for i in summary_document_list:
                summary_document_temp = re.sub('[^a-zA-Z0-9.]', '', i)
                summary_document_temp_list.append(summary_document_temp)
            summary_document_temp = ""
            for i in summary_document_temp_list:
                summary_document_temp += i+','
            invoice_details.ringkasan_dokumen = summary_document_temp[:-1]
        else:
            invoice_details.ringkasan_dokumen=""
                    
        attachment_temp = data.attachment
        if attachment_temp:
            attachment_list = attachment_temp.split(",")
            attachment_temp_list = []
            for i in attachment_list:
                attachment_temp = re.sub('[^a-zA-Z0-9.]', '', i)
                attachment_temp_list.append(attachment_temp)
            attachment_temp = ""
            for i in attachment_temp_list:
                attachment_temp += i+','
            invoice_details.lampiran = attachment_temp[:-1]
        else:
            invoice_details.lampiran=""
        
        invoice_details.status=status
        invoice_details.ulasan_pegawai=employee_review
        invoice_details.updated_by = invoice_no
        invoice_details.updated_date = now
        db.session.commit()
        statement = "Tuntutan Pembayaran berjaya dikemas kini."
        log_info = LogPengguna(tarikh=now, aktiviti=statement)
        db.session.add(log_info)
        db.session.commit()
        logger.info("Payment Claim Updated")
        
        response_object = {
            'status': 'success',
            'message': 'payment_claim_updated',
        }
        return response_object, 201
    except:
        logger.exception("Payment Claim could not be updated")
        response_object = {
            'status': 'fail',
            'message': 'payment_claim_not_updated',
        }
        return response_object, 409
    
""" ===============================<< Update Invoice ends >>=============================== """
