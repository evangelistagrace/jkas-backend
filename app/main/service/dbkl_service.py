""" Business logic for /auth API endpoints."""
from http import HTTPStatus
import os, glob, json, sys, csv, psycopg2, re
import smtplib
from random import randint 
from flask import current_app, jsonify, session
from flask_restx import abort
from twilio.rest import Client
import requests
import itertools 
import logging
from sqlalchemy import and_, or_, not_, select
from datetime import date, time
from applogger import logger
from app.main import db
from .decorators import token_required
from app.main.models.token_blacklist import BlacklistedToken
from app.main.models.models import (
    MasterUser, PublicAnnouncement, PublicManual, PhotoGallery, PublicApplicationList, PublicApplicationDetails, MeetingArea, MeetingPdfPath, 
    PublicSiteVisitInfo, NonComplianceForm, SiteVisitPdfPath, PublicRating, AgensiFeedback, AgencyJobPaymentClaim, OmpBaru, DetailedMeeting,InventoriPengguna, 
    LogPengguna, OmpLama, OfficersList, CompoundInformation, ComplaintInvestigation, InquiryInformation, CompoundForm, Notice, GrafPrestasiBulanan, Coordinates, OtpStore,
    Log)
from app.main.util.datetime_util import (
    remaining_fromtimestamp,
    format_timespan_digits,
)
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.main.config import DevelopmentConfig
from applogger import logger
import pandas as pd

SMTP_MAIL = os.environ.get('SMTP_MAIL')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
FROM_TITLE = os.environ.get('FROM_TITLE')
FROM_EMAIL = os.environ.get('FROM_EMAIL')


""" ===============================<< Registration of new user starts >>==============================="""


def registerDbklUser(data):
    name = data.name
    nama_pengguna = data.nama_pengguna.upper()
    email = data.email
    password = data.password
    user_type = 'dbkl'

    if MasterUser.find_by_email(email):
        abort(HTTPStatus.CONFLICT,
              f"Email {email} is already registered", status="fail")
    if MasterUser.find_by_nama_pengguna(nama_pengguna):
            abort(HTTPStatus.CONFLICT,
                  f"Name {nama_pengguna} is already registered", status="fail")
    if MasterUser.find_by_nama(name):
            abort(HTTPStatus.CONFLICT,
                  f"Username {name} is already registered", status="fail")
    return register(name, nama_pengguna, email, password, user_type)


def register(name, nama_pengguna, email, password, user_type):

    randotp = randint(100000, 999999)
    session['randotp'] = randotp
    if OtpStore.find_by_nama_pengguna(nama_pengguna):
        OtpStore.query.filter(OtpStore.nama_pengguna == nama_pengguna).delete()
        db.session.commit()
    otp_list = [{"nama_pengguna": f"{nama_pengguna}", "otp": f"{randotp}", "name": f"{name}",  "email": f"{email}",  "psswd": f"{password}"}]
    for i in otp_list:
        db.session.add(OtpStore(**i))
    db.session.commit()
    TO_EMAIL = email
    message = MIMEMultipart()
    message['From'] = FROM_EMAIL
    message['To'] = TO_EMAIL
    message['Subject'] = FROM_TITLE
    MAIL_CONTENT = f"Please note down the 6 digit code - {randotp} for registration of user of name {nama_pengguna}"
    message.attach(MIMEText(MAIL_CONTENT, 'plain'))
    try:
        mail_session = smtplib.SMTP('smtp.gmail.com', 587)
        mail_session.starttls()
        mail_session.login(SMTP_MAIL, SMTP_PASSWORD)
        text = message.as_string()
        mail_session.sendmail(FROM_EMAIL, TO_EMAIL, text)
        mail_session.quit()
        logger.info("Mail Sent")
        response_object = {
            "status": "success",
            "message": "OTP sent successfully!"
        }
        return response_object
    except:
        logger.exception("Mail could not be sent")
        response_object = {
            "status": "fail",
            "message": f"Failed to sent mail to {email}"
        }
        return response_object, 400
 
def completeRegistration(data):
    user_otp = data.otp
    nama_pengguna = data.nama_pengguna
    user_type = 'dbkl'
    try:
        user = OtpStore.find_by_nama_pengguna(nama_pengguna)
        randotp = user.otp
    except:
        response_object = {
            'status': 'fail',
            'message': 'Wrong ID Card Number',
        }
        return response_object, 409
    
    if int(user_otp) == int(randotp):
        try:
            name = user.name
            email = user.email
            password = user.psswd
            updated_user = MasterUser(
                nama=name, no_kad_pengenalan=nama_pengguna, nama_pengguna=nama_pengguna, alamat_emel=email, password=password, user_type=user_type)
            db.session.add(updated_user)
            OtpStore.query.filter(OtpStore.nama_pengguna == nama_pengguna).delete()
            db.session.commit()
            logger.info("User Registered")
            response = {
                'status': 'success',
                'message': f'User {nama_pengguna} registered'
            }
            return response, 201
        except:
            logger.exception("User not registered")
            response_object = {
                'status': 'fail',
                'message': 'User not validated.',
            }
            return response_object, 409

    else:
        response_object = {
            'status': 'fail',
            'message': 'OTP not validated.',
        }
        return response_object, 409

""" ===============================<< Registration of new user ends >>=============================== """

""" ===============================<< User login process starts >>=============================== """


def login(data):
    nama_pengguna = data.nama_pengguna.upper()
    password = data.password
    user = MasterUser.find_by_nama_pengguna(nama_pengguna)
    if not user or not user.check_password(password):
        logger.debug("Invalid Credential")
        abort(HTTPStatus.UNAUTHORIZED,"Invalid credentials! Please try again.", status="fail")
    elif user.user_type == 'admin' or user.user_type=='dbkl':
        access_token = user.encode_access_token()
        logger.info("Login Successfull")
        user_type = user.user_type
        role = user.role
        return _create_auth_successful_response(
            token=access_token.decode(),
            status_code=HTTPStatus.OK,
            message="successfully logged in",
            user_type=user_type,
            role=role,
        )
        
    else:
        response_object = {
                'status': 'success',
                'message': f'User {nama_pengguna} cant sign in here',
        }
        return response_object, 403
        
def _create_auth_successful_response(token, status_code, message,user_type,role):
    response = jsonify(
        status="success",
        message=message,
        access_token=token,
        token_type="bearer",
        expires_in=_get_token_expire_time(),
        user_type=user_type,
        role=role,
    )
    response.status_code = status_code
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response

def _get_token_expire_time():
    token_age_h = current_app.config.get("TOKEN_EXPIRE_HOURS")
    token_age_m = current_app.config.get("TOKEN_EXPIRE_MINUTES")
    expires_in_seconds = token_age_h * 10800 + token_age_m * 60
    return expires_in_seconds if not current_app.config["TESTING"] else 5

""" ===============================<< User login process ends >>=============================== """
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
""" ===============================<< User logout process starts >>=============================== """

@token_required
def logout():
    email = session.get('user_email')
    access_token = logout.token
    expires_at = logout.expires_at
    blacklisted_token = BlacklistedToken(access_token, expires_at)
    db.session.add(blacklisted_token)
    db.session.commit()
    if email:
        del session['user_email']
    response_dict = dict(status="success", message="successfully logged out")
    return response_dict, HTTPStatus.OK


def _get_token_expire_time():
    token_age_h = current_app.config.get("TOKEN_EXPIRE_HOURS")
    token_age_m = current_app.config.get("TOKEN_EXPIRE_MINUTES")
    expires_in_seconds = token_age_h * 3600 + token_age_m * 60
    return expires_in_seconds if not current_app.config["TESTING"] else 5

""" ===============================<< User logout process ends >>=============================== """
""" ===============================<< Role Assign Starts >>=============================== """

@token_required
def assignRole(data):
    no_kad_pengenalan = data.id_card_number
    role = data.role
    user = get_logged_in_user()
    if user.user_type == 'admin':
        try:
            exists = db.session.query(MasterUser).filter_by(no_kad_pengenalan=no_kad_pengenalan, user_type='dbkl')
            if exists:
                master_user_obj = MasterUser.query.filter_by(no_kad_pengenalan=no_kad_pengenalan).first()
                master_user_obj.role = role
                db.session.commit()
                logger.info("Role assigned")
                response_object = {
                    'status': 'success',
                    'message': 'Role assigned',
                }
                return response_object, 201

            else:
                response_object = {
                    'status': 'fail',
                    'message': 'nama pengguna not exists. Role not assigned.',
                }
                return response_object, 409
        except:
            logger.exception("Role not assigned.")
            response_object = {
                'status': 'fail',
                'message': 'Role not assigned.',
            }
            return response_object, 409
    else:
        logger.debug("user dont have permission to assign role")
        response_object = {
            'status': 'fail',
            'message': 'user dont have permission to assign role',
            }
        return response_object, 400 


""" ===============================<< Role Assign Ends >>=============================== """ 
""" ===============================<< Update Meeting Starts >>=============================== """
@token_required
def updateMeeting(no_siri_permohonan,data):
    tarikh=data.tarikh
    masa=data.masa
    tempat=data.tempat
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        exists = db.session.query(MeetingArea).filter_by(no_siri_permohonan=no_siri_permohonan).first() is not None
        if exists:
            meeting_area_obj = MeetingArea.query.filter_by(no_siri_permohonan=no_siri_permohonan, active=1).first()
            meeting_area_obj.tarikh = tarikh
            meeting_area_obj.masa = masa
            meeting_area_obj.tempat = tempat
            meeting_area_obj.updated_date = today
            meeting_area_obj.updated_by = id_card_no
            db.session.commit()

            statement = "Meeting for "+no_siri_permohonan+" updated successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Meeting Form Updated")
            response_object = {
                'status': 'success',
                'message': 'Meeting Form Updated.',
            }
            return response_object, 201
        else:
            new_meeting = MeetingArea(no_siri_permohonan=no_siri_permohonan,tarikh=tarikh,masa=masa,tempat=tempat,inserted_date=today,inserted_by=id_card_no,active=1)
            db.session.add(new_meeting)
            db.session.commit()

            statement = "New meeting for "+no_siri_permohonan+" is added successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            logger.info("new meeting added successfully")
            response = {
                'status':'success',
                'message':'new meeting added successfully'
            }
            return response, 201
        
    except:
        logger.exception("meeting not updated.")
        response = {
            'status':'fail',
            'message':'meeting not updated.'
        }
        return response, 409

""" ===============================<< Update Meeting Ends >>=============================== """
""" ===============================<< List Of Meeting Starts >>=============================== """

@token_required
def listOfMeeting(): 
    try:
        meeting_obj = MeetingArea.query.filter_by(active=1).all()
        results=[]
        for meeting_details in meeting_obj:
            results.append({
                "meeting_id" : meeting_details.meeting_id,
                "no_siri_permohonan" : meeting_details.no_siri_permohonan,
                "tarikh_mesyuarat" : meeting_details.tarikh,
                "masa_mesyuarat" : meeting_details.masa,
                "tempat_mesyuarat" : meeting_details.tempat
            })
        logger.info("list of meeting fetched")
        return jsonify(results)
    except:
        logger.exception("list of meeting not fetched")
        response_object = {
            'status':'fail',
            'message':'list of meeting not fetched'
        }
        return response_object, 409
""" ===============================<< List Of Detailed Meeting Ends >>=============================== """
""" ===============================<< Get Meeting Starts >>=============================== """
@token_required
def getMeeting(meeting_id): 
    try:
        meeting_info = MeetingArea.query.filter_by(meeting_id=meeting_id, active=1).first()
    except:
        logger.exception('No Meeting Information Found with meeting_id')
        response_object = {
                'status': 'fail',
                'message': f'No Meeting Information Found with meeting_id {meeting_id}',
            }
        return response_object, 404
    if meeting_info:
        try:
            meeting_info=[]
            for meeting_details in MeetingArea.query.filter_by(meeting_id=meeting_id, active=1):
                meeting_info.append({
                    "meeting_id" : meeting_details.meeting_id,
                    "no_siri_permohonan" : meeting_details.no_siri_permohonan,
                    "tarikh_mesyuarat" : meeting_details.tarikh,
                    "masa_mesyuarat" : meeting_details.masa,
                    "tempat_mesyuarat" : meeting_details.tempat
                })
            logger.info("Meeting fetched")
            return jsonify(meeting_info)
        except:
            logger.exception("Meeting not fetched")
            response_object = {
                'status':'fail',
                'message':'Meeting not fetched'
            }
            return response_object, 409
    else:
        response_object = {
            'status': 'fail',
            'message': f'No Meeting Information Found with meeting_id {meeting_id}',
        }
        return response_object, 404
    
""" ===============================<< Get Meeting Ends >>=============================== """
""" ===============================<< Delete List Of Meeting Starts >>=============================== """

@token_required
def deleteListOfMeeting(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    meeting_id_list = data.meeting_id_list.split(",")
    try:
        if user.user_type == 'dbkl':
            for i in meeting_id_list:
                if MeetingArea.query.filter_by(id=i).first():
                    MeetingArea.query.filter_by(id=i).first().active = 0
                
            db.session.commit()
            
            statement = "List of meeting form deleted successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Meeting id list Deleted successfully")

            response_object = {
                "status": "success",
                "message": "Meeting id list Deleted successfully."
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "User is not dbkl."
            } 

    except:
        logger.exception("Meeting id list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Meeting id list could not be Deleted."
        }
        return response_object, 400

""" ===============================<< Delete List Of Meeting Ends >>=============================== """
""" ===============================<< Add Detailed Meeting Starts >>=============================== """
@token_required
def addDetailedMeeting(kategori_mesyuarat,kekerapan_mesyuarat,jenis_mesyuarat,jabatan_terlibat,tarikh_mesyuarat,masa_mesyuarat,hingga,pengerusi,bill_mesyuarat,
                        tajuk_mesyuarat,setiausaha,tempat_mesyuarat,agenda_dan_minit):
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        newDetailedMeeting = DetailedMeeting(kategori_mesyuarat=kategori_mesyuarat,kekerapan_mesyuarat=kekerapan_mesyuarat,
                                            jenis_mesyuarat=jenis_mesyuarat,jabatan_terlibat=jabatan_terlibat,tarikh_mesyuarat=tarikh_mesyuarat,
                                            masa_mesyuarat=masa_mesyuarat,hingga=hingga,pengerusi=pengerusi,bill_mesyuarat=bill_mesyuarat,
                                            tajuk_mesyuarat=tajuk_mesyuarat,setiausaha=setiausaha,tempat_mesyuarat=tempat_mesyuarat,agenda_dan_minit=agenda_dan_minit,
                                            active=1)
        db.session.add(newDetailedMeeting)
        db.session.commit()
        
        statement = "New detailed meeting form added successfully by "+id_card_no
        log_info = Log(statement=statement,date=today,user_name=id_card_no)
        db.session.add(log_info)
        db.session.commit()

        response_object = {
            'status':'success',
            'message':'Detailed Meeting Form Added. Database updated successfully'
        }
        logger.info("Detailed Meeting Form Added.")
        return response_object, 201
    except:
        logger.exception("Detailed Meeting Form Not Added.")
        response_object = {
            'status':'fail',
            'message':'Detailed Meeting Form Not Added.'
        }
        return response_object, 409

""" ===============================<< Add Detailed Meeting Ends >>=============================== """
""" ===============================<< List Of Detailed Meeting Starts >>=============================== """
@token_required
def listOfDetailedMeeting(): 
    try:
        meeting_info=[]
        for meeting_details in DetailedMeeting.query.filter_by(active=1):
            meeting_info.append({
                "tajuk_mesyuarat" : meeting_details.tajuk_mesyuarat,
                "jenis_mesyuarat" : meeting_details.jenis_mesyuarat,
                "jawatankuasa_mesurat" : "",
                "tarikh_mesyuarat" : meeting_details.tarikh_mesyuarat,
                "hingga" : meeting_details.hingga
            })
        logger.info("list of detailed meeting fetched")
        return jsonify(meeting_info)
    except:
        logger.exception("list of detailed meeting not fetched")
        response_object = {
            'status':'fail',
            'message':'list of detailed meeting not fetched'
        }
        return response_object, 409
""" ===============================<< List Of Detailed Meeting Ends >>=============================== """
""" ===============================<< Update Detailed Meeting Starts >>=============================== """
@token_required
def updateDetailedMeeting(detailed_meeting_id,kategori_mesyuarat,kekerapan_mesyuarat,jenis_mesyuarat,jabatan_terlibat,tarikh_mesyuarat,masa_mesyuarat,hingga,pengerusi,bill_mesyuarat,tajuk_mesyuarat,setiausaha,tempat_mesyuarat,agenda_dan_minit):
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        exists = db.session.query(DetailedMeeting).filter_by(detailed_meeting_id=detailed_meeting_id, active=1)
        if exists:
            detailed_meeting_area_obj = DetailedMeeting.query.filter_by(detailed_meeting_id=detailed_meeting_id, active=1).first()
            detailed_meeting_area_obj.kategori_mesyuarat = kategori_mesyuarat
            detailed_meeting_area_obj.kekerapan_mesyuarat = kekerapan_mesyuarat
            detailed_meeting_area_obj.jenis_mesyuarat = jenis_mesyuarat
            detailed_meeting_area_obj.jabatan_terlibat = jabatan_terlibat
            detailed_meeting_area_obj.tarikh_mesyuarat = tarikh_mesyuarat
            detailed_meeting_area_obj.masa_mesyuarat = masa_mesyuarat
            detailed_meeting_area_obj.hingga = hingga
            detailed_meeting_area_obj.pengerusi = pengerusi
            detailed_meeting_area_obj.bill_mesyuarat = bill_mesyuarat
            detailed_meeting_area_obj.tajuk_mesyuarat = tajuk_mesyuarat
            detailed_meeting_area_obj.setiausaha = setiausaha
            detailed_meeting_area_obj.tempat_mesyuarat = tempat_mesyuarat
            detailed_meeting_area_obj.agenda_dan_minit = agenda_dan_minit
            db.session.commit()
            
            statement = "Detailed meeting form updated successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'Detailed Meeting Form Updated.',
            }
            logger.info("Detailed Meeting Form Updated")
            return response_object, 201
    except:
        logger.exception("Detailed Meeting Form not Updated")
        response_object = {
            'status':'fail',
            'message':'Detailed Meeting Form not Updated'
        }
        return response_object, 409
""" ===============================<< Update Detailed Meeting Ends >>=============================== """
""" ===============================<< Get Inventori Pengguna Starts >>=============================== """
@token_required
def getInventoriPengguna():
    try:
        inventori_pengguna_res=[]
        for inventori_pengguna in InventoriPengguna.query.filter_by(active=1):
            inventori_pengguna_res.append({
                "nama_pengguna" : inventori_pengguna.nama_pengguna,
                "id_pengguna" : inventori_pengguna.id_pengguna,
                "kata_laluan" : inventori_pengguna.kata_laluan,
                "peranan" : inventori_pengguna.peranan,
            })
        logger.info("inventori pengguna fetched")
        return inventori_pengguna_res
    except:
        logger.exception("inventori pengguna not fetched")
        response_object = {
            'status':'fail',
            'message':'inventori pengguna not fetched'
        }
        return response_object, 409
""" ===============================<< Get Inventori Pengguna Ends >>=============================== """
""" ===============================<< Delete Inventori Pengguna Starts >>=============================== """

@token_required
def deleteInventoriPengguna(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    id_pengguna_list = data.id_pengguna_list.split(",")
    try:
        if user.user_type == 'dbkl':
            for i in id_pengguna_list:
                if InventoriPengguna.query.filter_by(inventori_pengguna_id=i).first():
                    InventoriPengguna.query.filter_by(inventori_pengguna_id=i).first().active = 0

                if LogPengguna.query.filter_by(id_pengguna=i).first():
                    LogPengguna.query.filter_by(id_pengguna=i).first().active = 0
                
            db.session.commit()
            
            statement = "List of inventori pengguna deleted successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Inventori Pengguna list Deleted successfully")

            response_object = {
                "status": "success",
                "message": "Inventori Pengguna liST Deleted successfully."
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "User is not dbkl."
            } 

    except:
        logger.exception("Inventori Pengguna list and Log Pengguna list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Inventori Pengguna list and Log Pengguna list could not be Deleted."
        }
        return response_object, 400

""" ===============================<< Delete Inventori Pengguna Ends >>=============================== """   
""" ===============================<< Get Log Pengguna Starts >>=============================== """
@token_required
def getLogPengguna():
    try:
        log_pengguna_obj = LogPengguna.query.filter_by(active=1).all()
        log_pengguna_res=[]
        for log_pengguna in log_pengguna_obj:
            log_pengguna_res.append({
                "id_pengguna" : log_pengguna.id_pengguna,
                "tarikh" : log_pengguna.tarikh,
                "masa_masuk" : log_pengguna.masa_masuk,
                "masa_keluar" : log_pengguna.masa_keluar,
                "aktiviti" : log_pengguna.aktiviti,
            })
        logger.info("log pengguna fetched")
        return jsonify(log_pengguna_res)
    except:
        logger.exception("log pengguna not fetched")
        response_object = {
            'status':'fail',
            'message':'log pengguna not fetched'
        }
        return response_object, 409
""" ===============================<< Get Log Pengguna Ends >>=============================== """
""" ===============================<< Update Inventori Pengguna Starts >>=============================== """ 
@token_required
def updateInventoriPengguna(id_pengguna,data):
    nama_pengguna=data.nama_pengguna
    kata_laluan=data.kata_laluan
    peranan=data.peranan
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        exists = db.session.query(InventoriPengguna).filter_by(inventori_pengguna_id=id_pengguna, active=1)
        if exists:
            inventori_pengguna_obj = InventoriPengguna.query.filter_by(inventori_pengguna_id=id_pengguna, active=1).first()
            inventori_pengguna_obj.nama_pengguna = nama_pengguna
            inventori_pengguna_obj.kata_laluan = kata_laluan
            inventori_pengguna_obj.peranan = peranan
            inventori_pengguna_obj.updated_date = today
            inventori_pengguna_obj.updated_by = id_card_no
            db.session.commit()
            
            statement = "Inventori pengguna "+id_pengguna+" updated successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            response_object = {
                'status':'success',
                'message':'inventori pengguna updated successfully.'
            }
            logger.info("inventori pengguna updated.")
            return response_object, 201
    except:
        logger.exception("inventori pengguna not updated.")
        response_object = {
            'status':'fail',
            'message':'inventori pengguna not updated.'
        }
        return response_object, 409


""" ===============================<< Update Inventori Pengguna Ends >>=============================== """ 
""" ===============================<< Get Public Application List Starts >>=============================== """  
@token_required
def getPublicApplicationList():
    try:    
        application_list_obj = PublicApplicationList.query.all()
        application_list_res = []
        for publicApplication in application_list_obj:
                
            application_list_res.append({
                "no_siri_permohonan": publicApplication.no_siri_permohonan,
                "tarikh_permohonan" : publicApplication.tarikh_permohonan,
                "dokumen_senarai"   : publicApplication.dokumen_senarai,
                "status_semakan_dokumen":publicApplication.status_semakan_dokumen, 
                "surat_penyerahan_kawasan" : publicApplication.surat_penyerahan_kawasan,
            })
        logger.info("public application list fetched")            
        return jsonify(application_list_res)
    except:
        logger.exception("public application list not fetched")
        response_object = {
            'status':'fail',
            'message':'public application list not fetched.'
        }
        return response_object, 409


""" ===============================<< Get Public Application List Ends >>=============================== """
""" ===============================<< Update Public Application Status Details Starts >>=============================== """
@token_required
def updatePublicApplicationDetails(no_siri_permohonan,data):
    kutipan_sampah=data.kutipan_sampah
    sapuan_jalan=data.sapuan_jalan
    cucian_longkang=data.cucian_longkang
    pemotongan_rumput=data.pemotongan_rumput
    dinyatakan_nama_bangunan=data.dinyatakan_nama_bangunan
    strata_title=data.strata_title
    hak_milik_kekal=data.hak_milik_kekal
    nama_jalan=data.nama_jalan
    panjang_jalan_mengikut_nama_jalan=data.panjang_jalan_mengikut_nama_jalan
    panjang_longkang=data.panjang_longkang
    luas_kawasan_berumput=data.luas_kawasan_berumput
    luas_kawasan_TPKK=data.luas_kawasan_TPKK
    parkir_area=data.parkir_area
    surat_permohonan_perkhidmatan_pembersihan_dokumen = data.surat_permohonan_perkhidmatan_pembersihan_dokumen
    surat_salinan_CF_dokumen = data.surat_salinan_CF_dokumen
    salinan_status_pembanginan_dokumen = data.salinan_status_pembanginan_dokumen
    bagi_status_pembangunan_dokumen = data.bagi_status_pembangunan_dokumen
    surat_permohonan_perkhidmatan_pembersihan_status=data.surat_permohonan_perkhidmatan_pembersihan_status
    surat_salinan_CF_status=data.surat_salinan_CF_status
    salinan_status_pembanginan_status=data.salinan_status_pembanginan_status
    bagi_status_pembangunan_status=data.bagi_status_pembangunan_status
    
    try:
        app_details = db.session.query(PublicApplicationDetails).filter_by(no_siri_permohonan=no_siri_permohonan, active=1).first() 
    except:
        logger.exception('Public application Info not found with no siri permohonan')
        response_object = {
                'status': 'fail',
                'message': 'Public application Info not found with no siri permohonan',
            }
        return response_object, 404
    if app_details:
        try:
            user = get_logged_in_user()
            id_card_no = user.no_kad_pengenalan
            today = date.today()

            app_details.kutipan_sampah = kutipan_sampah
            app_details.sapuan_jalan = sapuan_jalan
            app_details.cucian_longkang = cucian_longkang
            app_details.pemotongan_rumput = pemotongan_rumput
            app_details.dinyatakan_nama_bangunan = dinyatakan_nama_bangunan
            app_details.strata_title = strata_title
            app_details.hak_milik_kekal = hak_milik_kekal
            app_details.nama_jalan = nama_jalan
            app_details.panjang_jalan_mengikut_nama_jalan = panjang_jalan_mengikut_nama_jalan
            app_details.panjang_longkang = panjang_longkang
            app_details.luas_kawasan_berumput = luas_kawasan_berumput
            app_details.luas_kawasan_TPKK = luas_kawasan_TPKK
            app_details.parkir_area = parkir_area
            if surat_permohonan_perkhidmatan_pembersihan_dokumen:
                surat_permohonan_perkhidmatan_pembersihan_dokumen = re.sub('[^a-zA-Z0-9.]', '', surat_permohonan_perkhidmatan_pembersihan_dokumen)
                app_details.surat_permohonan_perkhidmatan_pembersihan_dokumen = '/jkas_resourses/public/pdfs/'+surat_permohonan_perkhidmatan_pembersihan_dokumen
            else:
                app_details.surat_permohonan_perkhidmatan_pembersihan_dokumen = app_details.surat_permohonan_perkhidmatan_pembersihan_dokumen
            if surat_salinan_CF_dokumen:
                surat_salinan_CF_dokumen = re.sub('[^a-zA-Z0-9.]', '', surat_salinan_CF_dokumen)
                app_details.surat_salinan_CF_dokumen = '/jkas_resourses/public/pdfs/'+surat_salinan_CF_dokumen
            else:
                app_details.surat_salinan_CF_dokumen = app_details.surat_salinan_CF_dokumen
            if salinan_status_pembanginan_dokumen:
                salinan_status_pembanginan_dokumen = re.sub('[^a-zA-Z0-9.]', '', salinan_status_pembanginan_dokumen)
                app_details.salinan_status_pembanginan_dokumen = '/jkas_resourses/public/pdfs/'+salinan_status_pembanginan_dokumen
            else:
                app_details.salinan_status_pembanginan_dokumen = app_details.salinan_status_pembanginan_dokumen
            if bagi_status_pembangunan_dokumen:
                bagi_status_pembangunan_dokumen = re.sub('[^a-zA-Z0-9.]', '', bagi_status_pembangunan_dokumen)
                app_details.bagi_status_pembangunan_dokumen = '/jkas_resourses/public/pdfs/'+bagi_status_pembangunan_dokumen
            else:
                app_details.bagi_status_pembangunan_dokumen = app_details.bagi_status_pembangunan_dokumen
            app_details.surat_permohonan_perkhidmatan_pembersihan_status = surat_permohonan_perkhidmatan_pembersihan_status
            app_details.surat_salinan_CF_status = surat_salinan_CF_status
            app_details.salinan_status_pembanginan_status = salinan_status_pembanginan_status
            app_details.bagi_status_pembangunan_status = bagi_status_pembangunan_status
            if surat_permohonan_perkhidmatan_pembersihan_status is 1 and surat_permohonan_perkhidmatan_pembersihan_status is 1 and salinan_status_pembanginan_status is 1 and bagi_status_pembangunan_status is 1:
                app_details.status_dokumen_keseluruhan = 1
            else:
                app_details.status_dokumen_keseluruhan = 0
            db.session.commit()
            
            statement = "public application "+no_siri_permohonan+" updated successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            logger.info("public application updated successfully.")
            response_object = {
                'status':'success',
                'message':'public application updated successfully.'
            }
            return response_object, 201
        except:
            logger.exception("public application not updated ")
            response_object = {
                'status':'fail',
                'message':'public application not updated .'
            }
            return response_object, 409
    else:
        response_object = {
                'status': 'fail',
                'message': 'Public application Info not found with no siri permohonan',
            }
        return response_object, 404
 
""" ===============================<< Update Public Application Details Ends >>=============================== """
""" ===============================<< Delete Public Application List Starts >>=============================== """

@token_required
def deletePublicApplicationList(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    no_siri_permohonan_list = data.no_siri_permohonan_list.split(",")
    try:
        if user.user_type == 'dbkl':
            for i in no_siri_permohonan_list:
                
                if PublicApplicationList.query.filter_by(no_siri_permohonan=i).first():
                    PublicApplicationList.query.filter_by(no_siri_permohonan=i).first().active = 0

                if PublicApplicationDetails.query.filter_by(no_siri_permohonan=i).first():
                    PublicApplicationDetails.query.filter_by(no_siri_permohonan=i).first().active = 0

                if MeetingArea.query.filter_by(no_siri_permohonan=i).first():
                    MeetingArea.query.filter_by(no_siri_permohonan=i).first().active = 0

                if MeetingPdfPath.query.filter_by(no_siri_permohonan=i).first():
                    MeetingPdfPath.query.filter_by(no_siri_permohonan=i).first().active = 0

                if PublicSiteVisitInfo.query.filter_by(no_siri_permohonan=i).first():
                    PublicSiteVisitInfo.query.filter_by(no_siri_permohonan=i).first().active = 0
                    
                if NonComplianceForm.query.filter_by(no_siri_permohonan=i).first():
                    NonComplianceForm.query.filter_by(no_siri_permohonan=i).first().active = 0

            db.session.commit()
            
            statement = "Public application list deleted successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Public Application List Deleted successfully")

            response_object = {
                "status": "success",
                "message": "Public Application List Deleted successfully."
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "User is not dbkl."
            } 

    except:

        logger.exception("Public Application List could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Public Application List could not be Deleted."
        }
        return response_object, 400

""" ===============================<< Delete Public Application List Ends >>=============================== """
""" ===============================<< Fetch Public Application Status Details Starts >>=============================== """
@token_required
def fetchPublicApplicationDetails(no_siri_permohonan):
    if PublicApplicationDetails.find_by_app_srl_no(no_siri_permohonan):
        try:
            app_list = []
            for app in PublicApplicationDetails.query.filter_by(no_siri_permohonan=no_siri_permohonan, active=1):
                app_list.append({
                    "kutipan_sampah" : app.kutipan_sampah, 
                    "sapuan_jalan" : app.sapuan_jalan, 
                    "cucian_longkang" : app.cucian_longkang, 
                    "pemotongan_rumput" : app.pemotongan_rumput, 
                    "dinyatakan_nama_bangunan" : app.dinyatakan_nama_bangunan, 
                    "strata_title" : app.strata_title, 
                    "hak_milik_kekal" : app.hak_milik_kekal, 
                    "nama_jalan" : app.nama_jalan, 
                    "panjang_jalan_mengikut_nama_jalan" : app.panjang_jalan_mengikut_nama_jalan, 
                    "panjang_longkang" : app.panjang_longkang, 
                    "luas_kawasan_berumput" : app.luas_kawasan_berumput, 
                    "luas_kawasan_TPKK" : app.luas_kawasan_TPKK, 
                    "parkir_area" : app.parkir_area, 
                    "surat_permohonan_perkhidmatan_pembersihan_dokumen" : app.surat_permohonan_perkhidmatan_pembersihan_dokumen, 
                    "surat_salinan_CF_dokumen" : app.surat_salinan_CF_dokumen, 
                    "salinan_status_pembanginan_dokumen" : app.salinan_status_pembanginan_dokumen, 
                    "bagi_status_pembangunan_dokumen" : app.bagi_status_pembangunan_dokumen, 
                    "surat_permohonan_perkhidmatan_pembersihan_status" : app.surat_permohonan_perkhidmatan_pembersihan_status, 
                    "surat_salinan_CF_status" : app.surat_salinan_CF_status, 
                    "salinan_status_pembanginan_status" : app.salinan_status_pembanginan_status, 
                    "bagi_status_pembangunan_status" : app.bagi_status_pembangunan_status, 
                    "status_dokumen_keseluruhan" : app.status_dokumen_keseluruhan, 
                    })
            logger.info("Application List Fetched")
            return jsonify(app_list)
        except:
            logger.exception("Application List not fetched")
            response_object = {
                'status': 'fail',
                'message': f'Serial No. {no_siri_permohonan} is not found in Database',
            }
            return response_object, 404
    else:
        response_object = {
                'status': 'fail',
                'message': f'Serial No. {no_siri_permohonan} is not found in Database',
            }
        return response_object, 404
   
""" ===============================<< Fetch Public Application Status Details Ends >>=============================== """
""" ===============================<< update Status Semakan Dokumen Starts >>=============================== """
@token_required
def updateStatusSemakanDokumen(no_siri_permohonan,data):
    status_semakan_dokumen=data.status_semakan_dokumen
    surat_penyerahan_kawasan = data.surat_penyerahan_kawasan
    
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    try:
        public_application_list_obj = PublicApplicationList.query.filter_by(no_siri_permohonan=no_siri_permohonan, active=1).first()
        
        public_application_list_obj.status_semakan_dokumen = status_semakan_dokumen
        public_application_list_obj.updated_date = today
        public_application_list_obj.updated_by = id_card_no
        
        if surat_penyerahan_kawasan:
            surat_penyerahan_kawasan = re.sub('[^a-zA-Z0-9.]', '', surat_penyerahan_kawasan)
            public_application_list_obj.surat_penyerahan_kawasan  = '/jkas_resourses/public/pdfs/'+surat_penyerahan_kawasan
        else:
            public_application_list_obj.surat_penyerahan_kawasan = public_application_list_obj.surat_penyerahan_kawasan
        db.session.commit()

        public_application_obj = PublicApplicationDetails.query.filter_by(no_siri_permohonan=no_siri_permohonan).first()
        public_application_obj.status_dokumen_keseluruhan = status_semakan_dokumen
        public_application_obj.updated_date = today
        public_application_obj.updated_by = id_card_no
        db.session.commit()
        statement = "Status semakan dokumen of "+no_siri_permohonan+" updated successfully by "+id_card_no
        log_info = Log(statement=statement,date=today,user_name=id_card_no)
        db.session.add(log_info)
        db.session.commit()


        logger.info("status semakan dokumen updated successfully.")
        response_object = {
            'status':'success',
            'message':'status semakan dokumen updated successfully.'
        }
        return response_object, 201
    except:
        logger.exception("status semakan dokumen not updated")
        response_object = {
            'status':'fail',
            'message':'status semakan dokumen not updated .'
        }
        return response_object, 409

""" ===============================<< update Status Semakan Dokumen Ends >>=============================== """
""" ===============================<< update site visit application list starts >>=============================== """
@token_required
def updateSiteVisitApplicationList(site_id,data):
    tarikh=data.tarikh
    lawatan_tapak=data.lawatan_tapak
    tarikh_lawatan_tapak=data.tarikh_lawatan_tapak
    keputusan_lawatan_tapak=data.keputusan_lawatan_tapak
    makalumat_ketidakpatuhan=data.makalumat_ketidakpatuhan
    maklum_balas_ketidakpatuhan=data.maklum_balas_ketidakpatuhan
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
           
    try:
        exists = db.session.query(PublicSiteVisitInfo).filter_by(site_id=site_id, active=1)
    except:
        logger.exception('Site Visit Information could not be found')
        response_object = {
                'status': 'fail',
                'message': 'Site Visit Information could not be found',
            }
        return response_object, 404
    if exists:
        try:
            sitevisit_info_obj = PublicSiteVisitInfo.query.filter_by(site_id=site_id, active=1).first()
            sitevisit_info_obj.tarikh = tarikh
            sitevisit_info_obj.lawatan_tapak = lawatan_tapak
            sitevisit_info_obj.tarikh_lawatan_tapak = tarikh_lawatan_tapak
            sitevisit_info_obj.keputusan_lawatan_tapak = keputusan_lawatan_tapak
            sitevisit_info_obj.makalumat_ketidakpatuhan = makalumat_ketidakpatuhan
            sitevisit_info_obj.maklum_balas_ketidakpatuhan = maklum_balas_ketidakpatuhan
            sitevisit_info_obj.updated_date = today
            sitevisit_info_obj.updated_by = id_card_no
            db.session.commit()
            
            statement = "Site visit information "+site_id+" updated successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Site visit information updated successfully.")
            response_object = {
                'status':'success',
                'message':'Site visit information updated successfully.'
            }
            return response_object, 201
        except:
            logger.exception("Site visit information Could not be updated")
            response_object = {
                'status':'fail',
                'message':'Site visit information could not be updated .'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'Site Visit Information could not be found',
        }
        return response_object, 404    

""" ===============================<< update site visit application list Ends >>=============================== """
""" ===============================<< Delete list of site visit information starts >>=============================== """

@token_required
def deletelistOfsitevisitInformation(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    site_id_list = data.site_id_list.split(",")
    try:
        if user.user_type == 'dbkl':
            for i in site_id_list:
                
                if PublicSiteVisitInfo.query.filter_by(site_id=i).first():
                    PublicSiteVisitInfo.query.filter_by(site_id=i).first().active = 0

            db.session.commit()

            statement = "list Of sitevisit information Deleted successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()
            
            logger.info("list Of sitevisitInformation Deleted successfully")

            response_object = {
                "status": "success",
                "message": "list Of sitevisitInformation Deleted successfully."
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "User is not dbkl."
            } 

    except:

        logger.exception("list Of sitevisitInformation could not be deleted")
        response_object = {
            "status": "fail",
            "message": "list Of sitevisitInformation could not be Deleted."
        }
        return response_object, 400

""" ===============================<< Delete list of site visit information ends >>=============================== """

""" $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$<< KEWANGAN STARTS >>$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ """

""" ===============================<< Fetch Agency Job Payment claim starts >>=============================== """

@token_required
def getAgencyJobPaymentClaim():
    try:
        agency_jobPaymentClaim_res = []
        for jobPaymentClaim in AgencyJobPaymentClaim.query.filter_by(active=1):
            agency_jobPaymentClaim_res.append({
                "tarikh_tuntutan": jobPaymentClaim.tarikh,
                "kontraktor" : jobPaymentClaim.kontraktor,
                "no_inbois"   : jobPaymentClaim.no_inbois,
                "status_semakan_tuntutan_inbois":jobPaymentClaim.status,
                })
        logger.info("agency job payment claim fetched.")
        return jsonify(agency_jobPaymentClaim_res)
    except:
        logger.exception("agency job payment claim not fetched.")
        response_object = {
            'status':'fail',
            'message':'agency job payment claim not fetched.'
        }
        return response_object, 409  
""" ===============================<< Fetch Agency Job Payment claim ends >>=============================== """

""" ===============================<< Fetch Agency Job Payment claim by inbois starts >>=============================== """
@token_required
def getAgencyJobPaymentClaimByInbois(no_inbois):
    try:
        exists = db.session.query(AgencyJobPaymentClaim).filter_by(no_inbois=no_inbois, active=1)
    except:
        logger.exception('Agency Job Payment Claim by inbois could not be found')
        response_object = {
                'status': 'fail',
                'message': 'Agency Job Payment Claim by inbois could not be found',
            }
        return response_object, 404
    if exists:
        try:
            inventori_pengguna_obj = AgencyJobPaymentClaim.query.filter_by(no_inbois=no_inbois, active=1).first()
            inventori_pengguna_res = {
                "no_nbois" : inventori_pengguna_obj.no_inbois,
                "kontraktor" : inventori_pengguna_obj.kontraktor,
                "nama_pemohon" : inventori_pengguna_obj.nama_pemohon,
                "e_mei" : inventori_pengguna_obj.e_mei,
                "jumlah_tuntutan" : inventori_pengguna_obj.jumlah_tuntutan,
                "inbois_dokumen" : inventori_pengguna_obj.inbois_dokumen,
                "ringkasan_dokumen" : inventori_pengguna_obj.ringkasan_dokumen,
                "lampiran" : inventori_pengguna_obj.lampiran,
                "kemaskini_status" : inventori_pengguna_obj.status,
                "ulasan_pegawai" : inventori_pengguna_obj.ulasan_pegawai,
            }
            logger.info("Agency Job Payment Claim by inbois no fetched")
            return inventori_pengguna_res
        except:
            logger.exception("Agency Job Payment Claim by inbois no not fetched")
            response_object = {
                'status':'fail',
                'message':'Agency Job Payment Claim by inbois no not fetched.'
            }
            return response_object, 400  
    else:
        response_object = {
            'status': 'fail',
            'message': 'Agency Job Payment Claim by inbois could not be found',
        }
        return response_object, 404     
    
""" ===============================<< Fetch Agency Job Payment claim by inbois ends >>=============================== """

""" ===============================<< update Agency Job Payment claim by inbois starts >>=============================== """

@token_required
def updateAgencyJobPaymentClaimByInbois(no_inbois,data):
    nama_pemohon = data.nama_pemohon
    e_mei = data.e_mei
    jumlah_tuntutan = data.jumlah_tuntutan
    inbois_dokumen = data.inbois_dokumen
    ringkasan_dokumen = data.ringkasan_dokumen
    lampiran = data.lampiran
    status = data.status
    ulasan_pegawai = data.ulasan_pegawai
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    try:
        agency_job_obj = db.session.query(AgencyJobPaymentClaim).filter_by(no_inbois=no_inbois, active=1).first()
    
    except:
        logger.exception('Agency Job Payment claim by inbois could not be found')
        response_object = {
            'status': 'fail',
            'message': 'Agency Job Payment claim by inbois could not be found',
        }
        return response_object, 404
    if agency_job_obj:
        try:
            agency_job_obj.nama_pemohon = nama_pemohon
            agency_job_obj.e_mei = e_mei
            agency_job_obj.jumlah_tuntutan = jumlah_tuntutan
            agency_job_obj.inbois_dokumen = inbois_dokumen
            agency_job_obj.ringkasan_dokumen = ringkasan_dokumen
            agency_job_obj.lampiran = lampiran
            agency_job_obj.status = status
            agency_job_obj.ulasan_pegawai = ulasan_pegawai
            agency_job_obj.updated_date = today
            agency_job_obj.updated_by = id_card_no
            db.session.commit()
            
            statement = "Agency Job PaymentClaim "+no_inbois+" updated successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()
            
            logger.info("Agency Job PaymentClaim updated successfully")
            response_object = {
                'status' : 'Success',
                'message' : 'Agency Job PaymentClaim updated successfully'
            } 
            return response_object
        except:
            logger.exception("agency job payment claim by inbois no not updated")
            response_object = {
                    'status':'fail',
                    'message':'agency job payment claim by inbois no not updated.'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'Agency Job Payment claim by inbois could not be found',
        }
        return response_object, 404          
    
""" ===============================<< update Agency Job Payment claim by inbois ends >>=============================== """
""" ===============================<< Delete Agency Job Payment claim starts >>=============================== """

@token_required
def deleteAgencyJobPaymentClaim(data):

    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    no_inbois_list = data.no_inbois_list.split(",")
    try:
        if user.user_type == 'dbkl':
            for i in no_inbois_list:
                if AgencyJobPaymentClaim.query.filter_by(no_inbois=i).first():
                    AgencyJobPaymentClaim.query.filter_by(no_inbois=i).first().active = 0
                
            db.session.commit()
            
            statement = "Agency jobPaymentClaim list deleted successfully by "+id_card_no
            log_info = Log(statement=statement,date=today,user_name=id_card_no)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Agency JobPaymentClaim list Deleted successfully")

            response_object = {
                "status": "success",
                "message": "Agency JobPaymentClaim list Deleted successfully."
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "User is not dbkl."
            } 

    except:
        logger.exception("Agency JobPaymentClaim list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Agency JobPaymentClaim list could not be Deleted."
        }
        return response_object, 400


""" ===============================<< Delete Agency Job Payment claim ends >>=============================== """
""" ===============================<< Fetch jkas_omp starts >>=============================== """
@token_required
def getOmpBaru():
    try:
        omp_baru_list = []
        for jkasOmp in OmpBaru.query.filter_by(active=1):
            omp_baru_list.append({
                "kodarea": jkasOmp.kodarea,
                "lokasi" : jkasOmp.lokasi,
                "parlimen"   : jkasOmp.parlimen,
                "parlimen_subarea":jkasOmp.parlimen_subarea,
                "kordinat":jkasOmp.kordinat,
                "jumlah_unit_premis":jkasOmp.jumlah_unit_premis,
                "kekerapan_kutipan_sisa_domestik":jkasOmp.kekerapan_kutipan_sisa_domestik,
                "kekerapan_kutipan_sampah_pukal":jkasOmp.kekerapan_kutipan_sampah_pukal,
                "kekerapan_kutipan_sampah_haram":jkasOmp.kekerapan_kutipan_sampah_haram,
                "ukuran_panjang_sapuan_jalan":jkasOmp.ukuran_panjang_sapuan_jalan,
                "ukuran_panjang_sapuan_TPKK":jkasOmp.ukuran_panjang_sapuan_TPKK,
                "ukuran_panjang_sapuan_kewlapangparkir":jkasOmp.ukuran_panjang_sapuan_kewlapangparkir,
                "ukuran_panjang_jejantas_sapuan":jkasOmp.ukuran_panjang_jejantas_sapuan,
                "ukuran_panjang_jejantas_cucian":jkasOmp.ukuran_panjang_jejantas_cucian,
                "ukuran_panjang_cucian_siarkaki":jkasOmp.ukuran_panjang_cucian_siarkaki,
                "ukuran_panjang_cucian_siarkaki_berbumbung":jkasOmp.ukuran_panjang_cucian_siarkaki_berbumbung,
                "ukuran_panjang_cucian_slesenbaslteksi":jkasOmp.ukuran_panjang_cucian_slesenbaslteksi,
                "ukuran_panjang_cucilongkan":jkasOmp.ukuran_panjang_cucilongkan,
                "ukuran_panjang_potongrumput":jkasOmp.ukuran_panjang_potongrumput,
                "ukuran_panjang_sampahkebun":jkasOmp.ukuran_panjang_sampahkebun,
                "catatan":jkasOmp.catatan,
                "rujuken_tarikh_serahan":jkasOmp.rujuken_tarikh_serahan,
                "tarikh_semakandi_lapangant_keadeansemata_ada":jkasOmp.tarikh_semakandi_lapangant_keadeansemata_ada,
                "tarikh_semakandi_lapangant_keadeansemata_tiada":jkasOmp.tarikh_semakandi_lapangant_keadeansemata_tiada
                })
        logger.info("OMP Baru list fetched.")
        return jsonify(omp_baru_list)
    except:
        logger.exception("OMP Baru list could not be fetched.")
        response_object = {
            'status':'fail',
            'message':'OMP Baru list could not be fetched.'
        }
        return response_object, 400  
""" ===============================<< Fetch jkas_omp ends >>=============================== """
""" ===============================<< Fetch OmpLama starts >>=============================== """

@token_required
def getOmpLama(parliament_name):
    try:
        omp_lama_res = []
        for ompLama in OmpLama.query.filter_by(parlimen_name=parliament_name, active=1):
            omp_lama_res.append({
                "parlimen_name": ompLama.parlimen_name,
                "kod_kekerapan_kutipan" : ompLama.kod_kekerapan_kutipan,
                "pembersihan"   : ompLama.pembersihan
                })
        logger.info("OmpLama fetched")
        return jsonify(omp_lama_res) 
    except:
        logger.exception("OmpLama not fetched")
        response_object = {
            'status':'fail',
            'message':'OmpLama not fetched.'
        }
        return response_object, 400     
        
""" ===============================<< Fetch OmpLama Ends >>=============================== """           
""" ===============================<< MTB Officers List starts >>=============================== """
@token_required
def getMTBOfficersList():
    user = get_logged_in_user()
    if user.role == 'merinyu_mtk':
        try:
            officers_list = []
            for officer in OfficersList.query.filter_by(active=1):
                officers_list.append({
                    'officer_id': officer.officer_id,
                    'id_mtb': officer.id_mtb,
                    'parlimen': officer.parlimen,
                    'date': date.strftime(officer.tarikh, "%Y-%m-%d"),
            })
            logger.info("Officers list fetched")
            return jsonify(officers_list)

        except:
            logger.exception("Officers list could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Officers list could not be fetched',
            }
            return response_object, 400
    else:
        logger.debug("MTB user Dont have permission to see Officers list")
        response_object = {
            'status': 'fail',
            'message': 'MTB user Dont have permission to see Officers list',
            }
        return response_object, 400 
    
""" ===============================<< MTB Officers List ends >>=============================== """
""" ===============================<< getMTBOfficerInfo starts >>=============================== """

@token_required
def getMTBOfficerInfo():
    user = get_logged_in_user()
    nama = 'MTB_'+user.nama
    try:
        officer_info = []
        for officer in OfficersList.query.filter_by(id_mtb=nama, active=1):
            officer_info.append({
                'officer_id': officer.officer_id,
                'id_mtb': officer.id_mtb,
                'parlimen': officer.parlimen,
                'date': date.strftime(officer.tarikh, "%Y-%m-%d"),
        })
        logger.info("Officers info fetched")
        return jsonify(officer_info)

    except:
        logger.exception("Officers info could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Officers info could not be fetched',
        }
        return response_object, 400
    
    
""" ===============================<< getMTBOfficerInfo ends >>=============================== """
""" ===============================<< getDailyMTBInquiryInforByMTKn starts >>=============================== """

@token_required
def getDailyMTBInquiryInforByMTK(data):
    tarikh = data.tarikh
    id_mtb = data.id_mtb
    
    try:
        inquiry_list_log = []
        for log in InquiryInformation.query.filter_by(tarikh=tarikh,id_mtb=id_mtb, active=1):
            inquiry_list_log.append({
                'tarikh': log.tarikh,
                'masa': log.masa,
                'lokasi_aduan': log.lokasi_aduan,
                'lokasi_siasatan': log.lokasi_siasatan,
                'borang_siasatan': log.borang_siasatan
            })
        logger.info("Inquiry Information fetched")
        return jsonify(inquiry_list_log)
    except:
        logger.exception("Inquiry Information could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Inquiry Information could not be fetched',
        }
        return response_object, 400
        
""" ===============================<< getDailyMTBInquiryInforByMTK ends >>=============================== """
""" ===============================<< getDailyMTBInquiryInforByMTB starts >>=============================== """

@token_required
def getDailyMTBInquiryInforByMTB(tarikh):
    user = get_logged_in_user()
    id_mtb = 'MTB_'+user.nama
    parlimen = user.parlimen
    
    try:
        inquiry_list_log = []
        for log in InquiryInformation.query.filter_by(tarikh=tarikh,id_mtb=id_mtb, parlimen=parlimen, active=1):
            inquiry_list_log.append({
                'tarikh': log.tarikh,
                'masa': log.masa,
                'lokasi_aduan': log.lokasi_aduan,
                'lokasi_siasatan': log.lokasi_siasatan,
                'borang_siasatan': log.borang_siasatan
            })
        logger.info("Inquiry Information fetched")
        return jsonify(inquiry_list_log)
    except:
        logger.exception("Inquiry Information could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Inquiry Information could not be fetched',
        }
        return response_object, 400
        
""" ===============================<< getDailyMTBInquiryInforByMTK ends >>=============================== """
""" ===============================<< Add Complaint Investigation starts >>=============================== """
@token_required
def addComplaintInvestigation(data):
    user = get_logged_in_user()
    name = user.no_kad_pengenalan
    parlimen = user.parlimen
    pengadu_nama=data.pengadu_nama
    pengadu_alamat=data.pengadu_alamat
    no_telefon=data.no_telefon
    tarikh_terima_aduan=data.tarikh_terima_aduan
    emel=data.emel
    no_faksimili=data.no_faksimili
    sumber_aduan=data.sumber_aduan
    tarikh_aduan=data.tarikh_aduan
    tarikh_terima=data.tarikh_terima
    no_rujukan=data.no_rujukan
    lokasi_aduan=data.lokasi_aduan
    keterangan_aduan=data.keterangan_aduan
    tarikh_siasatan=data.tarikh_siasatan
    masa_siasatan=data.masa_siasatan
    nama_pegawai=data.nama_pegawai
    id_mtb=data.id_mtb
    lokasi_siasatan=data.lokasi_siasatan
    laporan_siasatan=data.laporan_siasatan
    tindakan=data.tindakan
    susulan=data.susulan
    ullasan_penyelia=data.ullasan_penyelia
    ullasan_ketua_seksyen=data.ullasan_ketua_seksyen
    today = date.today()
    try:
        officers_list = OfficersList(
            id_mtb=id_mtb ,parlimen=parlimen, tarikh=tarikh_siasatan, inserted_by=name,inserted_date=today, active=1
        )
        db.session.add(officers_list)
        db.session.commit()
        complaint_investigation_form = ComplaintInvestigation(
            pengadu_nama=pengadu_nama,pengadu_alamat=pengadu_alamat,no_telefon=no_telefon,tarikh_terima_aduan=tarikh_terima_aduan,
            emel=emel,no_faksimili=no_faksimili,sumber_aduan=sumber_aduan,tarikh_aduan=tarikh_aduan,tarikh_terima=tarikh_terima,no_rujukan=no_rujukan,
            lokasi_aduan=lokasi_aduan,keterangan_aduan=keterangan_aduan,tarikh_siasatan=tarikh_siasatan,masa_siasatan=masa_siasatan,
            nama_pegawai=nama_pegawai,id_mtb=id_mtb,lokasi_siasatan=lokasi_siasatan,laporan_siasatan=laporan_siasatan,tindakan=tindakan,
            susulan=susulan,ullasan_penyelia=ullasan_penyelia,ullasan_ketua_seksyen=ullasan_ketua_seksyen,inserted_by=name,inserted_date=today, active=1)
        db.session.add(complaint_investigation_form)
        db.session.commit()
        
        inquiry_info = InquiryInformation(
            id_mtb=id_mtb, tarikh=tarikh_siasatan, masa=masa_siasatan, lokasi_aduan=lokasi_aduan,lokasi_siasatan=lokasi_siasatan,borang_siasatan=lokasi_aduan ,inserted_by=name,inserted_date=today, active=1
        )
        db.session.add(inquiry_info)
        db.session.commit()
        
        statement = "New complaint investigation form added successfully by "+name
        log_info = Log(statement=statement,date=today,user_name=name)
        db.session.add(log_info)
        db.session.commit()

        logger.info('Complaint Investigation Form Added')
        response_object = {
                'status': 'success',
                'message': 'Complaint Investigation Added',
            }
        return response_object, 201
    except:
        logger.exception("Complaint Investigation not added")
        response_object = {
            'status': 'fail',
            'message': 'Complaint Investigation could not be added',
        }
        return response_object, 400
        

""" ===============================<< Add Complaint Investigation ends >>=============================== """
""" ===============================<< get Complaint Investigation Form starts >>=============================== """

@token_required
def getComplaintInvestigation(data):
    masa_siasatan=data.masa_siasatan
    tarikh_siasatan=data.tarikh_siasatan
    id_mtb=data.id_mtb
    try:
        complaint_info = db.session.query(ComplaintInvestigation).filter_by(id_mtb=id_mtb, masa_siasatan=masa_siasatan, tarikh_siasatan=tarikh_siasatan, active=1).first()
    except:
        logger.exception('No data found with given id_mtb and tarikh_siasatan')
        response_object = {
                'status': 'fail',
                'message': 'No data found with given id_mtb and tarikh_siasatan',
            }
        return response_object, 404
    if complaint_info:
        try:
            completed_form = []
            for form in ComplaintInvestigation.query.filter_by(id_mtb=id_mtb, masa_siasatan=masa_siasatan, tarikh_siasatan=tarikh_siasatan, active=1):
                completed_form.append({
                    "form_id": form.form_id,
                    "pengadu_nama":form.pengadu_nama,
                    "pengadu_alamat":form.pengadu_alamat,
                    "no_telefon":form.no_telefon,
                    "no_rujukan":form.no_rujukan,
                    "tarikh_terima_aduan":form.tarikh_terima_aduan,
                    "emel":form.emel,
                    "no_faksimili":form.no_faksimili,
                    "sumber_aduan":form.sumber_aduan,
                    "tarikh_aduan":form.tarikh_aduan,
                    "tarikh_terima":form.tarikh_terima,
                    "lokasi_aduan":form.lokasi_aduan,
                    "keterangan_aduan":form.keterangan_aduan,
                    "tarikh_siasatan":form.tarikh_siasatan,
                    "masa_siasatan":form.masa_siasatan,
                    "nama_pegawai":form.nama_pegawai,
                    "id_mtb":form.id_mtb,
                    "lokasi_siasatan":form.lokasi_siasatan,
                    "laporan_siasatan":form.laporan_siasatan,
                    "tindakan":form.tindakan,
                    "susulan":form.susulan,
                    "ullasan_penyelia":form.ullasan_penyelia,
                    "ullasan_ketua_seksyen":form.ullasan_ketua_seksyen,
                })
            logger.info("Complaint Investigation fetched")
            return jsonify(completed_form)
        except:
            logger.exception("Complaint Investigation Form could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Complaint Investigation form could not be fetched',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': f'No Complaint Investigation is found',
        }
        return response_object, 404

""" ===============================<< get Complaint Investigstion Form ends >>=============================== """
""" ===============================<< Update Complaint Investigation Form starts >>=============================== """

@token_required
def updateComplaintInvestigation(form_id,data):
    user = get_logged_in_user()
    name = user.no_kad_pengenalan
    parlimen = user.parlimen
    pengadu_nama=data.pengadu_nama
    pengadu_alamat=data.pengadu_alamat
    no_telefon=data.no_telefon
    tarikh_terima_aduan=data.tarikh_terima_aduan
    emel=data.emel
    no_faksimili=data.no_faksimili
    sumber_aduan=data.sumber_aduan
    tarikh_aduan=data.tarikh_aduan
    tarikh_terima=data.tarikh_terima
    no_rujukan=data.no_rujukan
    lokasi_aduan=data.lokasi_aduan
    keterangan_aduan=data.keterangan_aduan
    tarikh_siasatan=data.tarikh_siasatan
    masa_siasatan=data.masa_siasatan
    nama_pegawai=data.nama_pegawai
    id_mtb=data.id_mtb
    lokasi_siasatan=data.lokasi_siasatan
    laporan_siasatan=data.laporan_siasatan
    tindakan=data.tindakan
    susulan=data.susulan
    ullasan_penyelia=data.ullasan_penyelia
    ullasan_ketua_seksyen=data.ullasan_ketua_seksyen
    today = date.today()
    complaint_info = db.session.query(ComplaintInvestigation).filter_by(form_id=form_id, active=1).one()
    if complaint_info:
        try:
            complaint_Investigation_obj = ComplaintInvestigation.query.filter_by(form_id=form_id, active=1).first()
            complaint_Investigation_obj.pengadu_nama = pengadu_nama
            complaint_Investigation_obj.pengadu_alamat = pengadu_alamat
            complaint_Investigation_obj.no_telefon = no_telefon
            complaint_Investigation_obj.tarikh_terima_aduan = tarikh_terima_aduan
            complaint_Investigation_obj.no_rujukan = no_rujukan
            complaint_Investigation_obj.emel = emel
            complaint_Investigation_obj.no_faksimili = no_faksimili
            complaint_Investigation_obj.sumber_aduan = sumber_aduan
            complaint_Investigation_obj.tarikh_aduan = tarikh_aduan
            complaint_Investigation_obj.tarikh_terima = tarikh_terima
            complaint_Investigation_obj.lokasi_aduan = lokasi_aduan
            complaint_Investigation_obj.keterangan_aduan = keterangan_aduan
            complaint_Investigation_obj.tarikh_siasatan = tarikh_siasatan
            complaint_Investigation_obj.masa_siasatan = masa_siasatan
            complaint_Investigation_obj.nama_pegawai = nama_pegawai
            complaint_Investigation_obj.id_mtb = id_mtb
            complaint_Investigation_obj.lokasi_siasatan = lokasi_siasatan
            complaint_Investigation_obj.laporan_siasatan = laporan_siasatan
            complaint_Investigation_obj.tindakan = tindakan
            complaint_Investigation_obj.susulan = susulan
            complaint_Investigation_obj.ullasan_penyelia = ullasan_penyelia
            complaint_Investigation_obj.ullasan_ketua_seksyen = ullasan_ketua_seksyen
            complaint_Investigation_obj.updated_date = today
            complaint_Investigation_obj.updated_by = name
            db.session.commit()

            statement = "Complaint investigation form "+form_id+ " updated successfully by "+name
            log_info = Log(statement=statement,date=today,user_name=name)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Complaint investigation form updated successfully.")
            response_object = {
                'status': 'success',
                'message': 'Complaint investigation form updated.',
            }
            return response_object, 200
        except:
            logger.exception("Complaint investigation form could not be updated.")
            response_object = {
                'status': 'fail',
                'message': 'Complaint investigation form could not be updated.',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': f'No Complaint Investigation Form is registered with Form id {form_id}',
        }
        return response_object, 404

""" ===============================<< get MTB Complaint Investigstion Form ends >>=============================== """
""" ===============================<< get MTB Compound Information starts >>=============================== """
@token_required
def getMTBCompoundInformation(data):
    tarikh = data.tarikh
    id_mtb = data.id_mtb
    parlimen = data.parlimen
    
    try:
        compound_list = []
        for log in CompoundInformation.query.filter_by(tarikh=tarikh,id_mtb=id_mtb, parlimen=parlimen, active=1):
            compound_list.append({
                'masa': log.masa,
                'lokasi_kompaun': log.lokasi_kompaun,
                'no_notis_bas': log.no_notis_bas,
            })
        logger.info('MTB Compound Information fetched')
        return jsonify(compound_list)
    except:
        logger.exception("MTB Compound Information could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'MTB Compound Information could not be fetched',
        }
        return response_object, 400
        
""" ===============================<< get MTB CompoundInformation ends >>=============================== """
""" ===============================<< get MTB Compound Information by MTB starts >>=============================== """
@token_required
def getMTBCompoundInfoByMTB(data):
    user = get_logged_in_user()
    id_mtb = 'MTB_'+user.nama
    parlimen = user.parliemn
    tarikh = data.tarikh
    
    try:
        compound_list = []
        for log in CompoundInformation.query.filter_by(tarikh=tarikh,id_mtb=id_mtb, parlimen=parlimen, active=1):
            compound_list.append({
                'masa': log.masa,
                'lokasi_kompaun': log.lokasi_kompaun,
                'no_notis_bas': log.no_notis_bas,
            })
        logger.info('MTB Compound Information fetched')
        return jsonify(compound_list)
    except:
        logger.exception("MTB Compound Information could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'MTB Compound Information could not be fetched',
        }
        return response_object, 400
        
""" ===============================<< get MTB CompoundInformation by MTB ends >>=============================== """
""" ===============================<< Add MTB Compound Form starts >>=============================== """
@token_required
def addMTBCompoundForm(data):
    no_notis_bas = data.no_notis_bas
    kepada = data.kepada
    company_no = data.company_no
    alamat = data.alamat
    id_mtb = data.id_mtb
    parlimen = data.parlimen
    lokasi_kompaun = data.lokasi_kompaun
    akta_jalan = data.akta_jalan
    undang_kecil_permungutan = data.undang_kecil_permungutan
    undang_kecil_pelesenan = data.undang_kecil_pelesenan
    undang_pelesenan_penjaja = data.undang_pelesenan_penjaja
    undang_kecil_larangan_meludah = data.undang_kecil_larangan_meludah
    butir_butir_kesalahan = data.butir_butir_kesalahan
    tarikh = data.tarikh
    waktu = data.waktu
    tempat = data.tempat
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        newCompoundInfo = CompoundInformation(id_mtb=id_mtb,parlimen=parlimen,tarikh=tarikh,masa=today,lokasi_kompaun=lokasi_kompaun,
                                              no_notis_bas=no_notis_bas,inserted_by=id_card_no,inserted_date=today, active=1)
        db.session.add(newCompoundInfo)
        db.session.commit()

        newCompoundForm = CompoundForm(no_notis_bas=no_notis_bas,kepada=kepada,company_no=company_no,alamat=alamat,id_mtb=id_mtb,
                      parlimen=parlimen,lokasi_kompaun=lokasi_kompaun,akta_jalan=akta_jalan,undang_kecil_permungutan=undang_kecil_permungutan,
                      undang_kecil_pelesenan=undang_kecil_pelesenan,undang_pelesenan_penjaja=undang_pelesenan_penjaja,
                      undang_kecil_larangan_meludah=undang_kecil_larangan_meludah,butir_butir_kesalahan=butir_butir_kesalahan,
                      tarikh=tarikh,waktu=waktu,tempat=tempat,inserted_by=id_card_no,inserted_date=today, active=1)
        
        db.session.add(newCompoundForm)
        db.session.commit()
        
        statement = "New MTB compound form added successfully by "+id_card_no
        log_info = Log(statement=statement,date=today,user_name=id_card_no)
        db.session.add(log_info)
        db.session.commit()


        logger.info("MTB Compound Form added Successfully")
        response_object = {
            'status': 'success',
            'message': 'MTB Compound Form added Successfully',
        }
        return response_object, 201
    except:
        logger.exception("MTB Compound Form not added")
        response_object = {
            'status': 'fail',
            'message': 'MTB Compound Form not added',
        }
        return response_object, 400
    
""" ===============================<< Add MTB Compound Form ends >>=============================== """
""" ===============================<< get MTB Compound Form starts >>=============================== """
@token_required
def getCompoundForm(no_notis_bas):
    try:
        compound_form_data = CompoundForm.query.filter_by(no_notis_bas=no_notis_bas).first()
    except:
        logger.exception('Compound form not found in database')
        response_object = {
                'status': 'fail',
                'message': f'No Notis Bas {no_notis_bas} does not contain any information',
            }
        return response_object, 404 
    if compound_form_data: 
        try:
            compound_list = []
            for compound_info in CompoundForm.query.filter_by(no_notis_bas=no_notis_bas, active=1):
                compound_list.append({
                    'no_notis_bas': compound_info.no_notis_bas,
                    'kepada': compound_info.kepada,
                    'company_no': compound_info.company_no,
                    'alamat': compound_info.alamat,
                    'id_mtb': compound_info.id_mtb,
                    'parlimen': compound_info.parlimen,
                    'lokasi_kompaun': compound_info.lokasi_kompaun,
                    'akta_jalan': compound_info.akta_jalan,
                    'undang_kecil_permungutan': compound_info.undang_kecil_permungutan,
                    'undang_kecil_pelesenan': compound_info.undang_kecil_pelesenan,
                    'undang_pelesenan_penjaja': compound_info.undang_pelesenan_penjaja,
                    'undang_kecil_larangan_meludah': compound_info.undang_kecil_larangan_meludah,
                    'butir_butir_kesalahan': compound_info.butir_butir_kesalahan,
                    'tarikh': compound_info.tarikh,
                    'waktu': compound_info.waktu,
                    'tempat': compound_info.tempat,
                })
            logger.info('Compound Form fetched')
            return jsonify(compound_list)
        except:
            logger.exception("Compound Form could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Compound Form could not be fetched',
            }
            return response_object, 400
    else:
        response_object = {
                'status': 'fail',
                'message': f'No Notis Bas {no_notis_bas} does not contain any information',
            }
        return response_object, 404 
""" ===============================<< get MTB Compound Form ends >>=============================== """
""" ===============================<< Send Notice starts >>=============================== """
def sendNotice(data):
    id_mtb = data.id_mtb
    nama_pegawai_merinyu=data.nama_pegawai_merinyu
    lokasi_merinyu=data.lokasi_merinyu
    gambar_lokasi_kerja_photo1=data.gambar_lokasi_kerja_photo1
    gambar_lokasi_kerja_photo2=data.gambar_lokasi_kerja_photo2
    gambar_lokasi_kerja_photo3=data.gambar_lokasi_kerja_photo3
    if gambar_lokasi_kerja_photo1:
        gambar_lokasi_kerja_photo1 = re.sub('[^a-zA-Z0-9.]', '', gambar_lokasi_kerja_photo1)
        gambar_lokasi_kerja_photo1 = '/jkas_resourses/public/pdfs/'+gambar_lokasi_kerja_photo1
    if gambar_lokasi_kerja_photo2:
        gambar_lokasi_kerja_photo2 = re.sub('[^a-zA-Z0-9.]', '', gambar_lokasi_kerja_photo2)
        gambar_lokasi_kerja_photo2 = '/jkas_resourses/public/pdfs/'+gambar_lokasi_kerja_photo2
    if gambar_lokasi_kerja_photo3:
        gambar_lokasi_kerja_photo3 = re.sub('[^a-zA-Z0-9.]', '', gambar_lokasi_kerja_photo3)
        gambar_lokasi_kerja_photo3 = '/jkas_resourses/public/pdfs/'+gambar_lokasi_kerja_photo3
        
    status_tindakan=data.status_tindakan
    kontraktor_emel=data.kontraktor_emel
    
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()

        notice_info= Notice(id_mtb=id_mtb,nama_pegawai_merinyu=nama_pegawai_merinyu,lokasi_merinyu=lokasi_merinyu,
                            gambar_lokasi_kerja_photo1=gambar_lokasi_kerja_photo1,gambar_lokasi_kerja_photo2=gambar_lokasi_kerja_photo2,
                            gambar_lokasi_kerja_photo3=gambar_lokasi_kerja_photo3,status_tindakan=status_tindakan,kontraktor_emel=kontraktor_emel, active=1
        )
        db.session.add(notice_info)
        db.session.commit()
        statement = "New notice information added successfully by "+id_card_no
        log_info = Log(statement=statement,date=today,user_name=id_card_no)
        db.session.add(log_info)
        db.session.commit()
        
    except:
        logger.exception("Notice information could not be save in Database")
        return "Notice information could not be save in Database"
    
    TO_EMAIL = kontraktor_emel
    message = MIMEMultipart()
    message['From'] = FROM_EMAIL
    message['To'] = TO_EMAIL
    message['Subject'] = 'Notis Pemberitahuan'
    MAIL_CONTENT = f"nama_pegawai_merinyu : {nama_pegawai_merinyu}\
                    lokasi_merinyu: {lokasi_merinyu}\
                    status_tindakan: {status_tindakan}"
    message.attach(MIMEText(MAIL_CONTENT, 'plain'))
    try:
        mail_session = smtplib.SMTP('smtp.gmail.com', 587)
        mail_session.starttls()
        mail_session.login(SMTP_MAIL, SMTP_PASSWORD)
        text = message.as_string()
        mail_session.sendmail(FROM_EMAIL, TO_EMAIL, text)
        mail_session.quit()
        logger.info("Notice Sent")
        response_object = {
            "status": "success",
            "message": "Notice sent successfully!"
        }
        return response_object
    except:
        logger.exception("Notice could not be sent")
        response_object = {
            "status": "fail",
            "message": f"Failed to sent mail to {kontraktor_emel}"
        }
        return response_object, 400
        
""" ===============================<<Send Notice ends >>=============================== """
""" ===============================<<Fetch Graf Prestasi Bulanan Starts>>=============================== """
def grafPrestasiBulanan(data):
    id_pegawai_merinyu = data.id_pegawai_merinyu 
    parlimen = data.parlimen
    nama_pegawai = data.nama_pegawai
    sub_area = data.sub_area
    try:
        grafPrestasiBulanan_obj = GrafPrestasiBulanan.query.filter_by(id_pegawai_merinyu=id_pegawai_merinyu,parlimen=parlimen, nama_pegawai=nama_pegawai, sub_area=sub_area).scalar()
        grafPrestasiBulanan_list = [
            {
                "jan_count":grafPrestasiBulanan_obj.jan_count,
                "feb_count":grafPrestasiBulanan_obj.feb_count,
                "mac_count":grafPrestasiBulanan_obj.mac_count,
                "april_count":grafPrestasiBulanan_obj.april_count,
                "mei_count":grafPrestasiBulanan_obj.mei_count,
                "jun_count":grafPrestasiBulanan_obj.jun_count,
                "julai_count":grafPrestasiBulanan_obj.julai_count,
                "ogos_count":grafPrestasiBulanan_obj.ogos_count,
                "sept_count":grafPrestasiBulanan_obj.sept_count,
                "okt_count":grafPrestasiBulanan_obj.okt_count,
                "nos_count":grafPrestasiBulanan_obj.nos_count,
                "dis_count":grafPrestasiBulanan_obj.dis_count
            }
        ]
        logger.info("graf prestasi bulanan fetched")
        return jsonify(grafPrestasiBulanan_list)
    except:
        logger.exception("graf prestasi bulanan not fetched")
        response_object = {
            "status" : "fail",
            "message" : "graf prestasi bulanan not fetched"
        }
        return response_object, 400
""" ===============================<<Fetch Graf Prestasi Bulanan Ends>>=============================== """
""" ===============================<<Fetch Graf Analisis Dan Statistik Starts>>=============================== """
def grafAnalisisDanStatistik(data):
    try:
        parlimen = data.parlimen
        kekerapan_kutipan_sisa_domestik_irj = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "IRJ").count() 
        kekerapan_kutipan_sisa_domestik_sks = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "SKS").count() 
        kekerapan_kutipan_sisa_domestik_6m = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "6M").count() 
        kekerapan_kutipan_sisa_domestik_7m = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "7M").count() 
        kekerapan_kutipan_sisa_domestik_ahad = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "Ahad").count() 
        kekerapan_kutipan_sisa_domestik_6m += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "6M/IRJ").count() 
        kekerapan_kutipan_sisa_domestik_irj += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "6M/IRJ").count() 
        kekerapan_kutipan_sisa_domestik_6m += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "6M/SKS").count() 
        kekerapan_kutipan_sisa_domestik_sks += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "6M/SKS").count() 
        kekerapan_kutipan_sisa_domestik_7m += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "7M/SKS").count() 
        kekerapan_kutipan_sisa_domestik_sks += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "7M/SKS").count() 
        kekerapan_kutipan_sisa_domestik_6m += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "IRJ/6M").count() 
        kekerapan_kutipan_sisa_domestik_irj += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "IRJ/6M").count() 
        kekerapan_kutipan_sisa_domestik_rabu = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "RABU & AHAD").count() 
        kekerapan_kutipan_sisa_domestik_ahad += OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "RABU & AHAD").count() 
        kekerapan_kutipan_sisa_domestik_rs = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "RS").count() 
        kekerapan_kutipan_sisa_domestik_sj = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sisa_domestik = "SJ").count()
        kekerapan_kutipan_sampah_pukal_ahad = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_pukal = "Ahad").count() 
        kekerapan_kutipan_sampah_pukal_irj = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_pukal = "IRJ").count() 
        kekerapan_kutipan_sampah_pukal_isnin = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_pukal = "Isnin").count() 
        kekerapan_kutipan_sampah_pukal_jumaat = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_pukal = "Jumaat").count() 
        kekerapan_kutipan_sampah_pukal_khamis = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_pukal = "Khamis").count() 
        kekerapan_kutipan_sampah_pukal_rabu = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_pukal = "Rabu").count() 
        kekerapan_kutipan_sampah_pukal_sabtu = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_pukal = "Sabtu").count() 
        kekerapan_kutipan_sampah_pukal_selasa = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_pukal = "Selasa").count() 
        kekerapan_kutipan_sampah_haram_ahad = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_haram = "Ahad").count() 
        kekerapan_kutipan_sampah_haram_irj = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_haram = "IRJ").count() 
        kekerapan_kutipan_sampah_haram_isnin = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_haram = "Isnin").count() 
        kekerapan_kutipan_sampah_haram_jumaat = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_haram = "Jumaat").count() 
        kekerapan_kutipan_sampah_haram_khamis = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_haram = "Khamis").count() 
        kekerapan_kutipan_sampah_haram_rabu = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_haram = "Rabu").count() 
        kekerapan_kutipan_sampah_haram_sabtu = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_haram = "Sabtu").count() 
        kekerapan_kutipan_sampah_haram_selasa = OmpBaru.query.filter_by(parlimen=parlimen,kekerapan_kutipan_sampah_haram = "Selasa").count() 
        ukuran_panjang_sapuan_jalan_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jalan = "7M").count() 
        ukuran_panjang_sapuan_jalan_6m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jalan = "6M").count() 
        ukuran_panjang_sapuan_jalan_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jalan = "IRJ/6M").count() 
        ukuran_panjang_sapuan_jalan_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jalan = "IRJ/6M").count() 
        ukuran_panjang_sapuan_jalan_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jalan = "SKS/ 6M").count() 
        ukuran_panjang_sapuan_jalan_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jalan = "SKS/ 6M").count() 
        ukuran_panjang_sapuan_jalan_sks += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jalan = "SKS").count() 
        ukuran_panjang_sapuan_jalan_irj += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jalan = "IRJ").count() 
        ukuran_panjang_jejantas_sapuan_6m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_jejantas_sapuan = "6M").count() 
        ukuran_panjang_jejantas_sapuan_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_jejantas_sapuan = "7M").count() 
        ukuran_panjang_jejantas_sapuan_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_jejantas_sapuan = "100 / SKS").count() 
        ukuran_panjang_jejantas_sapuan_sks += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_jejantas_sapuan = "279 / SKS").count() 
        ukuran_panjang_jejantas_sapuan_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_jejantas_sapuan = "557.4 / IRJ").count() 
        ukuran_panjang_sapuan_TPKK_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_TPKK = "7M").count() 
        ukuran_panjang_sapuan_TPKK_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_TPKK = "298 / SKS").count() 
        ukuran_panjang_sapuan_TPKK_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_TPKK = "IRJ").count()
        ukuran_panjang_sapuan_kewlapangparkir_6m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "3114.50 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "3213 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "1488 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "2439.68 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "8381.66 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "2306 / 7M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_7m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "1335.46 / 7M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_7m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "1275.353 / 7M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_7m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "227 / 7M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "8440.99 / SKS").count() 
        ukuran_panjang_sapuan_kewlapangparkir_sks += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "1223.43 / SKS").count() 
        ukuran_panjang_sapuan_kewlapangparkir_1s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kewlapangparkir = "950.86 / 1S").count()
        ukuran_panjang_jejantas_cucian_1s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_jejantas_cucian = "281.31 / 1S").count() 
        ukuran_panjang_jejantas_cucian_2s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_jejantas_cucian = "2S").count() 
        ukuran_panjang_jejantas_cucian_6m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_jejantas_cucian = "6M").count() 
        ukuran_panjang_cucian_siarkaki_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_siarkaki = "448 / 7M").count() 
        ukuran_panjang_cucian_siarkaki_7m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_siarkaki = "413 / 7M").count() 
        ukuran_panjang_cucian_siarkaki_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_siarkaki = "4151 / IRJ").count() 
        ukuran_panjang_cucilongkan_1s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucilongkan = "1S").count() 
        ukuran_panjang_cucilongkan_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucilongkan = "IRJ").count() 
        ukuran_panjang_cucilongkan_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucilongkan = "SKS").count()
        ukuran_panjang_potongrumput_2s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_potongrumput = "2S").count() 
        ukuran_panjang_potongrumput_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_potongrumput = "IRJ").count() 
        ukuran_panjang_potongrumput_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_potongrumput = "SKS").count()
        ukuran_panjang_sampahkebun_isnin = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sampahkebun = "Isnin").count() 
        ukuran_panjang_sampahkebun_6m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sampahkebun = "6M").count() 
        ukuran_panjang_sampahkebun_ahad = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sampahkebun = "Ahad").count() 
        ukuran_panjang_sampahkebun_jumaat = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sampahkebun = "Jumaat").count() 
        ukuran_panjang_sampahkebun_khamis = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sampahkebun = "Khamis").count() 
        ukuran_panjang_sampahkebun_rabu = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sampahkebun = "Rabu").count() 
        ukuran_panjang_sampahkebun_sabtu = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sampahkebun = "Sabtu").count() 
        ukuran_panjang_sampahkebun_selasa = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sampahkebun = "Selasa").count() 
    except:
        logger.exception("Data Not fetched")
        response_object = {
            "status": "fail",
            "message": "Data Not fetched"
        } 
    result = {
        "kekerapan_kutipan_sisa_domestik" : {
            "IRJ" : kekerapan_kutipan_sisa_domestik_irj, 
            "SKS" : kekerapan_kutipan_sisa_domestik_sks,
            "6M" : kekerapan_kutipan_sisa_domestik_6m,
            "7M" : kekerapan_kutipan_sisa_domestik_7m,   
            "Rabu" : kekerapan_kutipan_sisa_domestik_rabu, 
            "Ahad" : kekerapan_kutipan_sisa_domestik_ahad,
            "R/S" : kekerapan_kutipan_sisa_domestik_rs,
            "S/J" :  kekerapan_kutipan_sisa_domestik_sj
        },
        "kekerapan_kutipan_sampah_pukal" : {
            "Ahad" : kekerapan_kutipan_sampah_pukal_ahad, 
            "IRJ" : kekerapan_kutipan_sampah_pukal_irj, 
            "Isnin" : kekerapan_kutipan_sampah_pukal_isnin, 
            "Jumaat" : kekerapan_kutipan_sampah_pukal_jumaat, 
            "Khamis" : kekerapan_kutipan_sampah_pukal_khamis, 
            "Rabu" : kekerapan_kutipan_sampah_pukal_rabu, 
            "Sabtu" : kekerapan_kutipan_sampah_pukal_sabtu, 
            "Selasa" : kekerapan_kutipan_sampah_pukal_selasa
        },
        "kekerapan_kutipan_sampah_haram" : {
            "Ahad" : kekerapan_kutipan_sampah_haram_ahad, 
            "IRJ" : kekerapan_kutipan_sampah_haram_irj, 
            "Isnin" : kekerapan_kutipan_sampah_haram_isnin, 
            "Jumaat" : kekerapan_kutipan_sampah_haram_jumaat, 
            "Khamis" : kekerapan_kutipan_sampah_haram_khamis, 
            "Rabu" : kekerapan_kutipan_sampah_haram_rabu, 
            "Sabtu" : kekerapan_kutipan_sampah_haram_sabtu, 
            "Selasa" : kekerapan_kutipan_sampah_haram_selasa
        },
        "sapuan_jalan" : {
            "7M" : ukuran_panjang_sapuan_jalan_7m, 
            "6M" : ukuran_panjang_sapuan_jalan_6m, 
            "IRJ" : ukuran_panjang_sapuan_jalan_irj, 
            "SKS" : ukuran_panjang_sapuan_jalan_sks, 
        },
        "sapuan_jejantas" : {
            "6M" : ukuran_panjang_jejantas_sapuan_6m,
            "7M" : ukuran_panjang_jejantas_sapuan_7m,
            "SKS" : ukuran_panjang_jejantas_sapuan_sks,
            "IRJ" : ukuran_panjang_jejantas_sapuan_irj,
        },
        "sapuan_TPKK" : {
            "7M" : ukuran_panjang_sapuan_TPKK_7m,
            "SKS" : ukuran_panjang_sapuan_TPKK_sks,
            "IRJ" : ukuran_panjang_sapuan_TPKK_irj,        
        },
        "sapuan_kewlapang_parkir" : {
            "6M" : ukuran_panjang_sapuan_kewlapangparkir_6m,
            "7M" : ukuran_panjang_sapuan_kewlapangparkir_7m,
            "SKS" : ukuran_panjang_sapuan_kewlapangparkir_sks,
            "1S" : ukuran_panjang_sapuan_kewlapangparkir_1s       
        },
        "cucian_jejantas" : {
            "1S" : ukuran_panjang_jejantas_cucian_1s,
            "2S" : ukuran_panjang_jejantas_cucian_2s,
            "6M" : ukuran_panjang_jejantas_cucian_6m,
        },
        "cucian_siar_kaki" : {
            "7M" : ukuran_panjang_cucian_siarkaki_7m,
            "IRJ" : ukuran_panjang_cucian_siarkaki_irj,
        },
        "cuci_longkang" : {
            "1S" : ukuran_panjang_cucilongkan_1s,
            "IRJ" : ukuran_panjang_cucilongkan_irj,
            "SKS" : ukuran_panjang_cucilongkan_sks,
        },
        "potong_rumput" : {
            "2S" : ukuran_panjang_potongrumput_2s,
            "IRJ" : ukuran_panjang_potongrumput_irj,
            "SKS" : ukuran_panjang_potongrumput_sks,
        },
        "sampah_kebun" : {
            "Isnin" : ukuran_panjang_sampahkebun_isnin, 
            "6M" : ukuran_panjang_sampahkebun_6m,
            "Ahad" : ukuran_panjang_sampahkebun_ahad,
            "Jumaat" :ukuran_panjang_sampahkebun_jumaat,
            "Khamis" : ukuran_panjang_sampahkebun_khamis,
            "Rabu" : ukuran_panjang_sampahkebun_rabu,
            "Sabtu" : ukuran_panjang_sampahkebun_sabtu,
            "Selasa" :  ukuran_panjang_sampahkebun_selasa,
        },
    }
    return result, 200
""" ===============================<<Fetch Graf Analisis Dan Statistik Ends>>=============================== """
""" ===============================<<Fetch Graf Jumlah Kutipan Starts>>=============================== """
def grafJumlahKutipan():
    try:
        batu_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Batu",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        bukit_bintang_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="B.Bintang",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        lembah_pantai_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="L.Pantai",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        segambut_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Segambut",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        kepong_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Kepong",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        seputeh_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Seputeh",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        BTR_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="BTR",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        WMaju_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="W/Maju",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        cheras_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Cheras",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        titiwangsa_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Titiwangsa",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        SWangsa_count_domestik = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="S/Wangsa",OmpBaru.kekerapan_kutipan_sisa_domestik != " ").count() 
        batu_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Batu",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        bukit_bintang_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="B.Bintang",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        lembah_pantai_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="L.Pantai",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        segambut_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Segambut",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        kepong_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Kepong",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        seputeh_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Seputeh",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        BTR_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="BTR",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        WMaju_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="W/Maju",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        cheras_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Cheras",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        titiwangsa_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Titiwangsa",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
        SWangsa_count_pukal = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="S/Wangsa",OmpBaru.kekerapan_kutipan_sampah_pukal != " ").count() 
    except:
        logger.exception("Data Not fetched")
        response_object = {
            "status": "fail",
            "message": "Data Not fetched"
        } 
    response = {
        "sampah_sisa_domestik" : {
            "Bukit_Bintang" : bukit_bintang_count_domestik,
            "Lembah_Pantai" : lembah_pantai_count_domestik,
            "Segambut" : segambut_count_domestik,
            "Batu" : batu_count_domestik,
            "Kepong" : kepong_count_domestik,
            "Seputeh" : seputeh_count_domestik,
            "BTR" : BTR_count_domestik,
            "Wangsa_Maju" : WMaju_count_domestik,
            "Cheras" : cheras_count_domestik,
            "Titiwangsa" : titiwangsa_count_domestik,
            "Setiawangsa" : SWangsa_count_domestik,
        },
        "sampah_pukal" :  {
            "Bukit_Bintang" : bukit_bintang_count_pukal,
            "Lembah_Pantai" : lembah_pantai_count_pukal,
            "Segambut" : segambut_count_pukal,
            "Batu" : batu_count_pukal,
            "Kepong" : kepong_count_pukal,
            "Seputeh" : seputeh_count_pukal,
            "BTR" : BTR_count_pukal,
            "Wangsa_Maju" : WMaju_count_pukal,
            "Cheras" : cheras_count_pukal,
            "Titiwangsa" : titiwangsa_count_pukal,
            "Setiawangsa" : SWangsa_count_pukal,
        }
    }
    logger.info("Data Fetched")
    return response, 200
""" ===============================<<Fetch Graf Jumlah Kutipan Ends >>=============================== """
""" ===============================<<Fetch Graf Jumlah Pembersihan Awam Starts >>=============================== """
def grafJumlahPembersihanAwam():
    try:
        batu_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Batu",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        bukit_bintang_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="B.Bintang",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        lembah_pantai_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="L.Pantai",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        segambut_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Segambut",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        kepong_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Kepong",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        seputeh_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Seputeh",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        BTR_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="BTR",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        WMaju_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="W/Maju",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        cheras_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Cheras",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        titiwangsa_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Titiwangsa",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 
        SWangsa_count_sapuan = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="S/Wangsa",OmpBaru.ukuran_panjang_sapuan_jalan != " ").count() 

        batu_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Batu",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        bukit_bintang_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="B.Bintang",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        lembah_pantai_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="L.Pantai",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        segambut_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Segambut",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        kepong_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Kepong",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        seputeh_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Seputeh",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        BTR_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="BTR",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        WMaju_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="W/Maju",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        cheras_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Cheras",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        titiwangsa_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="Titiwangsa",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count() 
        SWangsa_count_cucian = db.session.query(OmpBaru).filter(OmpBaru.parlimen=="S/Wangsa",OmpBaru.ukuran_panjang_cucian_siarkaki != " ").count()
    
    except:
        logger.exception("Data Not fetched")
        response_object = {
            "status": "fail",
            "message": "Data Not fetched"
        } 

    response = {
        "Sapuan" : {
            "Bukit_Bintang" : bukit_bintang_count_sapuan,
            "Lembah_Pantai" : lembah_pantai_count_sapuan,
            "Segambut" : segambut_count_sapuan,
            "Batu" : batu_count_sapuan,
            "Kepong" : kepong_count_sapuan,
            "Seputeh" : seputeh_count_sapuan,
            "BTR" : BTR_count_sapuan,
            "Wangsa_Maju" : WMaju_count_sapuan,
            "Cheras" : cheras_count_sapuan,
            "Titiwangsa" : titiwangsa_count_sapuan,
            "Setiawangsa" : SWangsa_count_sapuan,
        },
        "Cucian" :  {
            "Bukit_Bintang" : bukit_bintang_count_cucian,
            "Lembah_Pantai" : lembah_pantai_count_cucian,
            "Segambut" : segambut_count_cucian,
            "Batu" : batu_count_cucian,
            "Kepong" : kepong_count_cucian,
            "Seputeh" : seputeh_count_cucian,
            "BTR" : BTR_count_cucian,
            "Wangsa_Maju" : WMaju_count_cucian,
            "Cheras" : cheras_count_cucian,
            "Titiwangsa" : titiwangsa_count_cucian,
            "Setiawangsa" : SWangsa_count_cucian,
        }
    } 
    logger.info("Data Fetched")
    return response, 200

""" ===============================<<Fetch Graf Jumlah Pembersihan Awam Ends >>=============================== """
""" ===============================<< getIdPegawai Starts >>=============================== """
def getIdPegawai():
    try:
        user = get_logged_in_user()
        name = user.no_kad_pengenalan
        Id_Pegawai = "MTB_"+name
        parlimen = user.parlimen
        response_object = {
            "Id_Pegawai" : Id_Pegawai,
            "parlimen" : parlimen
        }
        logger.info("Id_Pegawai and Parlimen fetched")
        return response_object
    except:
        response_object = {
            "status" : "fail",
            "message" : "Id_Pegawai and Parlimen not fetched"
        }
        logger.exception("Id_Pegawai and Parlimen not fetched")
        return response_object,400 
""" ===============================<< getIdPegawai Ends >>=============================== """
""" ===============================<< getLokasi Starts >>=============================== """
def getLokasi(parlimen):
    try:
        lokasi = Coordinates.query.filter_by(parlimen=parlimen, active=1).with_entities(Coordinates.lokasi).all()         
        lokasi_list = list(itertools.chain(*lokasi)) 
        return lokasi_list
        logger.info("lokasi fetched")
        
    except:
        response_object = {
            "status" : "fail",
            "message" : "lokasi not fetched"
        }
        logger.exception("lokasi not fetched")
        return response_object,400 
""" ===============================<< getLokasi Ends >>=============================== """