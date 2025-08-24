""" Business logic for /auth API endpoints."""
from http import HTTPStatus
# import os, glob, json, sys, csv, psycopg2, re, secrets
import os, glob, json, sys, csv, re, secrets
from flask.signals import appcontext_tearing_down
import smtplib
import calendar
from random import randint 
from flask import current_app, jsonify, session
from flask_restx import abort
from twilio.rest import Client
import pytz, requests, itertools
import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, not_, select, extract, desc
from datetime import date, time
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
import httplib2
import geopy
from geopy.geocoders import Nominatim

from applogger import logger
from app.main import db
from .decorators import token_required
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.main.config import DevelopmentConfig

from app.main.models.models import (
    Inquiry, MasterUser, PublicApplicationList, PublicApplicationDetails, MeetingArea, EMeeting,
    PublicSiteVisitInfo, NonComplianceForm, AgenciFeedback, JobPaymentClaim, OmpBaru, DetailedMeeting, 
    Organisasi, OfficersList, CompoundList, CompoundInformation, ComplaintInvestigation, InquiryInformation, CompoundForm, Notice, GrafPrestasiBulanan, Coordinates,
    LogPengguna, PerkhidmatanPusatTong, OtpStore, MapData, BlacklistedToken)
from app.main.util.datetime_util import (
    remaining_fromtimestamp,
    format_timespan_digits,
)

SMTP_MAIL = os.environ.get('SMTP_MAIL')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
UI_URL = os.environ.get('UI_URL')
SEND_GRID_KEY = os.environ.get('SEND_GRID_KEY')
# PRIVATE_PHOTO_FOLDER = os.environ.get('PRIVATE_PHOTO_FOLDER')
# PRIVATE_DOC_FOLDER = os.environ.get('PRIVATE_DOC_FOLDER')
tz = pytz.timezone('Asia/Kuala_Lumpur')

def send_email(sender, recipient, subject, content):
    response = requests.post('https://api.sendgrid.com/v3/mail/send', verify=False, json={
        "personalizations": [{
            "to": [{
                "email": recipient
            }]
        }],
        "from": {
            "email": sender
        },
        "subject": subject,
        "content": [{
            "type": "text/plain",
            "value": content
        }]
    }, headers={
        "Authorization": "Bearer " + SEND_GRID_KEY,
        "Content-Type": "application/json" 
    })
    return response.status_code == 202

""" ===============================<< Registration of new user starts >>==============================="""


def registerDbklUser(data):
    name = data.name
    nama_pengguna = data.nama_pengguna.upper()
    email = data.email
    password = data.password

    if MasterUser.find_by_email(email):
        abort(HTTPStatus.CONFLICT,"email_exists", status="fail")
    if MasterUser.find_by_nama_pengguna(nama_pengguna):
            abort(HTTPStatus.CONFLICT,"user_exists", status="fail")
    if MasterUser.find_by_nama(name):
            abort(HTTPStatus.CONFLICT,"user_exists", status="fail")
    return register(name, nama_pengguna, email, password)


def register(name, nama_pengguna, email, password):

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
    message['Subject'] = 'JKAS OTP'
    MAIL_CONTENT = f'''
    Salam Sejahtera,
    
    Harap perhatikan kod 6 digit - {randotp} untuk pendaftaran pengguna nama {nama_pengguna}
    
    
    Jabatan Kesihatan dan Alam Sekitar
    '''
    if send_email(FROM_EMAIL, TO_EMAIL, 'JKAS OTP', MAIL_CONTENT):
        logger.info("Mail Sent")
        response_object = {
            "status": "success",
            "message": "otp_sent"
        }
        return response_object
    logger.exception("Mail could not be sent")
    response_object = {
        "status": "fail",
        "message": "mail_failed"
    }
    return response_object, 400

 
def completeRegistration(data):
    user_otp = data.otp
    nama_pengguna = data.nama_pengguna.upper()
    user_type = 'dbkl'
    role = 'Analisis'
    lock_time = datetime(9999, 12, 31, 12, 59, 59)
    
    
    try:
        user = OtpStore.find_by_nama_pengguna(nama_pengguna)
        randotp = user.otp
    except:
        response_object = {
            'status': 'fail',
            'message': 'Nama Penggunna yang salah',
        }
        return response_object, 409
    
    if int(user_otp) == int(randotp):
        try:
            name = user.name
            email = user.email
            password = user.psswd
            updated_user = MasterUser(
                nama=name, no_kad_pengenalan=nama_pengguna, nama_pengguna=nama_pengguna, alamat_emel=email, kata_laluan=password, lock_time=lock_time, user_type=user_type,  role=role)
                # nama=name, no_kad_pengenalan=nama_pengguna, nama_pengguna=nama_pengguna, alamat_emel=email, password=password, lock_time=lock_time, user_type=user_type,  role=role)
            db.session.add(updated_user)
            OtpStore.query.filter(OtpStore.nama_pengguna == nama_pengguna).delete()
            db.session.commit()
            logger.info("User Registered")
            response = {
                'status': 'success',
                'message': 'user_added'
            }
            return response, 201
        except:
            logger.exception("User not registered")
            response_object = {
                'status': 'fail',
                'message': 'user_not_added',
            }
            return response_object, 409

    else:
        response_object = {
            'status': 'fail',
            'message': 'otp_invalid',
        }
        return response_object, 409

""" ===============================<< Registration of new user ends >>=============================== """
""" ===============================<< User login process starts >>=============================== """

def login(data):
    nama_pengguna = data.nama_pengguna.upper()
    password = data.password
    user = MasterUser.find_by_nama_pengguna(nama_pengguna)

    logging.info("By pass login.")
    if user:
        access_token = user.encode_access_token()
        logger.info("Logged in Successfully.")
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        nama = user.nama.upper()
        user_type = user.user_type
        role = user.role
        parlimen = user.parlimen
        zon = user.zon
        
        statement = "Log masuk berjaya."
        log_info = LogPengguna(id_pengguna=user.no_kad_pengenalan, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        
        return _create_auth_successful_response(
            token=access_token.decode(),
            status_code=HTTPStatus.OK,
            message="login_success",
            user=nama,
            user_type=user_type,
            role=role,
            parlimen=parlimen,
            zon=zon
        )

    if not user:
        logger.debug("Invalid Credential")
        abort(HTTPStatus.UNAUTHORIZED,"invalid_cred", status="fail")
    # elif not user.check_password(password)
    elif not MasterUser.find_by_kata_laluan(nama_pengguna, password):
        logger.debug("Invalid Credential")
        abort(HTTPStatus.UNAUTHORIZED,"invalid_cred", status="fail")
        
    elif user.user_type == 'admin' or user.user_type=='dbkl' or user.user_type=='SuperAdmin' and user.active==1:
        access_token = user.encode_access_token()
        logger.info("Logged in Successfully.")
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        nama = user.nama.upper()
        user_type = user.user_type
        role = user.role
        parlimen = user.parlimen
        zon = user.zon
        
        statement = "Log masuk berjaya."
        log_info = LogPengguna(id_pengguna=user.no_kad_pengenalan, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        
        return _create_auth_successful_response(
            token=access_token.decode(),
            status_code=HTTPStatus.OK,
            message="login_success",
            user=nama,
            user_type=user_type,
            role=role,
            parlimen=parlimen,
            zon=zon
        )
        
    else:
        response_object = {
            'status': 'fail',
            'message': 'invalid_cred',
        }
        return response_object, 403
        
def _create_auth_successful_response(token, status_code, message, user, user_type, role, parlimen, zon):
    response = jsonify(
        status="success",
        message=message,
        access_token=token,
        token_type="bearer",
        expires_in=_get_token_expire_time(),
        user=user,
        user_type=user_type,
        role=role,
        parlimen=parlimen,
        zon=zon
    )
    response.status_code = status_code
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response

def _get_token_expire_time():
    token_age_h = current_app.config.get("TOKEN_EXPIRE_HOURS")
    token_age_m = current_app.config.get("TOKEN_EXPIRE_MINUTES")
    expires_in_seconds = token_age_h * 3600 + token_age_m * 60
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
""" ===============================<< Get Profile Information starts >>=============================== """
@token_required
def getProfileInformation():
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        username = user.nama_pengguna
        name = user.nama
        user_type = user.user_type
        role = user.role
        email = user.alamat_emel
        parlimen = user.parlimen
        zon = user.zon
        log_list = []
        for logs in LogPengguna.query.filter_by(id_pengguna=id_card_no).order_by(desc(LogPengguna.tarikh)):
            log_list.append({
                'id_card_no': id_card_no,
                'username': username,
                'name': name,
                'role': role,
                'email': email,
                'parlimen': parlimen,
                'zon': zon,
                'time': logs.tarikh,
                'action': logs.aktiviti,
            })
        logger.info("Profile Information fetched.")
        return jsonify(log_list)
    except:
        logger.exception("Profile Information Could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Profile Information Could not be fetched"
        }
""" ===============================<< Get Profile Information ends >>=============================== """
""" ===============================<< Change password starts >>=============================== """

@token_required
def changePassword(data):
    new_password = data.new_password
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type
        role = user.role
        user.kata_laluan = new_password
        
        statement = "Kata laluan berjaya diubah."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        
        response_object = {
            "status": "success",
            "message": "Password changed successfully.",
        }
        logger.info("Password changed successfully.")
        return response_object, 200
    except:
        logger.exception("Password could not be changed")
        response_object = {
            "status": "fail",
            "message": "Password could not be changed"
        }
        return response_object, 400

""" ===============================<< Change password ends >>=============================== """
""" ===============================<< User logout process starts >>=============================== """

@token_required
def logout():
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
        
    statement = "Log keluar berjaya."
    log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
    db.session.add(log_info)
    db.session.commit()
    
    access_token = logout.token
    expires_at = logout.expires_at
    blacklisted_token = BlacklistedToken(access_token, expires_at)
    db.session.add(blacklisted_token)
    db.session.commit()
    response_dict = dict(status="success", message="Successfully Logged Out")
    return response_dict, HTTPStatus.OK

""" ===============================<< User logout process ends >>=============================== """
""" ===============================<< Forgot password starts >>=============================== """

def forgotPassword(data):
    id_card_no = data.nama_pengguna.upper()
    if MasterUser.find_by_id_card(id_card_no):
        reset_password_token = secrets.token_hex(20)
        user = MasterUser.find_by_id_card(id_card_no)
        user.reset_password_token = reset_password_token
        db.session.commit()
        email = user.alamat_emel
        lang = data.lang
        return make_forgot_mail(id_card_no, email,lang, reset_password_token)
    
    elif MasterUser.find_by_email(id_card_no):
        reset_password_token = secrets.token_hex(20)
        user = MasterUser.find_by_email(id_card_no)
        user.reset_password_token = reset_password_token
        db.session.commit()
        email = id_card_no
        lang = data.lang
        return make_forgot_mail(id_card_no, email, lang, reset_password_token)
    
    else:
        logger.debug("Email or Nama Pengguna Present")
        response_object = {
            'status': 'fail',
            'message': 'user_not_found'
        }
        return response_object, 400

def make_forgot_mail(id_card_no, email, lang, reset_password_token):
    id_card_no = id_card_no
    TO_EMAIL = email
    message = MIMEMultipart()
    message['From'] = FROM_EMAIL
    message['To'] = TO_EMAIL
    message['Subject'] = 'JKAS Tetapkan Semula Kata Laluan'
    MAIL_CONTENT = f'''
    Salam Sejahtera,
    
    Sila klik pautan di bawah untuk menetapkan semula kata laluan anda.
    {UI_URL}/{lang}/dbkl/resetpassword?token={reset_password_token}
    
    
    Jabatan Kesihatan dan Alam Sekitar
    '''
    if send_email(FROM_EMAIL, TO_EMAIL, 'JKAS - Tetapan Semula Kata Laluan', MAIL_CONTENT):
        logger.info("Mail Sent with reset password token")
        response_object = {
            'status': 'success',
            'message': 'reset_pwd_mail_sent'
            }
        return response_object, 200
    logger.exception("could not be sent mail")
    response_object = {
        'status': 'fail',
        'message': 'Can not sent reset pasword link'
    }
    return response_object, 400

""" ===============================<< Forgot password ends >>===============================  """
""" ===============================<< Reset password starts >>===============================  """

def resetPassword(data):
    token = data.token
    password = data.password
    try:
        new_user = db.session.query(MasterUser).filter_by(reset_password_token=token).one()
    except:
        logger.exception('No user found with the reset password token')
        response_object = {
            'status': 'fail',
            'message': 'No user found with the reset password token !'
        }
        return response_object, 400
    if new_user:
        try:
            new_user.kata_laluan = password
            new_user.reset_password_token = ''
            db.session.commit()
            logger.info("Password reset Successfull")
            response_object = {
                'status': 'success',
                'message': 'password_updated'
            }
            logger.info("Password Updated")
            return response_object, 201
        except:
            logger.exception("Password Update Failed")
            response_object = {
                'status': 'fail',
                'message': 'password_not_updated'
            }
            return response_object, 400
    
    
""" ===============================<< Reset password ends >>===============================  """
""" ===============================<< Role Assign Starts >>=============================== """

@token_required
def assignRole(data):
    no_kad_pengenalan = data.id_card_number
    parlimen = data.parlimen
    role = data.role
    user = get_logged_in_user()
    if user.user_type == 'admin' or user.user_type == 'SuperAdmin':
        try:
            exists = db.session.query(MasterUser).filter_by(no_kad_pengenalan=no_kad_pengenalan)
            if exists:
                master_user_obj = MasterUser.query.filter_by(no_kad_pengenalan=no_kad_pengenalan).first()
                if role == 'Orang Awam': 
                    master_user_obj.user_type = 'public'
                elif role == 'Superadmin': 
                    master_user_obj.user_type = 'SuperAdmin'
                elif role == 'Agensi':
                    master_user_obj.user_type = 'agenci'
                else: 
                    master_user_obj.user_type = 'dbkl'
                master_user_obj.role = role
                master_user_obj.parlimen = parlimen
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
""" ===============================<<Fetch jumlah kawasan perkhidmatan starts >>=============================== """ 
def getJumlahKawasanPerkhidmatan():
    dummy_value = 258
    return jsonify(dummy_value)
""" ===============================<<Fetch jumlah kawasan perkhidmatan ends >>=============================== """  
""" ===============================<<Fetch jumlah permis starts >>=============================== """ 
def getJumlahPermis():
    dummy_value = 1603
    return jsonify(dummy_value)
""" ===============================<<Fetch jumlah permis ends >>=============================== """ 
""" ===============================<<Fetch jumlah pembersihan awam starts >>=============================== """ 
def getJumlahPembersihanAwam():
    dummy_value = 11018
    return jsonify(dummy_value)
""" ===============================<<Fetch jumlah pembersihan awam ends >>=============================== """ 
""" ===============================<<Fetch jumlah kutipan sampah starts >>=============================== """ 
def getJumlahKutipanSampah():
    dummy_value = 2169
    return jsonify(dummy_value)
""" ===============================<<Fetch jumlah kutipan sampah ends >>=============================== """
""" ===============================<< Update Meeting Starts >>=============================== """
@token_required
def updateMeeting(no_siri_permohonan,data):
    tarikh=data.tarikh
    masa=data.masa
    tempat=data.tempat
    # app_tarikh = tarikh.strftime("%Y-%m-%d")
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type
        role = user.role
        exists = db.session.query(MeetingArea).filter_by(no_siri_permohonan=no_siri_permohonan).first() is not None
        if exists:
            meeting_area_obj = MeetingArea.query.filter_by(no_siri_permohonan=no_siri_permohonan, active=1).first()
            meeting_area_obj.tarikh = tarikh
            meeting_area_obj.masa = masa
            meeting_area_obj.tempat = tempat
            meeting_area_obj.updated_date = today
            meeting_area_obj.updated_by = id_card_no
            db.session.commit()

            # applicationList_obj = db.session.query(PublicApplicationList).filter_by(no_siri_permohonan=no_siri_permohonan).first()
            # applicationList_obj.mesyuarat_permohanan_serahan_kawasan= f"{app_tarikh}, {masa}, {tempat}"
            # db.session.commit()
            statement = f"Mesyuarat untuk {no_siri_permohonan} berjaya dikemas kini"
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info(f"Meeting for {no_siri_permohonan} updated successfully")
            response_object = {
                'status': 'success',
                'message': 'meeting_updated',
            }
            return response_object, 201
        else:
            new_meeting = MeetingArea(no_siri_permohonan=no_siri_permohonan,tarikh=tarikh,masa=masa,tempat=tempat,inserted_date=today,inserted_by=id_card_no,active=1)
            db.session.add(new_meeting)
            db.session.commit()

            statement = f"Makan baru untuk {no_siri_permohonan} berjaya ditambahkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info(f"New meeting for {no_siri_permohonan} added successfully")
            response = {
                'status':'success',
                'message': 'meeting_uadded'
            }
            return response, 201
        
    except:
        logger.exception("meeting not updated.")
        response = {
            'status':'fail',
            'message':'meeting_not_updated.'
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
        logger.info("List of meeting fetched")
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
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    meeting_id_list = data.meeting_id_list.split(",")
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin':
            for i in meeting_id_list:
                if MeetingArea.query.filter_by(id=i).first():
                    MeetingArea.query.filter_by(id=i).first().active = 0
                
            db.session.commit()
            
            statement = "Senarai borang mesyuarat berjaya dipadamkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Meeting id list Deleted successfully")

            response_object = {
                "status": "success",
                "message": "meeting_deleted"
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 

    except:
        logger.exception("Meeting id list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "meeting_not_deleted"
        }
        return response_object, 400

""" ===============================<< Delete List Of Meeting Ends >>=============================== """
""" ===============================<< Get Committee List starts >>=============================== """
def getCommitteeList():
    try:
        committee = EMeeting.query.with_entities(EMeeting.jenis_jawatankuasa).distinct().all()
        committee_list = list(itertools.chain(*committee))
        logger.info("Committee List fetched")
        return committee_list
    except:
        logger.exception("Committee List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Committee List could not be fetched"
        }

""" ===============================<< Get Committee List ends >>=============================== """
""" ===============================<< Get Department List starts >>=============================== """
def getDepartmentList():
    try:
        department = EMeeting.query.with_entities(EMeeting.jabatan_terlibat).distinct().all()
        department_list = list(itertools.chain(*department))
        logger.info("Department List fetched")
        return department_list
    except:
        logger.exception("Department List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Department List could not be fetched"
        }
        
""" ===============================<< Get Department List ends >>=============================== """
""" ===============================<< Add Detailed Meeting Starts >>=============================== """
@token_required
def addDetailedMeeting(data):
    jenis_jawatankuasa = data.jenis_jawatankuasa
    jenis_mesyuarat = data.jenis_mesyuarat
    jabatan_terlibat = data.jabatan_terlibat
    tarikh_mesyuarat = data.tarikh_mesyuarat
    masa_mesyuarat = data.masa_mesyuarat
    hingga = data.hingga
    pengerusi = data.pengerusi
    bill_mesyuarat = data.bill_mesyuarat
    tajuk_mesyuarat = data.tajuk_mesyuarat
    setiausaha = data.setiausaha
    tempat_mesyuarat = data.tempat_mesyuarat
    agenda_dan_minit = data.agenda_dan_minit
    meeting_dokumen = data.meeting_dokumen
    if meeting_dokumen:
        meeting_dokumen = re.sub('[^a-zA-Z0-9.]', '', meeting_dokumen)
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type
        role = user.role
        newEMeeting = EMeeting(jenis_jawatankuasa=jenis_jawatankuasa,jenis_mesyuarat=jenis_mesyuarat,jabatan_terlibat=jabatan_terlibat,
                                             tarikh_mesyuarat=tarikh_mesyuarat,masa_mesyuarat=masa_mesyuarat,hingga=hingga,pengerusi=pengerusi,bill_mesyuarat=bill_mesyuarat,
                                            tajuk_mesyuarat=tajuk_mesyuarat,setiausaha=setiausaha,tempat_mesyuarat=tempat_mesyuarat,agenda_dan_minit=agenda_dan_minit,meeting_dokumen=meeting_dokumen,
                                            inserted_by=id_card_no,inserted_date=now,active=1)
        db.session.add(newEMeeting)
        db.session.commit()
        
        statement = "Borang mesyuarat terperinci baru berjaya ditambahkan."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()

        response_object = {
            'status':'success',
            'message':'detailed_meeting_added.'
        }
        logger.info("Detailed Meeting Form Added.")
        return response_object, 201
    except:
        logger.exception("Detailed Meeting Form Not Added.")
        response_object = {
            'status':'fail',
            'message':'detailed_meeting_not_added'
        }
        return response_object, 409

""" ===============================<< Add Detailed Meeting Ends >>=============================== """
""" ===============================<< List Of Detailed Meeting Starts >>=============================== """
@token_required
def listOfDetailedMeeting(data):
    jenis_mesyuarat = data.jenis_mesyuarat
    jawatankuasa_mesurat = data.jawatankuasa_mesurat
    if EMeeting.query.filter_by(jenis_mesyuarat=jenis_mesyuarat,jenis_jawatankuasa=jawatankuasa_mesurat,active=1).first() == None:
        abort(HTTPStatus.NOT_FOUND, f"No Meeting Details Found with jenis_mesyuarat : {jenis_mesyuarat} and jawatankuasa_mesurat : {jawatankuasa_mesurat}")
    try:
        meeting_info=[]
        for meeting_details in EMeeting.query.filter_by(jenis_mesyuarat=jenis_mesyuarat, jenis_jawatankuasa=jawatankuasa_mesurat, active=1).order_by(desc(EMeeting.inserted_date)):
            meeting_info.append({
                "detailed_meeting_id" : meeting_details.e_meeting_id,
                "tajuk_mesyuarat" : meeting_details.tajuk_mesyuarat,
                "jenis_mesyuarat" : meeting_details.jenis_mesyuarat,
                "jawatankuasa_mesurat" : meeting_details.jenis_jawatankuasa,
                "tarikh_mesyuarat" : meeting_details.tarikh_mesyuarat,
                "masa_mesyuarat" : meeting_details.masa_mesyuarat
            })
        logger.info("List of detailed meeting fetched")
        return jsonify(meeting_info)
    except:
        logger.exception("list of detailed meeting not fetched")
        response_object = {
            'status':'fail',
            'message':'list of detailed meeting not fetched'
        }
        return response_object, 409
    
""" ===============================<< List Of Detailed Meeting Ends >>=============================== """
""" ===============================<< getAllDetailedMeeting Starts >>=============================== """
@token_required
def getAllDetailedMeeting():
    try:
        meeting_info=[]
        for meeting_details in DetailedMeeting.query.filter_by(active=1).order_by(desc(DetailedMeeting.inserted_date)):
            meeting_info.append({
                "detailed_meeting_id" : meeting_details.detailed_meeting_id,
                "no_siri_permohonan" : meeting_details.no_siri_permohonan,
                "tarikh_mesyuarat" : meeting_details.tarikh_mesyuarat,
                "masa_mesyuarat" : meeting_details.masa_mesyuarat,
                "tempat_mesyuarat" : meeting_details.tempat_mesyuarat,
            })
        logger.info("List of all detailed meeting fetched")
        return jsonify(meeting_info)
    except:
        logger.exception("list of all detailed meeting not fetched")
        response_object = {
            'status':'fail',
            'message':'list of all detailed meeting not fetched'
        }
        return response_object, 409
    
""" ===============================<< getAllDetailedMeeting Ends >>=============================== """
""" ===============================<< Get Detailed Meeting Starts >>=============================== """
@token_required
def getDetailedMeeting(detailed_meeting_id):
   
    if EMeeting.query.filter_by(e_meeting_id=detailed_meeting_id,active=1).first() == None:
        abort(HTTPStatus.NOT_FOUND, f"No Meeting Details Found with detailed_meeting_id : {detailed_meeting_id}")
    try:
        meeting_info=[]
        for meeting_details in EMeeting.query.filter_by(e_meeting_id=detailed_meeting_id, active=1):
            meeting_info.append({
                "detailed_meeting_id" : meeting_details.e_meeting_id,
                "jawatankuasa_mesurat" : meeting_details.jenis_jawatankuasa,
                "jenis_mesyuarat" : meeting_details.jenis_mesyuarat,
                "jabatan_terlibat" : meeting_details.jabatan_terlibat,
                "tarikh_mesyuarat" : meeting_details.tarikh_mesyuarat,
                "masa_mesyuarat" : meeting_details.masa_mesyuarat,
                "hingga" : meeting_details.hingga,
                "pengerusi" : meeting_details.pengerusi,
                "bill_mesyuarat" : meeting_details.bill_mesyuarat,
                "tajuk_mesyuarat" : meeting_details.tajuk_mesyuarat,
                "setiausaha" : meeting_details.setiausaha,
                "tempat_mesyuarat" : meeting_details.tempat_mesyuarat,
                "agenda_dan_minit" : meeting_details.agenda_dan_minit,
                "meeting_dokumen" : meeting_details.meeting_dokumen
            })
        logger.info("Detailed meeting fetched")
        return jsonify(meeting_info)
    except:
        logger.exception("Detailed meeting not fetched")
        response_object = {
            'status':'fail',
            'message':'Detailed meeting not fetched'
        }
        return response_object, 409
    
""" ===============================<< Get Detailed Meeting Ends >>=============================== """
""" ===============================<< Update Detailed Meeting Starts >>=============================== """
@token_required
def updateEMeeting(detailed_meeting_id, data):
    try:
        detailed_meeting_area_obj = db.session.query(EMeeting).filter_by(e_meeting_id=detailed_meeting_id, active=1).first()
    except:
        logger.exception("Detaile Meeting Form Not Found")
        response_object = {
            'status':'fail',
            'message':'Detailed Meeting Form not Found'
        }
        return response_object, 404
        
    if detailed_meeting_area_obj:
        try:
            user = get_logged_in_user()
            id_card_no = user.no_kad_pengenalan
            today = date.today()
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            user_type = user.user_type
            role = user.role
            
            detailed_meeting_area_obj.jenis_jawatankuasa = data.jenis_jawatankuasa
            detailed_meeting_area_obj.jenis_mesyuarat = data.jenis_mesyuarat
            detailed_meeting_area_obj.jenis_jawatankuasa = data.jenis_jawatankuasa
            detailed_meeting_area_obj.tarikh_mesyuarat = data.tarikh_mesyuarat
            detailed_meeting_area_obj.masa_mesyuarat = data.masa_mesyuarat
            detailed_meeting_area_obj.hingga = data.hingga
            detailed_meeting_area_obj.pengerusi = data.pengerusi
            detailed_meeting_area_obj.bill_mesyuarat = data.bill_mesyuarat
            detailed_meeting_area_obj.tajuk_mesyuarat = data.tajuk_mesyuarat
            detailed_meeting_area_obj.setiausaha = data.setiausaha
            detailed_meeting_area_obj.tempat_mesyuarat = data.tempat_mesyuarat
            detailed_meeting_area_obj.agenda_dan_minit = data.agenda_dan_minit
            meeting_dokumen = data.meeting_dokumen
            if meeting_dokumen:
                meeting_dokumen = re.sub('[^a-zA-Z0-9.]', '', meeting_dokumen)
                detailed_meeting_area_obj.meeting_dokumen=meeting_dokumen
            else:    
                detailed_meeting_area_obj.meeting_dokumen = detailed_meeting_area_obj.meeting_dokumen
            detailed_meeting_area_obj.updated_by = id_card_no
            detailed_meeting_area_obj.updated_date = today
            db.session.commit()
            
            statement = "Borang mesyuarat terperinci berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'detailed_meeting_updated',
            }
            logger.info("Detailed Meeting Form Updated")
            return response_object, 201
        except:
            logger.exception("Detailed Meeting Form not Updated")
            response_object = {
                'status':'fail',
                'message':'detailed_meeting_not_updated'
            }
            return response_object, 409
    else:
        response_object = {
            'status':'fail',
            'message':'Detailed Meeting Form not Found'
        }
        return response_object, 404
    
""" ===============================<< Update Detailed Meeting Ends >>=============================== """
""" ===============================<< Update Detailed Meeting Starts >>=============================== """
@token_required
def updateDetailedMeeting(detailed_meeting_id, data):
    try:
        detailed_meeting_area_obj = db.session.query(DetailedMeeting).filter_by(detailed_meeting_id=detailed_meeting_id, active=1).first()
    except:
        logger.exception("Detaile Meeting Form Not Found")
        response_object = {
            'status':'fail',
            'message':'Detailed Meeting Form not Found'
        }
        return response_object, 404
        
    if detailed_meeting_area_obj:
        try:
            no_siri_permohonan = detailed_meeting_area_obj.no_siri_permohonan
            user = get_logged_in_user()
            id_card_no = user.no_kad_pengenalan
            today = date.today()
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            user_type = user.user_type
            role = user.role

            detailed_meeting_area_obj.tarikh_mesyuarat = data.tarikh_mesyuarat
            detailed_meeting_area_obj.masa_mesyuarat = data.masa_mesyuarat
            detailed_meeting_area_obj.tempat_mesyuarat = data.tempat_mesyuarat
            detailed_meeting_area_obj.updated_by = id_card_no
            detailed_meeting_area_obj.updated_date = today
            db.session.commit()
            
            applicationList_obj = db.session.query(PublicApplicationList).filter_by(no_siri_permohonan=no_siri_permohonan).first()
            applicationList_obj.mesyuarat_permohanan_serahan_kawasan= f"{data.tarikh_mesyuarat}, {data.masa_mesyuarat}, {data.tempat_mesyuarat}"
            db.session.commit()
            statement = "Borang mesyuarat terperinci berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'detailed_meeting_updated',
            }
            logger.info("Detailed Meeting Form Updated")
            return response_object, 201
        except:
            logger.exception("Detailed Meeting Form not Updated")
            response_object = {
                'status':'fail',
                'message':'detailed_meeting_not_updated'
            }
            return response_object, 409
    else:
        response_object = {
            'status':'fail',
            'message':'Detailed Meeting Form not Found'
        }
        return response_object, 404
    
""" ===============================<< Update Detailed Meeting Ends >>=============================== """
""" ===============================<< Get Inventori Pengguna Starts >>=============================== """
@token_required
def getInventoriPengguna():
    user = get_logged_in_user()
    nama_pengguna = user.nama_pengguna
    try:
        if user.role == 'Superadmin' or user.role == 'Admin' or user.role == 'Pentadbir':
            inventori_pengguna_res=[]
            for inventori_pengguna in MasterUser.query.filter(MasterUser.active==1, MasterUser.role != 'Superadmin').order_by(desc(MasterUser.id)).all():
                inventori_pengguna_res.append({
                    "inventori_pengguna_id" : inventori_pengguna.id,
                    "nama_pengguna" : inventori_pengguna.nama,
                    "id_pengguna" : inventori_pengguna.no_kad_pengenalan,
                    "kata_laluan": inventori_pengguna.kata_laluan,
                    "peranan" : inventori_pengguna.role,
                })
            logger.info("Inventori pengguna fetched")
            return inventori_pengguna_res
        else:
            response_object = {
            'status':'fail',
            'message': f'User {nama_pengguna} do not have permission to view this page'
            }
            return response_object, 403
    except:
        logger.exception("inventori pengguna not fetched")
        response_object = {
            'status':'fail',
            'message':'inventori pengguna not fetched'
        }
        return response_object, 409
""" ===============================<< Get Inventori Pengguna Ends >>=============================== """
""" ===============================<< Get Inventori Pengguna By Id Starts >>=============================== """ 
@token_required
def getInventoriPenggunaById(id_pengguna):
    user = get_logged_in_user()
    nama_pengguna = user.nama_pengguna
    if user.role == 'Superadmin' or user.role == 'Pentadbir' or user.role == 'Admin':
        try:
            exists = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_pengguna, active=1).first()
        except:
            logger.exception("inventori pengguna not fetched.")
            response_object = {
                'status':'fail',
                'message':'inventori pengguna not fetched.'
            }
            return response_object, 409
        if exists:
            inventori_pengguna_res = []
            for inventori_pengguna in MasterUser.query.filter_by(no_kad_pengenalan=id_pengguna, active=1):
                nama = inventori_pengguna.nama
                nama = nama.upper()
                inventori_pengguna_res.append({
                    "nama_pengguna" : nama,
                    "id_pengguna" : inventori_pengguna.no_kad_pengenalan,
                    "peranan" : inventori_pengguna.role,
                    "parlimen": inventori_pengguna.parlimen
                })
            logger.info("Inventori pengguna fetched")
            return inventori_pengguna_res
        else:
            response_object = {
                'status':'fail',
                'message':'inventori pengguna not fetched.'
            }
            return response_object, 409
    else:
        response_object = {
            'status':'fail',
            'message': f'User {nama_pengguna} do not have permission to view this page'
        }
        return response_object, 403
        
""" ===============================<< Get Inventori Pengguna By Id Ends >>=============================== """ 
""" ===============================<< Update Inventori Pengguna Starts >>=============================== """ 
@token_required
def updateInventoriPengguna(id_pengguna,data):
    nama_pengguna=data.nama_pengguna
    peranan=data.peranan
    parlimen=data.parlimen
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    if user.role == 'Superadmin' or user.role == 'Pentadbir' or user.role == 'Admin':
        try:
            inventori_pengguna_obj = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_pengguna, active=1).first()
        except:
            logger.exception('Inventori Data not found with the Inventori data')
            response_object = {
                "status": "fail",
                "message": "Inventori Data not found with the Inventori data"
            }
            return response_object, 404
        if inventori_pengguna_obj:
            try:
                inventori_pengguna_obj.nama = nama_pengguna
                inventori_pengguna_obj.updated_date = today
                inventori_pengguna_obj.updated_by = id_card_no
                inventori_pengguna_obj.role = peranan
                inventori_pengguna_obj.parlimen = parlimen
                if peranan == 'Orang Awam': 
                    inventori_pengguna_obj.user_type = 'public'
                elif peranan == 'Superadmin': 
                    inventori_pengguna_obj.user_type = 'SuperAdmin'
                elif peranan == 'Agensi':
                    inventori_pengguna_obj.user_type = 'agenci'
                else: 
                    inventori_pengguna_obj.user_type = 'dbkl'
                db.session.commit()
                
                statement = f"Inventori pengguna : {id_pengguna} berjaya dikemas kini."
                log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
                db.session.add(log_info)
                db.session.commit()

                response_object = {
                    'status':'success',
                    'message': 'inventori_pengguna_updated'
                }
                logger.info(f"Inventori pengguna : {id_pengguna} updated successfully")
                return response_object, 201
            except:
                logger.exception("inventori pengguna not updated.")
                response_object = {
                    'status':'fail',
                    'message':'inventori_pengguna_not_updated.'
                }
                return response_object, 409
        else:
            response_object = {
                "status": "fail",
                "message": "Inventori Data not found with the Inventori data"
            }
            return response_object, 404
    else:
        response_object = {
            'status':'fail',
            'message': 'not_authorized'
        }
        return response_object, 403

""" ===============================<< Update Inventori Pengguna Ends >>=============================== """ 
""" ===============================<< Delete Inventori Pengguna Starts >>=============================== """
@token_required
def deleteInventoriPengguna(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    id_pengguna_list = data.id_pengguna_list.split(",")
    try:
        if role and role.strip().lower() == 'superadmin':
            for i in id_pengguna_list:
                if MasterUser.query.filter_by(id=i).first():
                    MasterUser.query.filter_by(id=i).first().active = 0
            
            db.session.commit()
            
            statement = "Senarai pengguna inventori berjaya dipadam."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Inventori Pengguna List Deleted successfully")

            response_object = {
                "status": "success",
                "message": "inventori_pengguna_deleted"
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 
            return response_object, 403
    except:
        logger.exception("Inventori Pengguna list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "inventori_pengguna_not_deleted"
        }
        return response_object, 400

""" ===============================<< Delete Inventori Pengguna Ends >>=============================== """   
""" ===============================<< Get LogPengguna Pengguna Starts >>=============================== """
@token_required
def getLogPengguna():
    user = get_logged_in_user()
    nama_pengguna = user.nama_pengguna
    try:
        if user.role == 'Superadmin' or user.role == 'Admin' or user.role == 'Pentadbir':
            log_pengguna_obj = LogPengguna.query.filter_by(active=1).order_by(desc(LogPengguna.tarikh)).all()
            log_pengguna_res=[]
            for log_pengguna in log_pengguna_obj:
                log_pengguna_res.append({
                    "id_pengguna" : log_pengguna.id_pengguna,
                    "tarikh" : log_pengguna.tarikh,
                    "aktiviti" : log_pengguna.aktiviti,
                    "user_type" : log_pengguna.user_type,
                    "role" : log_pengguna.role,
                })
            logger.info("Log pengguna fetched")
            return jsonify(log_pengguna_res)
        else:
            response_object = {
            'status':'fail',
            'message': f'User {nama_pengguna} do not have permission to view this page'
        }
        return response_object, 403
    except:
        logger.exception("log pengguna not fetched")
        response_object = {
            'status':'fail',
            'message':'log pengguna not fetched'
        }
        return response_object, 409
""" ===============================<< Get LogPengguna Pengguna Ends >>=============================== """
""" ===============================<< Get Application List Starts >>=============================== """  
@token_required
def getPublicApplicationList():
    try:
        application_list_obj = PublicApplicationList.query.order_by(desc(PublicApplicationList.application_id)).all()
        application_list_res = []
        for app in application_list_obj:
            meeting_detail_obj = db.session.query(DetailedMeeting).filter_by(no_siri_permohonan=app.no_siri_permohonan).all()
            tetepan_mesyuarat = {}
            if meeting_detail_obj != []:
                for each_meeting in meeting_detail_obj:
                    tetepan_mesyuarat['tarikh'] = each_meeting.tarikh_mesyuarat
                    tetepan_mesyuarat['masa'] = each_meeting.masa_mesyuarat
                    tetepan_mesyuarat['tempat'] = each_meeting.tempat_mesyuarat
            application_list_res.append({
                "application_id": app.application_id,
                "no_siri_permohonan": app.no_siri_permohonan,
                "tarikh_permohonan" : app.tarikh_permohonan,
                "dokumen_senarai"   : app.dokumen_senarai,
                "status_semakan_dokumen": app.status_semakan_dokumen, 
                "tetepan_mesyuarat": tetepan_mesyuarat, 
                "surat_penyerahan_kawasan" : app.surat_penyerahan_kawasan,
                "text" : app.text,
                "active" : app.active,
            })
        logger.info("Application list fetched")            
        return jsonify(application_list_res)
    except:
        logger.exception("Application list not fetched")
        response_object = {
            'status':'fail',
            'message':'Application list not fetched.'
        }
        return response_object, 409


""" ===============================<< Get Application List Ends >>=============================== """
""" ===============================<< Get Application List 2 Starts >>=============================== """  
@token_required
def getPublicApplicationList2():
    try:
        application_list_obj = PublicApplicationList.query.order_by(desc(PublicApplicationList.inserted_date)).all()
        application_list_res = []
        for app in application_list_obj:
            site_visit_info_arr = db.session.query(PublicSiteVisitInfo).filter_by(no_siri_permohonan=app.no_siri_permohonan).all()
            site_visit_info_obj = {}
            if site_visit_info_arr != []:
                for site_info in site_visit_info_arr:
                    site_visit_info_obj['site_id'] = site_info.site_id
                    site_visit_info_obj['tarikh'] = site_info.tarikh
                    site_visit_info_obj['tarikh_datetime'] = site_info.tarikh_datetime
                    site_visit_info_obj['tarikh_lawatan_tapak'] = site_info.tarikh_lawatan_tapak
                    site_visit_info_obj['keputusan_lawatan_tapak'] = site_info.keputusan_lawatan_tapak,
                    site_visit_info_obj['keputusan_lawatan_tapak_filename'] = site_info.keputusan_lawatan_tapak_filename,
                    site_visit_info_obj['maklum_balas_ketidakpatuhan'] = site_info.maklum_balas_ketidakpatuhan
                    site_visit_info_obj['tetapan_lawatan_tapak_filename'] = site_info.tetapan_lawatan_tapak_filename

            application_list_res.append({
                "application_id": app.application_id,
                "no_siri_permohonan": app.no_siri_permohonan,
                "tarikh_permohonan" : app.tarikh_permohonan,
                # "dokumen_senarai"   : app.dokumen_senarai,
                "status_semakan_dokumen": app.status_semakan_dokumen, 
                "site_visit_info": site_visit_info_obj, 
                # "surat_penyerahan_kawasan" : app.surat_penyerahan_kawasan,
                "status_keputusan_permohonan": app.status_keputusan_permohonan,
                "tarikh_keputusan_permohonan": app.tarikh_keputusan_permohonan,
                "catatan" : app.text,
                "active" : app.active,
            })
        logger.info("Application list fetched")            
        return jsonify(application_list_res)
    except:
        logger.exception("Application list not fetched")
        response_object = {
            'status':'fail',
            'message':'Application list not fetched.'
        }
        return response_object, 409


""" ===============================<< Get Application List 2 Ends >>=============================== """
""" ===============================<< Update Application List Starts >>=============================== """  
@token_required
def updateApplicationList(no_siri_permohonan, data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type 
    role = user.role
    
    status_semakan_dokumen = data.status_semakan_dokumen
    catatan = data.catatan
    if user.user_type == 'SuperAdmin':
        try:
            app_list_info = db.session.query(PublicApplicationList).filter_by(no_siri_permohonan=no_siri_permohonan).first()
            app_list_info.status_semakan_dokumen = status_semakan_dokumen
            app_list_info.text = catatan
            
            app_detail_info = db.session.query(PublicApplicationDetails).filter_by(no_siri_permohonan=no_siri_permohonan).first()
            app_detail_info.surat_permohonan_perkhidmatan_pembersihan_status = status_semakan_dokumen
            app_detail_info.surat_salinan_CF_status = status_semakan_dokumen
            app_detail_info.salinan_status_pembanginan_status = status_semakan_dokumen
            app_detail_info.bagi_status_pembangunan_status = status_semakan_dokumen
            app_detail_info.status_dokumen_keseluruhan = status_semakan_dokumen
            app_detail_info.updated_by = id_card_no
            app_detail_info.updated_date = today
            db.session.commit()
            logger.info("Application list updated.")   
            
            statement = f"Permohonan : {no_siri_permohonan} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
              
            response_object = {
                'status':'sucess',
                'message':'application_list_updated'
            }       
            return response_object, 200
        except:
            logger.exception("Application list could not be updated")
            response_object = {
                'status':'fail',
                'message':'application_list_not_updated'
            }
            return response_object, 409
    else:
        response_object = {
            'status':'fail',
            'message':'not_authorized'
        }
        return response_object, 401


""" ===============================<< Update Application List Ends >>=============================== """
""" ===============================<< Update Application Status Details Starts >>=============================== """
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
    surat_permohonan_perkhidmatan_pembersihan_catatan=data.surat_permohonan_perkhidmatan_pembersihan_catatan
    surat_salinan_CF_catatan=data.surat_salinan_CF_catatan
    salinan_status_pembanginan_catatan=data.salinan_status_pembanginan_catatan
    bagi_status_pembangunan_catatan=data.bagi_status_pembangunan_catatan
    status_dokumen_keseluruhan=data.status_dokumen_keseluruhan
    dinyatakan_jenis_sistem=data.dinyatakan_jenis_sistem
    
    try:
        app_details = db.session.query(PublicApplicationDetails).filter_by(no_siri_permohonan=no_siri_permohonan, active=1).first() 
        app_list_info = db.session.query(PublicApplicationList).filter_by(no_siri_permohonan=no_siri_permohonan).first()
        app_list_info.status_semakan_dokumen = status_dokumen_keseluruhan
    except:
        logger.exception('Application Info not found with no siri permohonan')
        response_object = {
                'status': 'fail',
                'message': 'Application Info not found with no siri permohonan',
            }
        return response_object, 404
    if app_details:
        try:
            user = get_logged_in_user()
            id_card_no = user.no_kad_pengenalan
            today = date.today()
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            user_type = user.user_type 
            role = user.role
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
            
            
            surat_permohonan_perkhidmatan_pembersihan_dokumen_temp = data.surat_permohonan_perkhidmatan_pembersihan_dokumen
            if surat_permohonan_perkhidmatan_pembersihan_dokumen_temp:
                surat_permohonan_perkhidmatan_pembersihan_dokumen_list = surat_permohonan_perkhidmatan_pembersihan_dokumen_temp.split(",")
                surat_permohonan_perkhidmatan_pembersihan_dokumen_temp_list = []
                for i in surat_permohonan_perkhidmatan_pembersihan_dokumen_list:
                    #surat_permohonan_perkhidmatan_pembersihan_dokumen_temp = re.sub('[^a-zA-Z0-9.]', '', i)
                    surat_permohonan_perkhidmatan_pembersihan_dokumen_temp_list.append(surat_permohonan_perkhidmatan_pembersihan_dokumen_temp)
                surat_permohonan_perkhidmatan_pembersihan_dokumen_temp = ""
                for i in surat_permohonan_perkhidmatan_pembersihan_dokumen_temp_list:
                    surat_permohonan_perkhidmatan_pembersihan_dokumen_temp += i+','
                app_details.surat_permohonan_perkhidmatan_pembersihan_dokumen = surat_permohonan_perkhidmatan_pembersihan_dokumen_temp[:-1]
                
            else:
                app_details.surat_permohonan_perkhidmatan_pembersihan_dokumen = ""
            
            surat_salinan_CF_dokumen_temp = data.surat_salinan_CF_dokumen
            if surat_salinan_CF_dokumen_temp:
                surat_salinan_CF_dokumen_list = surat_salinan_CF_dokumen_temp.split(",")
                surat_salinan_CF_dokumen_temp_list = []
                for i in surat_salinan_CF_dokumen_list:
                    #surat_salinan_CF_dokumen_temp = re.sub('[^a-zA-Z0-9.]', '', i)
                    surat_salinan_CF_dokumen_temp_list.append(surat_salinan_CF_dokumen_temp)
                surat_salinan_CF_dokumen_temp = ""
                for i in surat_salinan_CF_dokumen_temp_list:
                    surat_salinan_CF_dokumen_temp += i+','
                app_details.surat_salinan_CF_dokumen = surat_salinan_CF_dokumen_temp[:-1]
                
            else:
                app_details.surat_salinan_CF_dokumen = ""
            
            salinan_status_pembanginan_dokumen_temp = data.salinan_status_pembanginan_dokumen
            if salinan_status_pembanginan_dokumen_temp:
                salinan_status_pembanginan_dokumen_list = salinan_status_pembanginan_dokumen_temp.split(",")
                salinan_status_pembanginan_dokumen_temp_list = []
                for i in salinan_status_pembanginan_dokumen_list:
                    #salinan_status_pembanginan_dokumen_temp = re.sub('[^a-zA-Z0-9.]', '', i)
                    salinan_status_pembanginan_dokumen_temp_list.append(salinan_status_pembanginan_dokumen_temp)
                salinan_status_pembanginan_dokumen_temp = ""
                for i in salinan_status_pembanginan_dokumen_temp_list:
                    salinan_status_pembanginan_dokumen_temp += i+','
                app_details.salinan_status_pembanginan_dokumen = salinan_status_pembanginan_dokumen_temp[:-1]
                
            else:
                app_details.salinan_status_pembanginan_dokumen = ""        
            
            bagi_status_pembangunan_dokumen_temp = data.bagi_status_pembangunan_dokumen
            if bagi_status_pembangunan_dokumen_temp:
                bagi_status_pembangunan_dokumen_list = bagi_status_pembangunan_dokumen_temp.split(",")
                bagi_status_pembangunan_dokumen_temp_list = []
                for i in bagi_status_pembangunan_dokumen_list:
                    #bagi_status_pembangunan_dokumen_temp = re.sub('[^a-zA-Z0-9.]', '', i)
                    bagi_status_pembangunan_dokumen_temp_list.append(bagi_status_pembangunan_dokumen_temp)
                bagi_status_pembangunan_dokumen_temp = ""
                for i in bagi_status_pembangunan_dokumen_temp_list:
                    bagi_status_pembangunan_dokumen_temp += i+','
                app_details.bagi_status_pembangunan_dokumen = bagi_status_pembangunan_dokumen_temp[:-1]
                
            else:
                app_details.bagi_status_pembangunan_dokumen = ""
                
            app_details.surat_permohonan_perkhidmatan_pembersihan_status = surat_permohonan_perkhidmatan_pembersihan_status
            app_details.surat_salinan_CF_status = surat_salinan_CF_status
            app_details.salinan_status_pembanginan_status = salinan_status_pembanginan_status
            app_details.bagi_status_pembangunan_status = bagi_status_pembangunan_status
            app_details.surat_permohonan_perkhidmatan_pembersihan_catatan = surat_permohonan_perkhidmatan_pembersihan_catatan
            app_details.surat_salinan_CF_catatan = surat_salinan_CF_catatan
            app_details.salinan_status_pembanginan_catatan = salinan_status_pembanginan_catatan
            app_details.bagi_status_pembangunan_catatan = bagi_status_pembangunan_catatan
            app_details.status_dokumen_keseluruhan = status_dokumen_keseluruhan

            dinyatakan_jenis_sistem_temp = data.dinyatakan_jenis_sistem
            if dinyatakan_jenis_sistem_temp:
                dinyatakan_jenis_sistem_list = dinyatakan_jenis_sistem_temp.split(",")
                dinyatakan_jenis_sistem_temp_list = []
                for i in dinyatakan_jenis_sistem_list:
                    #dinyatakan_jenis_sistem_temp = re.sub('[^a-zA-Z0-9.]', '', i)
                    dinyatakan_jenis_sistem_temp = dinyatakan_jenis_sistem_temp
                    dinyatakan_jenis_sistem_temp_list.append(dinyatakan_jenis_sistem_temp)
                dinyatakan_jenis_sistem_temp = ""
                for i in dinyatakan_jenis_sistem_temp_list:
                    dinyatakan_jenis_sistem_temp += i+','
                app_details.dinyatakan_jenis_sistem = dinyatakan_jenis_sistem_temp[:-1]
                
            else:
                app_details.dinyatakan_jenis_sistem = ""

            app_details.updated_by = id_card_no
            app_details.updated_date = today
            db.session.commit()
            
            statement = f"Permohonan  : {no_siri_permohonan} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info(f"Application : {no_siri_permohonan} updated successfully")
            response_object = {
                'status':'success',
                'message': 'application_updated'
            }
            return response_object, 201
        except:
            logger.exception("Application not updated ")
            response_object = {
                'status':'fail',
                'message':'application_not_updated .'
            }
            return response_object, 409
    else:
        response_object = {
                'status': 'fail',
                'message': 'application Info not found with no siri permohonan',
            }
        return response_object, 404
 
""" ===============================<< Update Application Details Ends >>=============================== """
""" ===============================<< Delete Application List Starts >>=============================== """

@token_required
def deletePublicApplicationList(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    application_id_list = data.application_id_list.split(",")
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin' or user.user_type == 'dbkl':
            for i in application_id_list:
                
                if PublicApplicationList.query.filter_by(application_id=i).first():
                    data = PublicApplicationList.query.filter_by(application_id=i).first()
                    no_siri_permohonan = data.no_siri_permohonan
                    db.session.delete(data)

                if PublicApplicationDetails.query.filter_by(no_siri_permohonan=no_siri_permohonan).first():
                    data = PublicApplicationDetails.query.filter_by(no_siri_permohonan=no_siri_permohonan).first()
                    db.session.delete(data)

            db.session.commit()
            
            statement = f"Senarai aplikasi : {application_id_list} berjaya dipadamkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info(f"Application list : {application_id_list} deleted successfully.")

            response_object = {
                "status": "success",
                "message": "application_list_deleted"
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 

    except:

        logger.exception("Application List could not be deleted")
        response_object = {
            "status": "fail",
            "message": "application_list_not_deleted"
        }
        return response_object, 400

""" ===============================<< Delete Application List Ends >>=============================== """
@token_required
def addTextInPublicApplicationList(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    text = data.text
    application_id = data.application_id
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin':
            if PublicApplicationList.query.filter_by(application_id=application_id).first():
                PublicApplicationList.query.filter_by(application_id=application_id).first().text = text
        
        db.session.commit()
        logger.info(f"Text added successfully.")
        response_object = {
            "status": "success",
            "message": "text_added_successfully"
        }
        return response_object, 200
    except:

        logger.exception("Application List could not be deleted")
        response_object = {
            "status": "fail",
            "message": "application_list_not_undeleted"
        }
        return response_object, 400
""" ===============================<< Undelete Application List Starts >>=============================== """

@token_required
def undeletePublicApplicationList(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    application_id_list = data.application_id_list.split(",")
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin':
            for i in application_id_list:
                
                if PublicApplicationList.query.filter_by(no_siri_permohonan=i).first():
                    PublicApplicationList.query.filter_by(no_siri_permohonan=i).first().active = 1

                if PublicApplicationDetails.query.filter_by(no_siri_permohonan=i).first():
                    PublicApplicationDetails.query.filter_by(no_siri_permohonan=i).first().active = 1

                if PublicSiteVisitInfo.query.filter_by(no_siri_permohonan=i).first():
                    PublicSiteVisitInfo.query.filter_by(no_siri_permohonan=i).first().active = 1
                    
                if NonComplianceForm.query.filter_by(no_siri_permohonan=i).first():
                    NonComplianceForm.query.filter_by(no_siri_permohonan=i).first().active = 1

            db.session.commit()
            
            statement = f"Senarai aplikasi  : {application_id_list} berjaya dibatalkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info(f"Application list : {application_id_list} undeleted successfully.")

            response_object = {
                "status": "success",
                "message": "application_list_undeleted"
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "User is not dbkl."
            } 

    except:

        logger.exception("Application List could not be deleted")
        response_object = {
            "status": "fail",
            "message": "application_list_not_undeleted"
        }
        return response_object, 400

""" ===============================<< Unelete Application List Ends >>=============================== """
""" ===============================<< Fetch Application Details Starts >>=============================== """
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
                    "surat_permohonan_perkhidmatan_pembersihan_catatan": app.surat_permohonan_perkhidmatan_pembersihan_catatan,
                    "surat_salinan_CF_catatan": app.surat_salinan_CF_catatan,
                    "salinan_status_pembanginan_catatan": app.salinan_status_pembanginan_catatan,
                    "bagi_status_pembangunan_catatan": app.bagi_status_pembangunan_catatan, 
                    "status_dokumen_keseluruhan": app.status_dokumen_keseluruhan, 
                    "dinyatakan_jenis_sistem": app.dinyatakan_jenis_sistem,
                    })
            logger.info("Application List Fetched")
            return jsonify(app_list)
        except:
            logger.exception("Application List not fetched")
            response_object = {
                'status': 'fail',
                'message': f'No Application Details found with Serial No. {no_siri_permohonan}',
            }
            return response_object, 404
    else:
        response_object = {
                'status': 'fail',
                'message': f'No Application Details found with Serial No. {no_siri_permohonan}',
            }
        return response_object, 404
   
""" ===============================<< Fetch Application Details Ends >>=============================== """
""" ===============================<< update Status Semakan Dokumen Starts >>=============================== """
@token_required
def updateStatusSemakanDokumen(no_siri_permohonan,data):
    status_semakan_dokumen=data.status_semakan_dokumen
    surat_penyerahan_kawasan = data.surat_penyerahan_kawasan
    
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    try:
        public_application_list_obj = PublicApplicationList.query.filter_by(no_siri_permohonan=no_siri_permohonan, active=1).first()
        
        public_application_list_obj.status_semakan_dokumen = status_semakan_dokumen
        public_application_list_obj.updated_date = now
        public_application_list_obj.updated_by = id_card_no
        
        if surat_penyerahan_kawasan:
            surat_penyerahan_kawasan = re.sub('[^a-zA-Z0-9.]', '', surat_penyerahan_kawasan)
            public_application_list_obj.surat_penyerahan_kawasan  = surat_penyerahan_kawasan
        else:
            public_application_list_obj.surat_penyerahan_kawasan = public_application_list_obj.surat_penyerahan_kawasan
        db.session.commit()

        public_application_obj = PublicApplicationDetails.query.filter_by(no_siri_permohonan=no_siri_permohonan).first()
        public_application_obj.status_dokumen_keseluruhan = status_semakan_dokumen
        public_application_obj.updated_date = now
        public_application_obj.updated_by = id_card_no
        db.session.commit()
        statement = f"Status semakan dokumen {no_siri_permohonan} berjaya dikemas kini."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()


        logger.info(f"Status semakan dokumen of {no_siri_permohonan} updated successfully")
        response_object = {
            'status':'success',
            'message': f'Status semakan dokumen of {no_siri_permohonan} updated successfully'
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
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
           
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
            # sitevisit_info_obj.makalumat_ketidakpatuhan = makalumat_ketidakpatuhan
            sitevisit_info_obj.maklum_balas_ketidakpatuhan = maklum_balas_ketidakpatuhan
            sitevisit_info_obj.updated_date = today
            sitevisit_info_obj.updated_by = id_card_no
            db.session.commit()
            
            statement = f"Item maklumat lawatan laman web : {site_id} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info(f"Site visit information item : {site_id} updated successfully")
            response_object = {
                'status':'success',
                'message': f'site_visit_updated'
            }
            return response_object, 201
        except:
            logger.exception("Site visit information Could not be updated")
            response_object = {
                'status':'fail',
                'message':'site_visit_not_updated'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'site_visit_not_updated',
        }
        return response_object, 404    

""" ===============================<< update site visit application list Ends >>=============================== """
""" ===============================<< update site visit application list 2 starts >>=============================== """
@token_required
def updateSiteVisitApplicationList2(site_id,data):
    if data.tarikh_datetime:
        tarikh_datetime=data.tarikh_datetime
    # lawatan_tapak=data.lawatan_tapak
    # tarikh_lawatan_tapak=data.tarikh_lawatan_tapak
    # keputusan_lawatan_tapak=data.keputusan_lawatan_tapak
    # makalumat_ketidakpatuhan=data.makalumat_ketidakpatuhan
    # maklum_balas_ketidakpatuhan=data.maklum_balas_ketidakpatuhan
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    if data.tetapan_lawatan_tapak_filename:
        tetapan_lawatan_tapak_filename = re.sub('[^a-zA-Z0-9.]', '', data.tetapan_lawatan_tapak_filename)
    if data.keputusan_lawatan_tapak:
        keputusan_lawatan_tapak = data.keputusan_lawatan_tapak
    if data.keputusan_lawatan_tapak_filename:
        keputusan_lawatan_tapak_filename = re.sub('[^a-zA-Z0-9.]', '', data.keputusan_lawatan_tapak_filename)

    logger.info(f"Updating site visit information for site_id: {site_id}")
    logger.info(f"Data received: {data}")

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
            if data.tarikh_datetime:
                sitevisit_info_obj.tarikh_datetime = tarikh_datetime
            # sitevisit_info_obj.lawatan_tapak = lawatan_tapak
            # sitevisit_info_obj.tarikh_lawatan_tapak = tarikh_lawatan_tapak
            # sitevisit_info_obj.keputusan_lawatan_tapak = keputusan_lawatan_tapak
            # # sitevisit_info_obj.makalumat_ketidakpatuhan = makalumat_ketidakpatuhan
            # sitevisit_info_obj.maklum_balas_ketidakpatuhan = maklum_balas_ketidakpatuhan
            sitevisit_info_obj.updated_date = today
            sitevisit_info_obj.updated_by = id_card_no
            if data.tetapan_lawatan_tapak_filename: 
                sitevisit_info_obj.tetapan_lawatan_tapak_filename = tetapan_lawatan_tapak_filename
            if data.keputusan_lawatan_tapak:
                sitevisit_info_obj.keputusan_lawatan_tapak = keputusan_lawatan_tapak
            if data.keputusan_lawatan_tapak_filename:
                sitevisit_info_obj.keputusan_lawatan_tapak_filename = keputusan_lawatan_tapak_filename
            db.session.commit()
            
            statement = f"Item maklumat lawatan laman web : {site_id} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info(f"Site visit information item : {site_id} updated successfully")
            response_object = {
                'status':'success',
                'message': f'site_visit_updated'
            }
            return response_object, 201
        except:
            logger.exception("Site visit information Could not be updated")
            response_object = {
                'status':'fail',
                'message':'site_visit_not_updated'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'site_visit_not_updated',
        }
        return response_object, 404    

""" ===============================<< update site visit application list 2 Ends >>=============================== """
""" ===============================<< Delete list of site visit information starts >>=============================== """

@token_required
def deletelistOfsitevisitInformation(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    site_id_list = data.site_id_list.split(",")
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin':
            for i in site_id_list:
                
                if PublicSiteVisitInfo.query.filter_by(site_id=i).first():
                    PublicSiteVisitInfo.query.filter_by(site_id=i).first().active = 0

            db.session.commit()

            statement = "Senarai maklumat laman web lawatan berjaya dihapuskan"
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            
            logger.info("List Of sitevisitInformation Deleted successfully")

            response_object = {
                "status": "success",
                "message": "site_visit_deleted"
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 

    except:

        logger.exception("list Of sitevisitInformation could not be deleted")
        response_object = {
            "status": "fail",
            "message": "site_visit_not_deleted"
        }
        return response_object, 400

""" ===============================<< Delete list of site visit information ends >>=============================== """
""" ===============================<< Undelete list of site visit information starts >>=============================== """

@token_required
def undeletelistOfsitevisitInformation(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    site_id_list = data.site_id_list.split(",")
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin':
            for i in site_id_list:
                
                if PublicSiteVisitInfo.query.filter_by(site_id=i).first():
                    PublicSiteVisitInfo.query.filter_by(site_id=i).first().active = 1

            db.session.commit()

            statement = "Maklumat senarai laman web berjaya dihapuskan"
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            
            logger.info("List Of sitevisitInformation uneleted successfully")

            response_object = {
                "status": "success",
                "message": "list Of sitevisitInformation uneleted successfully."
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

""" ===============================<< Unelete list of site visit information ends >>=============================== """
""" ===============================<< Delete site visit PDF starts >>=============================== """

@token_required
def deleteSitevisitPDF(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    site_id = data.site_id
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin':
            
            if PublicSiteVisitInfo.query.filter_by(site_id=site_id).first():
                PublicSiteVisitInfo.query.filter_by(site_id=site_id).first().maklum_balas_ketidakpatuhan = ''

            db.session.commit()

            statement = "PDF lawatan laman web berjaya dipadamkan"
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            
            logger.info("Site Visit PDF Deleted successfully")

            response_object = {
                "status": "success",
                "message": "site_visit_pdf_deleted"
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 

    except:

        logger.exception("Site Visit PDF could not be deleted")
        response_object = {
            "status": "fail",
            "message": "site_visit_pdf_not_deleted"
        }
        return response_object, 400

""" ===============================<< Delete list of site visit PDF ends >>=============================== """
""" $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$<< KEWANGAN STARTS >>$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ """

""" ===============================<< Fetch Job Payment claim starts >>=============================== """

@token_required
def getJobPaymentClaim():
    try:
        job_payment_claim_res = []
        for jobPaymentClaim in JobPaymentClaim.query.filter_by(active=1).order_by(desc(JobPaymentClaim.inserted_date)):
            job_payment_claim_res.append({
                "id": jobPaymentClaim.id,
                "tarikh_tuntutan": jobPaymentClaim.tarikh,
                "kontraktor" : jobPaymentClaim.kontraktor,
                "no_inbois"   : jobPaymentClaim.no_inbois,
                "status_semakan_tuntutan_inbois":jobPaymentClaim.status,
                })
        logger.info("Job payment claim fetched.")
        return jsonify(job_payment_claim_res)
    except:
        logger.exception("Job payment claim not fetched.")
        response_object = {
            'status':'fail',
            'message':'Job payment claim not fetched.'
        }
        return response_object, 409  
""" ===============================<< Fetch Job Payment claim ends >>=============================== """
""" ===============================<< Fetch Agency Job Payment claim by inbois starts >>=============================== """
@token_required
def getJobPaymentClaimByInbois(no_inbois):
    try:
        exists = db.session.query(JobPaymentClaim).filter_by(no_inbois=no_inbois, active=1)
    except:
        logger.exception('Job Payment Claim by inbois could not be found')
        response_object = {
                'status': 'fail',
                'message': 'Job Payment Claim by inbois could not be found',
            }
        return response_object, 404
    if exists:
        try:
            inventori_pengguna_obj = JobPaymentClaim.query.filter_by(no_inbois=no_inbois, active=1).first()
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
                "bd44": inventori_pengguna_obj.bd44,
                "laporan_tuntutan": inventori_pengguna_obj.laporan_tuntutan
            }
            logger.info("Job Payment Claim by inbois no fetched")
            return inventori_pengguna_res
        except:
            logger.exception("Job Payment Claim by inbois no not fetched")
            response_object = {
                'status':'fail',
                'message':'Job Payment Claim by inbois no not fetched.'
            }
            return response_object, 400  
    else:
        response_object = {
            'status': 'fail',
            'message': 'Job Payment Claim by inbois could not be found',
        }
        return response_object, 404     
    
""" ===============================<< Fetch Job Payment claim by inbois ends >>=============================== """

""" ===============================<< update Job Payment claim by inbois starts >>=============================== """

@token_required
def updateJobPaymentClaimByInbois(no_inbois,data):
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
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    try:
        job_payment_claim_obj = db.session.query(JobPaymentClaim).filter_by(no_inbois=no_inbois, active=1).first()
    
    except:
        logger.exception('Agency Job Payment claim by inbois could not be found')
        response_object = {
            'status': 'fail',
            'message': 'Agency Job Payment claim by inbois could not be found',
        }
        return response_object, 404
    if job_payment_claim_obj:
        try:
            job_payment_claim_obj.nama_pemohon = nama_pemohon
            job_payment_claim_obj.e_mei = e_mei
            job_payment_claim_obj.jumlah_tuntutan = jumlah_tuntutan
            job_payment_claim_obj.inbois_dokumen = inbois_dokumen
            job_payment_claim_obj.ringkasan_dokumen = ringkasan_dokumen
            job_payment_claim_obj.lampiran = lampiran
            job_payment_claim_obj.status = status
            job_payment_claim_obj.ulasan_pegawai = ulasan_pegawai
            job_payment_claim_obj.updated_date = now
            job_payment_claim_obj.updated_by = id_card_no
            db.session.commit()
            
            statement = f"Tuntutan Pembayaran Pekerjaan {no_inbois} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            
            logger.info(f"Job Payment Claim {no_inbois} updated successfully")
            response_object = {
                'status' : 'Success',
                'message' : 'payment_claim_updated'
            } 
            return response_object
        except:
            logger.exception("Job payment claim by inbois no not updated")
            response_object = {
                    'status':'fail',
                    'message':'payment_claim_not_updated'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'Agency Job Payment claim by inbois could not be found',
        }
        return response_object, 404          
    
""" ===============================<< Update Job Payment claim by inbois ends >>=============================== """
""" ===============================<< Delete Job Payment claim starts >>=============================== """

@token_required
def deleteJobPaymentClaim(data):

    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    agensi_id_list = data.agensi_id_list.split(",")
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin':
            for i in agensi_id_list:
                if JobPaymentClaim.query.filter_by(id=i).first():
                   data = JobPaymentClaim.query.filter_by(id=i).first()
                   db.session.delete(data)
            db.session.commit()
            
            statement = "Tuntutan Pembayaran Pekerjaan berjaya dipadamkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Job Payment Claim list Deleted successfully")

            response_object = {
                "status": "success",
                "message": "payment_claim_deleted"
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 

    except:
        logger.exception("Job Payment Claim list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "payment_claim_not_deleted"
        }
        return response_object, 400


""" ===============================<< Delete Job Payment claim ends >>=============================== """
""" ===============================<< Fetch jkas_omp starts >>=============================== """

def getOmpSubArea(parliament_name):
    try:
        subarea = OmpBaru.query.with_entities(OmpBaru.parlimen_subarea).filter_by(parlimen=parliament_name).distinct().all()
        subarea_list = list(itertools.chain(*subarea))

        logger.info("Parlimen Subarea List fetched")
        return subarea_list
    except:
        logger.exception("Parlimen Subarea List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Parlimen Subarea List could not be fetched"
        }
        return response_object, HTTPStatus.BAD_REQUEST

""" ===============================<< Fetch jkas_omp starts >>=============================== """
@token_required
def getOmpBaru(data):
    parliament_name = data.parliament_name
    parliament_subarea = data.parliament_subarea
    if db.session.query(OmpBaru).filter_by(parlimen = parliament_name, parlimen_subarea=parliament_subarea,active=1).first() == None:
        abort(HTTPStatus.CONFLICT, f"No Data Present with Parliament {parliament_name}", status="fail")
    try:
        omp_baru_list = []
        for jkasOmp in OmpBaru.query.filter_by(parlimen=parliament_name,parlimen_subarea=parliament_subarea, active=1).order_by(desc(OmpBaru.inserted_date)):
            omp_baru_list.append({
                "omp_id": jkasOmp.omp_id,
                "kodarea": jkasOmp.kodarea,
                "lokasi" : jkasOmp.lokasi,
                "parlimen"   : jkasOmp.parlimen,
                "parlimen_subarea":jkasOmp.parlimen_subarea,
                "kordinat":jkasOmp.kordinat,
                "jumlah_unit_premis":jkasOmp.jumlah_unit_premis,

                "domestic_category": jkasOmp.domestic_category,
                "domestic_freq": jkasOmp.domestic_freq,
                "domestic_rate": jkasOmp.domestic_rate,
                "domestic_total": jkasOmp.domestic_total,
                "pukal_category": jkasOmp.pukal_category,
                "pukal_freq": jkasOmp.pukal_freq,
                "pukal_rate": jkasOmp.pukal_rate,
                "pukal_total": jkasOmp.pukal_total,

                "sapuan_domestic_unit": jkasOmp.sapuan_domestic_unit,
                "sapuan_domestic_freq": jkasOmp.sapuan_domestic_freq,
                "sapuan_domestic_rate": jkasOmp.sapuan_domestic_rate,
                "sapuan_komersial_unit": jkasOmp.sapuan_komersial_unit,
                "sapuan_komersial_freq": jkasOmp.sapuan_komersial_freq,
                "sapuan_komersial_rate": jkasOmp.sapuan_komersial_rate,

                "cucian_domestic_unit": jkasOmp.cucian_domestic_unit,
                "cucian_domestic_freq": jkasOmp.cucian_domestic_freq,
                "cucian_domestic_rate": jkasOmp.cucian_domestic_rate,
                "cucian_komersial_unit": jkasOmp.cucian_komersial_unit,
                "cucian_komersial_freq": jkasOmp.cucian_komersial_freq,
                "cucian_komersial_rate": jkasOmp.cucian_komersial_rate,
                "cucian_drain_domestic_unit": jkasOmp.cucian_drain_domestic_unit,
                "cucian_drain_domestic_freq": jkasOmp.cucian_drain_domestic_freq,
                "cucian_drain_domestic_rate": jkasOmp.cucian_drain_domestic_rate,
                "cucian_drain_komersial_unit": jkasOmp.cucian_drain_komersial_unit,
                "cucian_drain_komersial_freq": jkasOmp.cucian_drain_komersial_freq,
                "cucian_drain_komersial_rate": jkasOmp.cucian_drain_komersial_rate,
                "cucian_jejantas_dalam_unit": jkasOmp.cucian_jejantas_dalam_unit,
                "cucian_jejantas_dalam_freq": jkasOmp.cucian_jejantas_dalam_freq,
                "cucian_jejantas_dalam_rate": jkasOmp.cucian_jejantas_dalam_rate,
                "cucian_jejantas_atas_unit": jkasOmp.cucian_jejantas_atas_unit,
                "cucian_jejantas_atas_freq": jkasOmp.cucian_jejantas_atas_freq,
                "cucian_jejantas_atas_rate": jkasOmp.cucian_jejantas_atas_rate,
                "cucian_siar_roof_unit": jkasOmp.cucian_siar_roof_unit,
                "cucian_siar_roof_freq": jkasOmp.cucian_siar_roof_freq,
                "cucian_siar_roof_rate": jkasOmp.cucian_siar_roof_rate,
                "cucian_siar_gulam1_unit": jkasOmp.cucian_siar_gulam1_unit,
                "cucian_siar_gulam1_freq": jkasOmp.cucian_siar_gulam1_freq,
                "cucian_siar_gulam1_rate": jkasOmp.cucian_siar_gulam1_rate,
                "cucian_siar_gulam2_unit": jkasOmp.cucian_siar_gulam2_unit,
                "cucian_siar_gulam2_freq": jkasOmp.cucian_siar_gulam2_freq,
                "cucian_siar_gulam2_rate": jkasOmp.cucian_siar_gulam2_rate,
                "cucian_tandas_unit": jkasOmp.cucian_tandas_unit,
                "cucian_tandas_freq": jkasOmp.cucian_tandas_freq,
                "cucian_tandas_rate": jkasOmp.cucian_tandas_rate,
                "cucian_teksi_rate": jkasOmp.cucian_teksi_rate,
                "cucian_teksi_freq": jkasOmp.cucian_teksi_freq,
                "cucian_teksi_total": jkasOmp.cucian_teksi_total,

                "bersih_lapang_unit": jkasOmp.bersih_lapang_unit,
                "bersih_lapang_freq": jkasOmp.bersih_lapang_freq,
                "bersih_lapang_rate": jkasOmp.bersih_lapang_rate,
                "bersih_tpkk_unit": jkasOmp.bersih_tpkk_unit,
                "bersih_tpkk_freq": jkasOmp.bersih_tpkk_freq,
                "bersih_tpkk_rate": jkasOmp.bersih_tpkk_rate,
                "bersih_penjaja_unit": jkasOmp.bersih_penjaja_unit,
                "bersih_penjaja_freq": jkasOmp.bersih_penjaja_freq,
                "bersih_penjaja_rate": jkasOmp.bersih_penjaja_rate,
                "bersih_pasar_unit": jkasOmp.bersih_pasar_unit,
                "bersih_pasar_freq": jkasOmp.bersih_pasar_freq,
                "bersih_pasar_rate": jkasOmp.bersih_pasar_rate,
                "bersih_pasar_mlm_unit": jkasOmp.bersih_pasar_mlm_unit,
                "bersih_pasar_mlm_freq": jkasOmp.bersih_pasar_mlm_freq,
                "bersih_pasar_mlm_rate": jkasOmp.bersih_pasar_mlm_rate,

                "rumput_unit": jkasOmp.rumput_unit,
                "rumput_freq": jkasOmp.rumput_freq,
                "rumput_rate": jkasOmp.rumput_rate,

                "kekerapan_kutipan_sisa_domestik":jkasOmp.kekerapan_kutipan_sisa_domestik,
                "kekerapan_kutipan_sampah_pukal":jkasOmp.kekerapan_kutipan_sampah_pukal,
                "kekerapan_kutipan_sampah_haram":jkasOmp.kekerapan_kutipan_sampah_haram,
                "ukuran_panjang_sapuan_jalan":jkasOmp.ukuran_panjang_sapuan_jalan,
                "ukuran_panjang_sapuan_TPKK":jkasOmp.ukuran_panjang_sapuan_TPKK,
                "ukuran_panjang_sapuan_kaw_lapang_parkir":jkasOmp.ukuran_panjang_sapuan_kaw_lapang_parkir,
                "ukuran_panjang_sapuan_jejantas":jkasOmp.ukuran_panjang_sapuan_jejantas,
                "ukuran_panjang_cucian_jejantas":jkasOmp.ukuran_panjang_cucian_jejantas,
                "ukuran_panjang_cucian_siarkaki":jkasOmp.ukuran_panjang_cucian_siarkaki,
                "ukuran_panjang_cucian_siarkaki_berbumbung":jkasOmp.ukuran_panjang_cucian_siarkaki_berbumbung,
                "ukuran_panjang_cucian_stesenbas_teksi":jkasOmp.ukuran_panjang_cucian_stesenbas_teksi,
                "ukuran_panjang_cucian_longkang":jkasOmp.ukuran_panjang_cucian_longkang,
                "ukuran_panjang_potongrumput":jkasOmp.ukuran_panjang_potongrumput,
                "ukuran_panjang_sampahkebun":jkasOmp.ukuran_panjang_sampahkebun,
                "catatan":jkasOmp.catatan,
                "rujuken_tarikh_serahan":jkasOmp.rujuken_tarikh_serahan,
                "tarikh_semakandi_lapangant_keadeansemata_ada":jkasOmp.tarikh_semakandi_lapangant_keadeansemata_ada,
                "tarikh_semakandi_lapangant_keadeansemata_tiada":jkasOmp.tarikh_semakandi_lapangant_keadeansemata_tiada,
                "surat_serahan": jkasOmp.surat_serahan,
                "kadar": jkasOmp.kadar,
                "frekuensi": jkasOmp.frekuensi
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
""" ===============================<< getSingleOmpBaru starts >>=============================== """
@token_required
def getSingleOmpBaru(omp_id):
    
    if db.session.query(OmpBaru).filter_by(omp_id=omp_id,active=1).first() == None:
        abort(HTTPStatus.CONFLICT, f"No Data Present omp_id {omp_id}", status="fail")
    try:
        ompBaruDict = {}
        ompInfo = db.session.query(OmpBaru).filter_by(omp_id=omp_id, active=1).first()
        ompBaruDict['omp_id']=ompInfo.omp_id
        ompBaruDict['kodarea']=ompInfo.kodarea
        ompBaruDict['lokasi']=ompInfo.lokasi
        ompBaruDict['parlimen']=ompInfo.parlimen
        ompBaruDict['parlimen_subarea']=ompInfo.parlimen_subarea
        ompBaruDict['kordinat']=ompInfo.kordinat
        ompBaruDict['jumlah_unit_premis']=ompInfo.jumlah_unit_premis
        ompBaruDict['kekerapan_kutipan_sisa_domestik']=ompInfo.kekerapan_kutipan_sisa_domestik
        ompBaruDict['kekerapan_kutipan_sampah_pukal']=ompInfo.kekerapan_kutipan_sampah_pukal
        ompBaruDict['kekerapan_kutipan_sampah_haram']=ompInfo.kekerapan_kutipan_sampah_haram
        ompBaruDict['ukuran_panjang_sapuan_jalan']=ompInfo.ukuran_panjang_sapuan_jalan
        ompBaruDict['ukuran_panjang_sapuan_TPKK']=ompInfo.ukuran_panjang_sapuan_TPKK
        ompBaruDict['ukuran_panjang_sapuan_kaw_lapang_parkir']=ompInfo.ukuran_panjang_sapuan_kaw_lapang_parkir
        ompBaruDict['ukuran_panjang_sapuan_jejantas']=ompInfo.ukuran_panjang_sapuan_jejantas
        ompBaruDict['ukuran_panjang_cucian_jejantas']=ompInfo.ukuran_panjang_cucian_jejantas
        ompBaruDict['ukuran_panjang_cucian_siarkaki']=ompInfo.ukuran_panjang_cucian_siarkaki
        ompBaruDict['ukuran_panjang_cucian_siarkaki_berbumbung']=ompInfo.ukuran_panjang_cucian_siarkaki_berbumbung
        ompBaruDict['ukuran_panjang_cucian_stesenbas_teksi']=ompInfo.ukuran_panjang_cucian_stesenbas_teksi
        ompBaruDict['ukuran_panjang_cucian_longkang']=ompInfo.ukuran_panjang_cucian_longkang
        ompBaruDict['ukuran_panjang_potongrumput']=ompInfo.ukuran_panjang_potongrumput
        ompBaruDict['ukuran_panjang_sampahkebun']=ompInfo.ukuran_panjang_sampahkebun
        ompBaruDict['catatan']=ompInfo.catatan
        ompBaruDict['rujuken_tarikh_serahan']=ompInfo.rujuken_tarikh_serahan
        ompBaruDict['tarikh_semakandi_lapangant_keadeansemata_ada']=ompInfo.tarikh_semakandi_lapangant_keadeansemata_ada
        ompBaruDict['tarikh_semakandi_lapangant_keadeansemata_tiada']=ompInfo.tarikh_semakandi_lapangant_keadeansemata_tiada
        ompBaruDict['kadar'] = ompInfo.kadar
        ompBaruDict['frekuensi'] = ompInfo.frekuensi

        ompBaruDict['domestic_category'] = ompInfo.domestic_category
        ompBaruDict['domestic_freq'] = ompInfo.domestic_freq
        ompBaruDict['domestic_rate'] = ompInfo.domestic_rate
        ompBaruDict['domestic_total'] = ompInfo.domestic_total
        ompBaruDict['pukal_category'] = ompInfo.pukal_category
        ompBaruDict['pukal_freq'] = ompInfo.pukal_freq
        ompBaruDict['pukal_rate'] = ompInfo.pukal_rate
        ompBaruDict['pukal_total'] = ompInfo.pukal_total

        ompBaruDict['sapuan_domestic_unit'] = ompInfo.sapuan_domestic_unit
        ompBaruDict['sapuan_domestic_rate'] = ompInfo.sapuan_domestic_rate
        ompBaruDict['sapuan_domestic_freq'] = ompInfo.sapuan_domestic_freq
        ompBaruDict['sapuan_komersial_unit'] = ompInfo.sapuan_komersial_unit
        ompBaruDict['sapuan_komersial_rate'] = ompInfo.sapuan_komersial_rate
        ompBaruDict['sapuan_komersial_freq'] = ompInfo.sapuan_komersial_freq

        ompBaruDict['cucian_domestic_unit'] = ompInfo.cucian_domestic_unit
        ompBaruDict['cucian_domestic_rate'] = ompInfo.cucian_domestic_rate
        ompBaruDict['cucian_domestic_freq'] = ompInfo.cucian_domestic_freq
        ompBaruDict['cucian_komersial_unit'] = ompInfo.cucian_komersial_unit
        ompBaruDict['cucian_komersial_rate'] = ompInfo.cucian_komersial_rate
        ompBaruDict['cucian_komersial_freq'] = ompInfo.cucian_komersial_freq
        ompBaruDict['cucian_drain_domestic_unit'] = ompInfo.cucian_drain_domestic_unit
        ompBaruDict['cucian_drain_domestic_rate'] = ompInfo.cucian_drain_domestic_rate
        ompBaruDict['cucian_drain_domestic_freq'] = ompInfo.cucian_drain_domestic_freq
        ompBaruDict['cucian_drain_komersial_unit'] = ompInfo.cucian_drain_komersial_unit
        ompBaruDict['cucian_drain_komersial_rate'] = ompInfo.cucian_drain_komersial_rate
        ompBaruDict['cucian_drain_komersial_freq'] = ompInfo.cucian_drain_komersial_freq
        ompBaruDict['cucian_jejantas_dalam_unit'] = ompInfo.cucian_jejantas_dalam_unit
        ompBaruDict['cucian_jejantas_dalam_rate'] = ompInfo.cucian_jejantas_dalam_rate
        ompBaruDict['cucian_jejantas_dalam_freq'] = ompInfo.cucian_jejantas_dalam_freq
        ompBaruDict['cucian_jejantas_atas_unit'] = ompInfo.cucian_jejantas_atas_unit
        ompBaruDict['cucian_jejantas_atas_rate'] = ompInfo.cucian_jejantas_atas_rate
        ompBaruDict['cucian_jejantas_atas_freq'] = ompInfo.cucian_jejantas_atas_freq
        ompBaruDict['cucian_siar_roof_unit'] = ompInfo.cucian_siar_roof_unit
        ompBaruDict['cucian_siar_roof_rate'] = ompInfo.cucian_siar_roof_rate
        ompBaruDict['cucian_siar_roof_freq'] = ompInfo.cucian_siar_roof_freq
        ompBaruDict['cucian_siar_gulam1_unit'] = ompInfo.cucian_siar_gulam1_unit
        ompBaruDict['cucian_siar_gulam1_rate'] = ompInfo.cucian_siar_gulam1_rate
        ompBaruDict['cucian_siar_gulam1_freq'] = ompInfo.cucian_siar_gulam1_freq
        ompBaruDict['cucian_siar_gulam2_unit'] = ompInfo.cucian_siar_gulam2_unit
        ompBaruDict['cucian_siar_gulam2_rate'] = ompInfo.cucian_siar_gulam2_rate
        ompBaruDict['cucian_siar_gulam2_freq'] = ompInfo.cucian_siar_gulam2_freq
        ompBaruDict['cucian_tandas_unit'] = ompInfo.cucian_tandas_unit
        ompBaruDict['cucian_tandas_rate'] = ompInfo.cucian_tandas_rate
        ompBaruDict['cucian_tandas_freq'] = ompInfo.cucian_tandas_freq
        ompBaruDict['cucian_teksi_rate'] = ompInfo.cucian_teksi_rate
        ompBaruDict['cucian_teksi_freq'] = ompInfo.cucian_teksi_freq
        ompBaruDict['cucian_teksi_total'] = ompInfo.cucian_teksi_total

        ompBaruDict['bersih_lapang_unit'] = ompInfo.bersih_lapang_unit
        ompBaruDict['bersih_lapang_freq'] = ompInfo.bersih_lapang_freq
        ompBaruDict['bersih_lapang_rate'] = ompInfo.bersih_lapang_rate
        ompBaruDict['bersih_tpkk_unit'] = ompInfo.bersih_tpkk_unit
        ompBaruDict['bersih_tpkk_freq'] = ompInfo.bersih_tpkk_freq
        ompBaruDict['bersih_tpkk_rate'] = ompInfo.bersih_tpkk_rate
        ompBaruDict['bersih_penjaja_unit'] = ompInfo.bersih_penjaja_unit
        ompBaruDict['bersih_penjaja_rate'] = ompInfo.bersih_penjaja_rate
        ompBaruDict['bersih_penjaja_freq'] = ompInfo.bersih_penjaja_freq
        ompBaruDict['bersih_pasar_unit'] = ompInfo.bersih_pasar_unit
        ompBaruDict['bersih_pasar_freq'] = ompInfo.bersih_pasar_freq
        ompBaruDict['bersih_pasar_rate'] = ompInfo.bersih_pasar_rate
        ompBaruDict['bersih_pasar_mlm_unit'] = ompInfo.bersih_pasar_mlm_unit
        ompBaruDict['bersih_pasar_mlm_rate'] = ompInfo.bersih_pasar_mlm_rate
        ompBaruDict['bersih_pasar_mlm_freq'] = ompInfo.bersih_pasar_mlm_freq

        ompBaruDict['rumput_unit'] = ompInfo.rumput_unit
        ompBaruDict['rumput_freq'] = ompInfo.rumput_freq
        ompBaruDict['rumput_rate'] = ompInfo.rumput_rate

        ompBaruDict['surat_serahan'] = ompInfo.surat_serahan


        logger.info("OMP Baru Info fetched.")
        return ompBaruDict
    except:
        logger.exception("OMP Baru list could not be fetched.")
        response_object = {
            'status':'fail',
            'message':'OMP Baru list could not be fetched.'
        }
        return response_object, 400  
""" ===============================<< getSingleOmpBaru ends >>=============================== """
""" ===============================<< updateOmpBaru starts >>=============================== """
@token_required
def updateOmpBaru(data,omp_id):
    parlimen = data.parlimen
    lokasi = data.lokasi
    kordinat = data.kordinat
    jumlah_unit_premis = data.jumlah_unit_premis
    kekerapan_kutipan_sisa_domestik = data.sisa_domestik
    kekerapan_kutipan_sampah_pukal = data.sampah_pukal
    kekerapan_kutipan_sampah_haram = data.sampah_haram
    ukuran_panjang_sapuan_jalan = data.sapuan_jalan
    ukuran_panjang_sapuan_TPKK = data.sapuan_TPKK
    ukuran_panjang_sapuan_kaw_lapang_parkir = data.sapuan_parkir
    ukuran_panjang_sapuan_jejantas = data.sapuan_jejantas
    ukuran_panjang_cucian_jejantas = data.cucian_jejantas
    ukuran_panjang_cucian_siarkaki = data.cucian_siarkaki
    ukuran_panjang_cucian_siarkaki_berbumbung = data.cucian_siarkaki_berbumbung
    ukuran_panjang_cucian_stesenbas_teksi = data.cucian_stesenbas_teksi
    ukuran_panjang_cucian_longkang = data.cucian_longkang
    ukuran_panjang_potongrumput = data.potong_rumput
    ukuran_panjang_sampahkebun = data.sampah_kebun
    catatan = data.catatan
    rujukan_tarikh_serahan = data.rujukan_tarikh_serahan
    tarikh_semakandi_lapangant_keadeansemata_ada = data.tarikh_semakandi_lapangant_keadeansemata_ada
    tarikh_semakandi_lapangant_keadeansemata_tiada = data.tarikh_semakandi_lapangant_keadeansemata_tiada
    surat_serahan = data.surat_serahan
    kadar = data.kadar
    frekuensi = data.frekuensi

    domestic_category = data.domestic_category
    domestic_total = data.domestic_total
    domestic_freq = data.domestic_freq
    domestic_rate = data.domestic_rate
    pukal_category = data.pukal_category
    pukal_total = data.pukal_total
    pukal_freq = data.pukal_freq
    pukal_rate = data.pukal_rate

    sapuan_domestic_unit = data.sapuan_domestic_unit
    sapuan_domestic_rate = data.sapuan_domestic_rate
    sapuan_domestic_freq = data.sapuan_domestic_freq
    sapuan_komersial_unit = data.sapuan_komersial_unit
    sapuan_komersial_rate = data.sapuan_komersial_rate
    sapuan_komersial_freq = data.sapuan_komersial_freq

    cucian_domestic_unit = data.cucian_domestic_unit
    cucian_domestic_rate = data.cucian_domestic_rate
    cucian_domestic_freq = data.cucian_domestic_freq
    cucian_komersial_unit = data.cucian_komersial_unit
    cucian_komersial_rate = data.cucian_komersial_rate
    cucian_komersial_freq = data.cucian_komersial_freq
    cucian_drain_domestic_unit = data.cucian_drain_domestic_unit
    cucian_drain_domestic_rate = data.cucian_drain_domestic_rate
    cucian_drain_domestic_freq = data.cucian_drain_domestic_freq
    cucian_drain_komersial_unit = data.cucian_drain_komersial_unit
    cucian_drain_komersial_rate = data.cucian_drain_komersial_rate
    cucian_drain_komersial_freq = data.cucian_drain_komersial_freq
    cucian_jejantas_dalam_unit = data.cucian_jejantas_dalam_unit
    cucian_jejantas_dalam_rate = data.cucian_jejantas_dalam_rate
    cucian_jejantas_dalam_freq = data.cucian_jejantas_dalam_freq
    cucian_jejantas_atas_unit = data.cucian_jejantas_atas_unit
    cucian_jejantas_atas_rate = data.cucian_jejantas_atas_rate
    cucian_jejantas_atas_freq = data.cucian_jejantas_atas_freq
    cucian_siar_roof_unit = data.cucian_siar_roof_unit
    cucian_siar_roof_rate = data.cucian_siar_roof_rate
    cucian_siar_roof_freq = data.cucian_siar_roof_freq
    cucian_siar_gulam1_unit = data.cucian_siar_gulam1_unit
    cucian_siar_gulam1_rate = data.cucian_siar_gulam1_rate
    cucian_siar_gulam1_freq = data.cucian_siar_gulam1_freq
    cucian_siar_gulam2_unit = data.cucian_siar_gulam2_unit
    cucian_siar_gulam2_rate = data.cucian_siar_gulam2_rate
    cucian_siar_gulam2_freq = data.cucian_siar_gulam2_freq
    cucian_tandas_unit = data.cucian_tandas_unit
    cucian_tandas_rate = data.cucian_tandas_rate
    cucian_tandas_freq = data.cucian_tandas_freq
    cucian_teksi_rate = data.cucian_teksi_rate
    cucian_teksi_freq = data.cucian_teksi_freq
    cucian_teksi_total = data.cucian_teksi_total

    bersih_lapang_unit = data.bersih_lapang_unit
    bersih_lapang_rate = data.bersih_lapang_rate
    bersih_lapang_freq = data.bersih_lapang_freq
    bersih_tpkk_unit = data.bersih_tpkk_unit
    bersih_tpkk_rate = data.bersih_tpkk_rate
    bersih_tpkk_freq = data.bersih_tpkk_freq
    bersih_penjaja_unit = data.bersih_penjaja_unit
    bersih_penjaja_rate = data.bersih_penjaja_rate
    bersih_penjaja_freq = data.bersih_penjaja_freq
    bersih_pasar_unit = data.bersih_pasar_unit
    bersih_pasar_rate = data.bersih_pasar_rate
    bersih_pasar_freq = data.bersih_pasar_freq
    bersih_pasar_mlm_unit = data.bersih_pasar_mlm_unit
    bersih_pasar_mlm_rate = data.bersih_pasar_mlm_rate
    bersih_pasar_mlm_freq = data.bersih_pasar_mlm_freq

    rumput_unit = data.rumput_unit
    rumput_rate = data.rumput_rate
    rumput_freq = data.rumput_freq
    if db.session.query(OmpBaru).filter_by(omp_id=omp_id,active=1).first() == None:
        abort(HTTPStatus.CONFLICT, f"No Data Present with omp_id {omp_id}", status="fail")
    try:
        ompInfo = db.session.query(OmpBaru).filter_by(omp_id=omp_id,active=1).first()
        ompInfo.lokasi = lokasi
        ompInfo.parlimen = parlimen
        ompInfo.kordinat=kordinat
        ompInfo.jumlah_unit_premis=jumlah_unit_premis
        ompInfo.kekerapan_kutipan_sisa_domestik=kekerapan_kutipan_sisa_domestik
        ompInfo.kekerapan_kutipan_sampah_pukal=kekerapan_kutipan_sampah_pukal
        ompInfo.kekerapan_kutipan_sampah_haram=kekerapan_kutipan_sampah_haram
        ompInfo.ukuran_panjang_sapuan_jalan=ukuran_panjang_sapuan_jalan
        ompInfo.ukuran_panjang_sapuan_TPKK=ukuran_panjang_sapuan_TPKK
        ompInfo.ukuran_panjang_sapuan_kaw_lapang_parkir=ukuran_panjang_sapuan_kaw_lapang_parkir
        ompInfo.ukuran_panjang_sapuan_jejantas=ukuran_panjang_sapuan_jejantas
        ompInfo.ukuran_panjang_cucian_jejantas=ukuran_panjang_cucian_jejantas
        ompInfo.ukuran_panjang_cucian_siarkaki=ukuran_panjang_cucian_siarkaki
        ompInfo.ukuran_panjang_cucian_siarkaki_berbumbung=ukuran_panjang_cucian_siarkaki_berbumbung
        ompInfo.ukuran_panjang_cucian_stesenbas_teksi=ukuran_panjang_cucian_stesenbas_teksi
        ompInfo.ukuran_panjang_cucian_longkang=ukuran_panjang_cucian_longkang
        ompInfo.ukuran_panjang_potongrumput=ukuran_panjang_potongrumput
        ompInfo.ukuran_panjang_sampahkebun=ukuran_panjang_sampahkebun
        ompInfo.catatan=catatan
        ompInfo.rujuken_tarikh_serahan=rujukan_tarikh_serahan
        ompInfo.surat_serahan = surat_serahan

        ompInfo.domestic_category = domestic_category
        ompInfo.domestic_total = domestic_total
        ompInfo.domestic_freq = domestic_freq
        ompInfo.domestic_rate = domestic_rate
        ompInfo.pukal_category = pukal_category
        ompInfo.pukal_total = pukal_total
        ompInfo.pukal_freq = pukal_freq
        ompInfo.pukal_rate = pukal_rate

        ompInfo.sapuan_domestic_unit = sapuan_domestic_unit
        ompInfo.sapuan_domestic_rate = sapuan_domestic_rate
        ompInfo.sapuan_domestic_freq = sapuan_domestic_freq
        ompInfo.sapuan_komersial_unit = sapuan_komersial_unit
        ompInfo.sapuan_komersial_rate = sapuan_komersial_rate
        ompInfo.sapuan_komersial_freq = sapuan_komersial_freq

        ompInfo.cucian_domestic_unit = cucian_domestic_unit
        ompInfo.cucian_domestic_rate = cucian_domestic_rate
        ompInfo.cucian_domestic_freq = cucian_domestic_freq
        ompInfo.cucian_komersial_unit = cucian_komersial_unit
        ompInfo.cucian_komersial_rate = cucian_komersial_rate
        ompInfo.cucian_komersial_freq = cucian_komersial_freq
        ompInfo.cucian_drain_domestic_unit = cucian_drain_domestic_unit
        ompInfo.cucian_drain_domestic_rate = cucian_drain_domestic_rate
        ompInfo.cucian_drain_domestic_freq = cucian_drain_domestic_freq
        ompInfo.cucian_drain_komersial_unit = cucian_drain_komersial_unit
        ompInfo.cucian_drain_komersial_rate = cucian_drain_komersial_rate
        ompInfo.cucian_drain_komersial_freq = cucian_drain_komersial_freq
        ompInfo.cucian_jejantas_dalam_unit = cucian_jejantas_dalam_unit
        ompInfo.cucian_jejantas_dalam_rate = cucian_jejantas_dalam_rate
        ompInfo.cucian_jejantas_dalam_freq = cucian_jejantas_dalam_freq
        ompInfo.cucian_jejantas_atas_unit = cucian_jejantas_atas_unit
        ompInfo.cucian_jejantas_atas_rate = cucian_jejantas_atas_rate
        ompInfo.cucian_jejantas_atas_freq = cucian_jejantas_atas_freq
        ompInfo.cucian_siar_roof_unit = cucian_siar_roof_unit
        ompInfo.cucian_siar_roof_rate = cucian_siar_roof_rate
        ompInfo.cucian_siar_roof_freq = cucian_siar_roof_freq
        ompInfo.cucian_siar_gulam1_unit = cucian_siar_gulam1_unit
        ompInfo.cucian_siar_gulam1_rate = cucian_siar_gulam1_rate
        ompInfo.cucian_siar_gulam1_freq = cucian_siar_gulam1_freq
        ompInfo.cucian_siar_gulam2_unit = cucian_siar_gulam2_unit
        ompInfo.cucian_siar_gulam2_rate = cucian_siar_gulam2_rate
        ompInfo.cucian_siar_gulam2_freq = cucian_siar_gulam2_freq
        ompInfo.cucian_tandas_unit = cucian_tandas_unit
        ompInfo.cucian_tandas_rate = cucian_tandas_rate
        ompInfo.cucian_tandas_freq = cucian_tandas_freq
        ompInfo.cucian_teksi_rate = cucian_teksi_rate
        ompInfo.cucian_teksi_freq = cucian_teksi_freq
        ompInfo.cucian_teksi_total = cucian_teksi_total

        ompInfo.bersih_lapang_unit = bersih_lapang_unit
        ompInfo.bersih_lapang_rate = bersih_lapang_rate
        ompInfo.bersih_lapang_freq = bersih_lapang_freq
        ompInfo.bersih_tpkk_unit = bersih_tpkk_unit
        ompInfo.bersih_tpkk_rate = bersih_tpkk_rate
        ompInfo.bersih_tpkk_freq = bersih_tpkk_freq
        ompInfo.bersih_penjaja_unit = bersih_penjaja_unit
        ompInfo.bersih_penjaja_rate = bersih_penjaja_rate
        ompInfo.bersih_penjaja_freq = bersih_penjaja_freq
        ompInfo.bersih_pasar_unit = bersih_pasar_unit
        ompInfo.bersih_pasar_rate = bersih_pasar_rate
        ompInfo.bersih_pasar_freq = bersih_pasar_freq
        ompInfo.bersih_pasar_mlm_unit = bersih_pasar_mlm_unit
        ompInfo.bersih_pasar_mlm_rate = bersih_pasar_mlm_rate
        ompInfo.bersih_pasar_mlm_freq = bersih_pasar_mlm_freq

        ompInfo.rumput_unit = rumput_unit
        ompInfo.rumput_rate = rumput_rate
        ompInfo.rumput_freq = rumput_freq

        ompInfo.tarikh_semakandi_lapangant_keadeansemata_ada=tarikh_semakandi_lapangant_keadeansemata_ada
        ompInfo.tarikh_semakandi_lapangant_keadeansemata_tiada=tarikh_semakandi_lapangant_keadeansemata_tiada
        ompInfo.kadar = kadar
        ompInfo.frekuensi = frekuensi
        db.session.commit()
        logger.info("OMP Baru list updated.")
        response_object = {
            'status':'success',
            'message':'OMP Baru list updated successfully.'
        }
        return response_object, 200  
    except:
        logger.exception("OMP Baru list could not be fetched.")
        response_object = {
            'status':'fail',
            'message':'OMP Baru list could not be fetched.'
        }
        return response_object, 400  
""" ===============================<< updateOmpBaru ends >>=============================== """
""" ===============================<< deleteOmpBaru Starts >>=============================== """
@token_required
def deleteOmpBaru(omp_id):
    user = get_logged_in_user()
    try:
        if user.user_type == 'SuperAdmin' or user.user_type == 'admin':
            if OmpBaru.query.filter_by(omp_id=omp_id).first():
                OmpBaru.query.filter_by(omp_id=omp_id).delete()
                
            db.session.commit()
            logger.info("Omp Baru Deleted successfully")
            response_object = {
                "status": "success",
                "message": "ompbaru_deleted"
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 

    except:
        logger.exception("Omp Baru could not be deleted")
        response_object = {
            "status": "fail",
            "message": "ompbaru_not_deleted"
        }
        return response_object, 400


""" ===============================<< deleteOmpBaru ends >>=============================== """
""" ===============================<< Get Filtered Lokasi Starts >>=============================== """
@token_required
def getFilteredLokasi(data):
    parliament_name = data.parlimen
    lokasi = data.lokasi
    if db.session.query(OmpBaru).filter_by(parlimen = parliament_name, lokasi=lokasi, active=1).first() == None:
        abort(HTTPStatus.CONFLICT, f"No Data Present with Parliament {parliament_name}", status="fail")
    try:
        omp_baru_list = []
        for jkasOmp in OmpBaru.query.filter_by(parlimen=parliament_name, lokasi=lokasi, active=1).order_by(desc(OmpBaru.inserted_date)):
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
                "ukuran_panjang_sapuan_kaw_lapang_parkir":jkasOmp.ukuran_panjang_sapuan_kaw_lapang_parkir,
                "ukuran_panjang_sapuan_jejantas":jkasOmp.ukuran_panjang_sapuan_jejantas,
                "ukuran_panjang_cucian_jejantas":jkasOmp.ukuran_panjang_cucian_jejantas,
                "ukuran_panjang_cucian_siarkaki":jkasOmp.ukuran_panjang_cucian_siarkaki,
                "ukuran_panjang_cucian_siarkaki_berbumbung":jkasOmp.ukuran_panjang_cucian_siarkaki_berbumbung,
                "ukuran_panjang_cucian_stesenbas_teksi":jkasOmp.ukuran_panjang_cucian_stesenbas_teksi,
                "ukuran_panjang_cucian_longkang":jkasOmp.ukuran_panjang_cucian_longkang,
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
""" ===============================<< Get Filtered Lokasi ends >>=============================== """

def getOmpLamaSubArea(parliament_name):
    try:
        subarea = Coordinates.query.with_entities(Coordinates.parlimen_subarea).filter_by(parlimen=parliament_name).distinct().all()
        subarea_list = list(itertools.chain(*subarea))

        logger.info("Parlimen Subarea List fetched")
        return subarea_list
    except:
        logger.exception("Parlimen Subarea List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Parlimen Subarea List could not be fetched"
        }
        return response_object, HTTPStatus.BAD_REQUEST
""" ===============================<< Fetch OmpLama starts >>=============================== """
@token_required
def getOmpLama(data):
    parliament_name = data.parliament_name
    parliament_subarea = data.parliament_subarea
    if db.session.query(Coordinates).filter_by(parlimen = parliament_name,parlimen_subarea=parliament_subarea, active=1).first() == None:
        abort(HTTPStatus.CONFLICT, f"No Data Present with Parliament {parliament_name}", status="fail")
        
    try:
        omp_lama_res = []
        for coordinate in Coordinates.query.filter_by(parlimen=parliament_name,parlimen_subarea=parliament_subarea, active=1):
            omp_lama_res.append({
                "kodarea": coordinate.coordinate_id,
                "lokasi": coordinate.lokasi,
                "parlimen" : coordinate.parlimen,
                "taman"   : coordinate.taman,
                "latitude" : coordinate.latitude,
                "longitude" : coordinate.longitude,
                "parlimen_subarea" : coordinate.parlimen_subarea,
                "jumlah_unit_premis" : coordinate.jumlah_unit_premis,
                "kekerapan_kutipan_sisa_domestik" : coordinate.kekerapan_kutipan_sisa_domestik,
                "kekerapan_kutipan_sampah_pukal" : coordinate.kekerapan_kutipan_sampah_pukal,
                "kekerapan_kutipan_sampah_haram" : coordinate.kekerapan_kutipan_sampah_haram,
                "ukuran_panjang_sapuan_jalan" : coordinate.ukuran_panjang_sapuan_jalan,
                "ukuran_panjang_sapuan_TPKK" : coordinate.ukuran_panjang_sapuan_TPKK,
                "ukuran_panjang_sapuan_kaw_lapang_parkir" : coordinate.ukuran_panjang_sapuan_kaw_lapang_parkir,
                "ukuran_panjang_sapuan_jejantas" : coordinate.ukuran_panjang_sapuan_jejantas,
                "ukuran_panjang_cucian_jejantas" : coordinate.ukuran_panjang_cucian_jejantas,
                "ukuran_panjang_cucian_siarkaki" : coordinate.ukuran_panjang_cucian_siarkaki,
                "ukuran_panjang_cucian_siarkaki_berbumbung" : coordinate.ukuran_panjang_cucian_siarkaki_berbumbung,
                "ukuran_panjang_cucian_stesenbas_teksi" : coordinate.ukuran_panjang_cucian_stesenbas_teksi,
                "ukuran_panjang_cucian_longkang" : coordinate.ukuran_panjang_cucian_longkang,
                "ukuran_panjang_potongrumput" : coordinate.ukuran_panjang_potongrumput,
                "ukuran_panjang_sampahkebun" : coordinate.ukuran_panjang_sampahkebun,
                "catatan" : coordinate.catatan,
                "rujuken_tarikh_serahan" : coordinate.rujuken_tarikh_serahan,
                "tarikh_semakandi_lapangant_keadeansemata_ada" : coordinate.tarikh_semakandi_lapangant_keadeansemata_ada,
                "tarikh_semakandi_lapangant_keadeansemata_tiada" : coordinate.tarikh_semakandi_lapangant_keadeansemata_tiada
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
""" ===============================<< getSapuanCucianCoordinates starts >>=============================== """
from sqlalchemy.sql import column
@token_required
def getSapuanCucianCoordinates(data):
    parlimen = data.parlimen
    lokasi = data.lokasi
    sapuan_cucian_list = ['Jalan','TPKK','Kaw Lapang','Sapuan Jejentas','Cucian Jejentas','Siar Kaki','Siar Kaki Berbumbung','Stesen Bas,Longkang']
    final = []
    sapuan_cucian_coordinates_list = []
    
    for sapuan_cucian_value in sapuan_cucian_list:
        if sapuan_cucian_value == 'Jalan':
            try:
                jalan_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_sapuan_jalan != '', Coordinates.ukuran_panjang_sapuan_jalan != '-', 
                                                                Coordinates.ukuran_panjang_sapuan_jalan != None, Coordinates.active==1):
                    jalan_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })
                if jalan_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'jalan': jalan_coordinates
                        }
                    )
                else:
                    jalan_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })
                    sapuan_cucian_coordinates_list.append(
                        {
                            'jalan': jalan_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
            
        if sapuan_cucian_value == 'TPKK':
            try:
                tpkk_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_sapuan_TPKK != '', Coordinates.ukuran_panjang_sapuan_TPKK != '-', 
                                                                Coordinates.ukuran_panjang_sapuan_TPKK != None, Coordinates.active==1):
                    tpkk_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })
                if tpkk_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'tpkk': tpkk_coordinates
                        }
                    )
                else:
                    tpkk_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })
                    sapuan_cucian_coordinates_list.append(
                        {
                            'tpkk': tpkk_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
            
        if sapuan_cucian_value == 'Kaw Lapang':
            try:
                kaw_lapang_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_sapuan_kaw_lapang_parkir != '', Coordinates.ukuran_panjang_sapuan_kaw_lapang_parkir != '-', 
                                                                Coordinates.ukuran_panjang_sapuan_kaw_lapang_parkir != None, Coordinates.active==1):
                    kaw_lapang_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })

                if kaw_lapang_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'kaw_lapang': kaw_lapang_coordinates
                        }
                    )
                else:
                    kaw_lapang_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })

                    sapuan_cucian_coordinates_list.append(
                        {
                            'kaw_lapang': kaw_lapang_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
            
        if sapuan_cucian_value == 'Sapuan Jejentas':
            try:
                sapuan_jejentas_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_sapuan_jejantas != '', Coordinates.ukuran_panjang_sapuan_jejantas != '-', 
                                                                Coordinates.ukuran_panjang_sapuan_jejantas != None, Coordinates.active==1):
                    sapuan_jejentas_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })

                if sapuan_jejentas_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'sapuan_jejentas': sapuan_jejentas_coordinates
                        }
                    )
                else:
                    sapuan_jejentas_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })

                    sapuan_cucian_coordinates_list.append(
                        {
                            'sapuan_jejentas': sapuan_jejentas_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
        
        if sapuan_cucian_value == 'Cucian Jejentas':
            try:
                cucian_jejentas_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_cucian_jejantas != '', Coordinates.ukuran_panjang_cucian_jejantas != '-', 
                                                                Coordinates.ukuran_panjang_cucian_jejantas != None, Coordinates.active==1):
                    cucian_jejentas_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })

                if cucian_jejentas_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'cucian_jejentas': cucian_jejentas_coordinates
                        }
                    )
                else:
                    cucian_jejentas_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })

                    sapuan_cucian_coordinates_list.append(
                        {
                            'cucian_jejentas': cucian_jejentas_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
        
        if sapuan_cucian_value == 'Siar Kaki':
            try:
                siar_kaki_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_cucian_siarkaki != '', Coordinates.ukuran_panjang_cucian_siarkaki != '-', 
                                                                Coordinates.ukuran_panjang_cucian_siarkaki != None, Coordinates.active==1):
                    siar_kaki_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })

                if siar_kaki_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'siar_kaki': siar_kaki_coordinates
                        }
                    )
                else:
                    siar_kaki_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })

                    sapuan_cucian_coordinates_list.append(
                        {
                            'siar_kaki': siar_kaki_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
        
        if sapuan_cucian_value == 'Siar Kaki Berbumbung':
            try:
                siar_kaki_berbumbung_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_cucian_siarkaki_berbumbung != '', Coordinates.ukuran_panjang_cucian_siarkaki_berbumbung != '-', 
                                                                Coordinates.ukuran_panjang_cucian_siarkaki_berbumbung != None, Coordinates.active==1):
                    siar_kaki_berbumbung_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })

                if siar_kaki_berbumbung_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'siar_kaki_berbumbung': siar_kaki_berbumbung_coordinates
                        }
                    )
                else:
                    siar_kaki_berbumbung_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })

                    sapuan_cucian_coordinates_list.append(
                        {
                            'siar_kaki_berbumbung': siar_kaki_berbumbung_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
            
        if sapuan_cucian_value == 'Stesen Bas':
            try:
                stesen_bas_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_cucian_stesenbas_teksi != '', Coordinates.ukuran_panjang_cucian_stesenbas_teksi != '-', 
                                                                Coordinates.ukuran_panjang_cucian_stesenbas_teksi != None, Coordinates.active==1):
                    stesen_bas_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })

                if stesen_bas_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'stesen_bas': stesen_bas_coordinates
                        }
                    )
                else:
                    stesen_bas_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })

                    sapuan_cucian_coordinates_list.append(
                        {
                            'stesen_bas': stesen_bas_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
            
        if sapuan_cucian_value == 'Longkang':
            try:
                longkang_coordinates = []
                for coordinate_info in Coordinates.query.filter(Coordinates.parlimen==parlimen, Coordinates.lokasi==lokasi, 
                                                                Coordinates.ukuran_panjang_cucian_longkang != '', Coordinates.ukuran_panjang_cucian_longkang != '-', 
                                                                Coordinates.ukuran_panjang_cucian_longkang != None, Coordinates.active==1):
                    longkang_coordinates.append({
                        'latitude': coordinate_info.latitude,
                        'longitude': coordinate_info.longitude
                    })

                if longkang_coordinates != []:
                    sapuan_cucian_coordinates_list.append(
                        {
                            'longkang': longkang_coordinates
                        }
                    )
                else:
                    longkang_coordinates.append({
                        'latitude': '',
                        'longitude': ''
                    })

                    sapuan_cucian_coordinates_list.append(
                        {
                            'longkang': longkang_coordinates
                        }
                    )

            except:
                logger.exception("Coordinates could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': 'Coordinates could not be fetched',
                }
                return response_object, 400
    # services['Service'] = sapuan_cucian_coordinates_list
    final.append({"parlimen": parlimen,
                  "lokasi": lokasi,
                 "services": sapuan_cucian_coordinates_list})    
    return jsonify(final)
    


""" ===============================<< getSapuanCucianCoordinates ends >>=============================== """
""" ===============================<< getMTKList Starts >>=============================== """

def getMTKList():
    try:
        mtk_user_info = MasterUser.query.with_entities(MasterUser.nama).filter_by(role='MerinyuMTK').all()
        mtk_user_list = list(itertools.chain(*mtk_user_info))
        logger.info("MTK User List fetched")
        return mtk_user_list
    except:
        logger.exception("MTK User List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "MTK User List could not be fetched"
        }
        return response_object, 400
    
""" ===============================<< getMTKList Ends >>=============================== """
""" ===============================<< MTB Officers List starts >>=============================== """
@token_required
def getMTBOfficersList():
    user = get_logged_in_user()
    id_mtk = user.no_kad_pengenalan

    officers_list = []

    mtk_user_info = MasterUser.query.with_entities(MasterUser.nama, MasterUser.parlimen,MasterUser.no_kad_pengenalan).filter_by(role='MerinyuMTK').all()
    for mtk in mtk_user_info:
        officers_list.append({'officer_name': mtk.nama, 'parlimen': mtk.parlimen, 'no_kad_pengenalan': mtk.no_kad_pengenalan})
    if user.role == 'Superadmin':
        try:
            for officer in db.session.query(OfficersList.officer_name,OfficersList.parlimen,OfficersList.no_ic_pegawai).distinct(OfficersList.no_ic_pegawai).filter_by(active=1):
                if officer.officer_name != 'SuperAdmin':
                    officers_list.append({
                        'officer_name': officer.officer_name,
                        'parlimen': officer.parlimen,
                        'no_kad_pengenalan': officer.no_ic_pegawai
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
    elif user.role == 'MerinyuMTK':
        try:
            for officer in db.session.query(OfficersList.officer_name,OfficersList.parlimen,OfficersList.no_ic_pegawai).distinct(OfficersList.no_ic_pegawai).filter_by(id_mtk=id_mtk, active=1):
                if officer.officer_name != 'SuperAdmin':
                    officers_list.append({
                        'officer_name': officer.officer_name,
                        'parlimen': officer.parlimen,
                        'no_kad_pengenalan': officer.no_ic_pegawai
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
    elif user.role == 'Analisis,MerinyuMTB,MerinyuMTK':
        try:
            for officer in db.session.query(OfficersList.officer_name,OfficersList.parlimen,OfficersList.no_ic_pegawai).distinct(OfficersList.no_ic_pegawai).filter_by(id_mtk=id_mtk, active=1):
                if officer.officer_name != 'SuperAdmin':
                    officers_list.append({
                        'officer_name': officer.officer_name,
                        'parlimen': officer.parlimen,
                        'no_kad_pengenalan': officer.no_ic_pegawai
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
    elif user.role == 'MerinyuMTB':
        try:
            for officer in db.session.query(OfficersList.officer_name,OfficersList.parlimen,OfficersList.no_ic_pegawai).distinct(OfficersList.no_ic_pegawai).filter_by(id_mtb=id_mtk, active=1):
                if officer.officer_name != 'SuperAdmin':
                    officers_list.append({
                        'officer_name': officer.officer_name,
                        'parlimen': officer.parlimen,
                        'no_kad_pengenalan': officer.no_ic_pegawai
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
        logger.debug("User Dont have permission to see Officers list")
        response_object = {
            'status': 'fail',
            'message': 'User Dont have permission to see Officers list',
            }
        return response_object, 400 
    
""" ===============================<< MTB Officers List ends >>=============================== """

@token_required
def get_mtk_list():
    try:
        officers_list = []
        for user in db.session.query(MasterUser).filter_by(role='MerinyuMTK'):
            officers_list.append({
                'officer_name': user.nama,
                'no_kad_pengenalan': user.no_kad_pengenalan,
            })
        # for officer in db.session.query(OfficersList.officer_name, OfficersList.parlimen).distinct(OfficersList.officer_name).filter_by(active=1):
        #     if officer.officer_name != 'SuperAdmin':
        #             officers_list.append({
        #                 'officer_name': officer.officer_name,
        #                 'parlimen': officer.parlimen,
        #             })
        logger.info("Officers list fetched")
        return jsonify(officers_list)
    except:
        logger.exception("Officers list could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Officers list could not be fetched',
        }
        return response_object, 400

""" ===============================<< list Pegawai  starts >>=============================== """
@token_required
def listPegawai():
    user = get_logged_in_user()
    id_mtk = user.no_kad_pengenalan
    if user.role == 'Superadmin':
        try:
            officers_list = []
            for officer in db.session.query(MasterUser.no_kad_pengenalan, MasterUser.nama, MasterUser.parlimen, MasterUser.role).distinct(MasterUser.nama).filter_by(active=1):
                if officer.role in ('MerinyuMTB', 'MerinyuMTK'):
                    officers_list.append({
                        'officer_name': officer.nama,
                        'parlimen': officer.parlimen,
                        'no_kad_pengenalan': officer.no_kad_pengenalan,
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
    elif user.role == 'MerinyuMTK':
        try:
            officers_list = []
            for officer in db.session.query(MasterUser.no_kad_pengenalan, MasterUser.nama, MasterUser.parlimen, MasterUser.role).distinct(MasterUser.nama).filter_by(zon=user.zon, active=1):
                if officer.role in ('MerinyuMTB', 'MerinyuMTK'):
                    officers_list.append({
                        'officer_name': officer.nama,
                        'parlimen': officer.parlimen,
                        'no_kad_pengenalan': officer.no_kad_pengenalan,
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
    elif user.role == 'Analisis,MerinyuMTB,MerinyuMTK':
        try:
            officers_list = []
            for officer in db.session.query(MasterUser.no_kad_pengenalan, MasterUser.nama, MasterUser.parlimen, MasterUser.role).distinct(MasterUser.nama).filter_by(zon=user.zon, active=1):
                if officer.role in ('MerinyuMTB', 'MerinyuMTK'):
                    officers_list.append({
                        'officer_name': officer.nama,
                        'parlimen': officer.parlimen,
                        'no_kad_pengenalan': officer.no_kad_pengenalan,
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
    elif user.role == 'MerinyuMTB':
        try:
            officers_list = []
            for officer in db.session.query(MasterUser.no_kad_pengenalan, MasterUser.nama, MasterUser.parlimen, MasterUser.role).distinct(MasterUser.nama).filter_by(zon=user.zon, active=1):
                if officer.role in ('MerinyuMTB'):
                    officers_list.append({
                        'officer_name': officer.nama,
                        'parlimen': officer.parlimen,
                        'no_kad_pengenalan': officer.no_kad_pengenalan,
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
""" ===============================<< MTB Officers Tarikh starts >>=============================== """
@token_required
def getMTBOfficersTarikh(officer_name):
    user = get_logged_in_user()
    if not officer_name:
        officer_name = user.no_kad_pengenalan
    try:
        tarikh_list = []
        for tarikh_data in db.session.query(InquiryInformation.tarikh).distinct().filter_by(no_ic_pegawai=officer_name, active=1):
            tarikh_list.append(date.strftime(tarikh_data.tarikh, "%Y-%m-%d"))
        logger.info("Officers tarikh fetched")
        return jsonify(tarikh_list)

    except:
        logger.exception("Officers tarikh could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Officers tarikh could not be fetched',
        }
        return response_object, 400
    
""" ===============================<< MTB Officers List ends >>=============================== """
""" ===============================<< getMTBOfficerInfo starts >>=============================== """

@token_required
def getMTBOfficerInfo():
    user = get_logged_in_user()
    id_mtk = user.no_kad_pengenalan
    try:
        officer_info = []
        if user.role == 'Superadmin':
            for officer in OfficersList.query.filter_by(active=1).order_by(desc(OfficersList.tarikh)):
                officer_info.append({
                    'officer_id': officer.officer_id,
                    'officer_name': officer.officer_name,
                    'id_mtb': officer.id_mtb,
                    'parlimen': officer.parlimen,
                    'date': date.strftime(officer.tarikh, "%Y-%m-%d"),
            })
        if user.role == 'MerinyuMTK':
            officer_info = []
            for officer in OfficersList.query.filter_by(id_mtk=id_mtk, active=1).order_by(desc(OfficersList.tarikh)):
                officer_info.append({
                    'officer_id': officer.officer_id,
                    'officer_name': officer.officer_name,
                    'id_mtb': officer.id_mtb,
                    'parlimen': officer.parlimen,
                    'date': date.strftime(officer.tarikh, "%Y-%m-%d"),
            })
        if user.role == 'Analisis,MerinyuMTB,MerinyuMTK':
            officer_info = []
            for officer in OfficersList.query.filter_by(id_mtk=id_mtk, active=1).order_by(desc(OfficersList.tarikh)):
                officer_info.append({
                    'officer_id': officer.officer_id,
                    'officer_name': officer.officer_name,
                    'id_mtb': officer.id_mtb,
                    'parlimen': officer.parlimen,
                    'date': date.strftime(officer.tarikh, "%Y-%m-%d"),
            })
        if user.role == 'MerinyuMTB':
            officer_info = []

            for officer in OfficersList.query.filter_by(id_mtb=user.no_kad_pengenalan, active=1).order_by(desc(OfficersList.tarikh)):
                officer_info.append({
                    'officer_id': officer.officer_id,
                    'officer_name': officer.officer_name,
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
""" ===============================<< getDailyMTBInquiryInforByMTK starts >>=============================== """

@token_required
def getDailyMTBInquiryInforByMTK(data):
    tarikh = data.tarikh
    officer_name = data.officer_name
    user = get_logged_in_user()
    if not officer_name:
        officer_name = user.no_kad_pengenalan
    
    try:
        inquiry_list_log = []
        for log in InquiryInformation.query.filter_by(tarikh=tarikh,no_ic_pegawai=officer_name, active=1):
            if log.inquiry_id or log.complaint_id:
                inquiry_list_log.append({
                    'id': log.inquiry_id,
                    'tarikh': log.tarikh,
                    'masa': log.masa,
                    'lokasi_aduan': log.lokasi_aduan,
                    'lokasi_siasatan': log.lokasi_siasatan,
                    'borang_siasatan': log.borang_siasatan,
                    'rujukan': getRujukan(log.parlimen, log.inquiry_information_id)
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

def getRujukan(parlimen, id):
    if not parlimen:
        return 'JKAS/X/XXX/' + str(id).zfill(5)
    if parlimen.lower() in ('segambut','batu','kepong', 'wangsa maju'):
        return 'JKAS/U/' + getParlimenAbbreviation(parlimen=parlimen) + '/' + str(id).zfill(5)
    if parlimen.lower() in ('bukit bintang','setiawangsa','titiwangsa'):
        return 'JKAS/T/' + getParlimenAbbreviation(parlimen=parlimen) + '/' + str(id).zfill(5)
    if parlimen.lower() in ('seputeh','lembah pantai','cheras', 'bandar tun razak'):
        return 'JKAS/S/' + getParlimenAbbreviation(parlimen=parlimen) + '/' + str(id).zfill(5)

def getParlimenAbbreviation(parlimen):
    if parlimen.lower() == 'Segambut'.lower():
        return 'SEG'
    if parlimen.lower() == 'Batu'.lower():
        return 'BT'
    if parlimen.lower() == 'Kepong'.lower():
        return 'KEP'
    if parlimen.lower() == 'Wangsa Maju'.lower():
        return 'WM'
    if parlimen.lower() == 'Titiwangsa'.lower():
        return 'TW'
    if parlimen.lower() == 'Setiawangsa'.lower():
        return 'SW'
    if parlimen.lower() == 'Bukit Bintang'.lower():
        return 'BB'
    if parlimen.lower() == 'Bandar Tun Razak'.lower():
        return 'BTR'
    if parlimen.lower() == 'Cheras'.lower():
        return 'CHE'
    if parlimen.lower() == 'Lembah Pantai'.lower():
        return 'LP'
    if parlimen.lower() == 'Seputeh'.lower():
        return 'SEP'
    return ''

""" ===============================<< getDailyMTBInquiryInforByMTK ends >>=============================== """
""" ===============================<< getDailyMTBInquiryInforByMTB starts >>=============================== """

@token_required
def getDailyMTBInquiryInforByMTB(data):
    user = get_logged_in_user()
    tarikh = data.tarikh
    id_mtb = data.id_mtb
    if not id_mtb:
        id_mtb = get_logged_in_user().no_kad_pengenalan
    
    try:
        inquiry_list_log = []
        for log in InquiryInformation.query.filter_by(tarikh=tarikh,no_ic_pegawai=id_mtb, active=1):
            if log.inquiry_id or log.complaint_id:
                inquiry_list_log.append({
                    'id': log.inquiry_information_id,
                    'tarikh': log.tarikh,
                    'masa': log.masa,
                    'lokasi_aduan': log.lokasi_aduan,
                    'lokasi_siasatan': log.lokasi_siasatan,
                    'borang_siasatan': log.borang_siasatan,
                    'complaint_id': log.complaint_id,
                    'inquiry_id': log.inquiry_id,
                    'rujukan': getRujukan(log.parlimen, log.inquiry_information_id)
                })
        # inquiry_list_log = []
        # for log in InquiryInformation.query.filter_by(tarikh=tarikh,id_mtb=id_mtb, active=1):
        #     inquiry_list_log.append({
        #         'tarikh': log.tarikh,
        #         'masa': log.masa,
        #         'lokasi_aduan': log.lokasi_aduan,
        #         'lokasi_siasatan': log.lokasi_siasatan,
        #         'borang_siasatan': log.borang_siasatan
        #     })
        logger.info("Inquiry Information fetched")
        return jsonify(inquiry_list_log)
    except:
        logger.exception("Inquiry Information could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Inquiry Information could not be fetched',
        }
        return response_object, 400
        
""" ===============================<< getDailyMTBInquiryInforByMTB ends >>=============================== """
""" ===============================<< Add Complaint Investigation starts >>=============================== """
@token_required
def addComplaintInvestigation(data):
    user = get_logged_in_user()

    name = user.no_kad_pengenalan
    
    user_type = user.user_type
    role = user.role
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    masa_siasatan = datetime.now(tz).strftime("%H:%M:%S")
    time = datetime.now(tz).strftime("%H:%M:%S")
    
    id_pegawai = data.id_pegawai
    jenis_kawasan = data.jenis_kawasan
    parlimen = data.parlimen
    if not parlimen:
        parlimen = user.parlimen
    pengadu_nama=data.pengadu_nama
    pengadu_alamat=data.pengadu_alamat
    no_telefon=data.no_telefon
    emel=data.emel
    no_faksimili=data.no_faksimili
    sumber_aduan=data.sumber_aduan
    lain_lain=data.lain_lain
    tarikh_aduan=data.tarikh_aduan
    tarikh_terima=data.tarikh_terima
    no_rujukan=data.no_rujukan
    lokasi_aduan=data.lokasi_aduan
    keterangan_aduan=data.keterangan_aduan
    zon=data.zon
    tarikh_siasatan=data.tarikh_siasatan
    nama_pegawai=data.nama_pegawai
    if not nama_pegawai:
        nama_pegawai = user.nama
    lokasi_siasatan=data.lokasi_siasatan
    laporan_siasatan=data.laporan_siasatan
    tindakan=data.tindakan
    susulan=data.susulan
    ullasan_penyelia=data.ullasan_penyelia
    ullasan_ketua_seksyen=data.ullasan_ketua_seksyen
    ulasanKetua_unitf1=data.ulasanKetua_unitf1
    gambar = data.gambar    
    cause = data.cause
    picture1 = data.picture1
    picture2 = data.picture2
    picture3 = data.picture3
    try:
        # if user.no_kad_pengenalan == 'SUPERADMIN':
        #     officer_name = nama_pegawai
        #     id_mtb = id_pegawai
        #     parlimen = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_pegawai).first().parlimen
        #     mtbUserInfo = db.session.query(OfficersList).filter_by(id_mtb=id_mtb).all()
        #     if not mtbUserInfo:
        #         id_mtk = id_pegawai
        #     for _ in mtbUserInfo:
        #         id_mtk = _.id_mtk
        # if user.role == 'MerinyuMTK' or user.role == 'Analisis,MerinyuMTB,MerinyuMTK':
        #     officer_name = nama_pegawai
        #     id_mtb = db.session.query(MasterUser).filter_by(nama=officer_name).first().no_kad_pengenalan
        #     parlimen = db.session.query(MasterUser).filter_by(nama=officer_name).first().parlimen
        #     id_mtk = user.no_kad_pengenalan
        #     mtbUserInfo = db.session.query(OfficersList).filter_by(id_mtb=id_mtb).all()
        #     if not mtbUserInfo:
        #         id_mtk = id_pegawai
        #     if not mtbUserInfo:
        #         id_mtk = id_pegawai
        # if user.role == 'MerinyuMTB':
        #     id_mtb=user.no_kad_pengenalan
        #     parlimen = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_mtb).first().parlimen
        #     mtkUserInfo = db.session.query(OfficersList).filter_by(id_mtb=id_mtb).all()
        #     if not mtkUserInfo:
        #         id_mtk = id_pegawai
        #     for _ in mtkUserInfo:
        #         id_mtk = _.id_mtk
        #     officer_name = user.nama
        #     compound_officer_name = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_mtk).first().nama
        # else:
        #     id_mtb=user.no_kad_pengenalan
        #     parlimen = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_mtb).first().parlimen
        #     mtkUserInfo = db.session.query(OfficersList).filter_by(id_mtb=id_mtb).all()
        #     if not mtkUserInfo:
        #         id_mtk = id_pegawai
        #     for _ in mtkUserInfo:
        #         id_mtk = _.id_mtk
        #     officer_name = user.nama
        
        # if not officer_name:
        #     officer_name = user.nama
        complaint_investigation_form = Inquiry(parlimenA=parlimen, jenis_kawasan=jenis_kawasan, picture1=picture1,picture2=picture2,picture3=picture3,no_ic_pegawai=id_pegawai,
            pengadu_nama=pengadu_nama,pengadu_alamat=pengadu_alamat,no_telefon=no_telefon,emel=emel,no_faksimili=no_faksimili,
            sumber_aduan=sumber_aduan,lain_lain=lain_lain,tarikh_aduan=tarikh_aduan,tarikh_terima=tarikh_terima,no_rujukan=no_rujukan,
            lokasi_aduan=lokasi_aduan,keterangan_aduan=keterangan_aduan,zon=zon,tarikh_siasatan=tarikh_siasatan,masa_siasatan=masa_siasatan,
            nama_pegawai=nama_pegawai,id_mtb='',lokasi_siasatan=lokasi_siasatan,laporan_siasatan=laporan_siasatan,tindakan=tindakan,
            susulan=susulan,ullasan_penyelia=ullasan_penyelia,ullasan_ketua_seksyen=ullasan_ketua_seksyen,ullasan_ketua_unit=ulasanKetua_unitf1,
            gambar=gambar,cause=cause,inserted_by=name,inserted_date=today, active=1, inquiry_type='complaint', tarikh=tarikh_siasatan)
        db.session.add(complaint_investigation_form)
        db.session.commit()
        
        inquiry_info = InquiryInformation(inquiry_id=complaint_investigation_form.inquiry_id, inquiry_type='complaint', no_ic_pegawai=id_pegawai,
            id_mtb='', officer_name='', tarikh=tarikh_siasatan, parlimen=parlimen, masa=time, 
            lokasi_aduan=lokasi_aduan,lokasi_siasatan=lokasi_siasatan,borang_siasatan=lokasi_aduan ,inserted_by=name,inserted_date=today, active=1)
        db.session.add(inquiry_info)
        db.session.commit()
        
        statement = "Borang siasatan aduan baru berjaya ditambahkan"
        log_info = LogPengguna(id_pengguna=name, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()

        logger.info('Complaint Investigation Form Added')
        response_object = {
                'status': 'success',
                'message': 'complaint_investigation_added',
            }
        return response_object, 201
    except:
        logger.exception("Complaint Investigation not added")
        response_object = {
            'status': 'fail',
            'message': 'complaint_investigation_not_added',
        }
        return response_object, 400
        

@token_required
def updateComplaintComments(data):
    user = get_logged_in_user()
    if user.role == "MerinyuMTK" or user.role == 'Superadmin':
        current_complaint = db.session.query(Inquiry).filter_by(inquiry_id=data.formId).first()
        if data.ulasanPenyelia:
            current_complaint.ullasan_penyelia = data.ulasanPenyelia
        if data.ulasanKetuaSeksyen:
            current_complaint.ullasan_ketua_seksyen = data.ulasanKetuaSeksyen
        if data.ulasanKetuaUnit:
            current_complaint.ullasan_ketua_unit = data.ulasanKetuaUnit
        db.session.commit()
        logging.info('Updated complaint ' + str(data.formId))
    return {}, 204

""" ===============================<< Add Complaint Investigation ends >>=============================== """
""" ===============================<< Add Complaint Investigation starts >>=============================== """
@token_required
def add2ndComplaintInvestigation(data):
    user = get_logged_in_user()
    name = user.no_kad_pengenalan
    # parlimen = user.parlimen
    
    user_type = user.user_type
    role = user.role
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    time = datetime.now(tz).strftime("%H:%M:%S")
    
    id_pegawai = data.id_pegawai
    parlimenA = data.parlimenA
    zon= data.zon
    tarikh_siasatan= data.tarikh_siasatan
    lokasi_siasatan= data.lokasi_siasatan
    picture1 = data.picture1
    picture2 = data.picture2
    picture3 = data.picture3
    laporan_siasatan = data.laporan_siasatan
    tindakan = data.tindakan

    locator = Nominatim(user_agent="myGeocoder")
    coordinates = lokasi_siasatan
    location_info = []
    try:
        location = locator.reverse(coordinates)
        if 'village' in location.raw['address']:
            village = location.raw['address']['village']
            location_info.append(village)
        if 'building' in location.raw['address']:
            building = location.raw['address']['building']
            location_info.append(building)
        if 'road' in location.raw['address']:
            road = location.raw['address']['road']
            location_info.append(road)
        if 'suburb' in location.raw['address']:
            suburb = location.raw['address']['suburb']
            location_info.append(suburb)
    except:
        logging.error("Unable to geocode location.")
    lokasi_aduan = ','.join(map(str, location_info))
    # bulan = calendar.month_abbr[tarikh_siasatan.month].upper()
    # tahun = tarikh_siasatan.year

    # if user.role == 'Superadmin':
    #     id_mtb = id_pegawai
    #     parlimen = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_pegawai).first().parlimen
    #     mtbUserInfo = db.session.query(OfficersList).filter_by(id_mtb=id_mtb).all()
    #     if len(mtbUserInfo) == 0:
    #         id_mtk = id_pegawai
    #     for _ in mtbUserInfo:
    #         id_mtk = _.id_mtk
    #     officer_name = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_pegawai).first().nama
    #     # compound_officer_name = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_mtk).first().nama
    # if user.role == 'MerinyuMTK' or user.role == 'Analisis,MerinyuMTB,MerinyuMTK':
    #     id_mtb = id_pegawai
    #     parlimen = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_pegawai).first().parlimen
    #     id_mtk = user.no_kad_pengenalan
    #     officer_name = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_pegawai).first().nama
    #     # compound_officer_name = user.nama
    # if user.role == 'MerinyuMTB':
    #     id_mtb=user.no_kad_pengenalan
    #     parlimen = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_mtb).first().parlimen
    #     mtkUserInfo = db.session.query(OfficersList).filter_by(id_mtb=id_mtb).all()
    #     if len(mtbUserInfo) == 0:
    #         id_mtk = id_pegawai
    #     for _ in mtkUserInfo:
    #         id_mtk = _.id_mtk
    #     officer_name = user.nama
    #     # compound_officer_name = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_mtk).first().nama

    pegawai = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_pegawai).first()
    parlimen = pegawai.parlimen
    officer_name = pegawai.nama

    if not officer_name:
        officer_name = user.nama
    if not parlimen:
        parlimen = parlimenA

    try:
        # officers_list = OfficersList(
        #     id_mtk='', id_mtb='',no_ic_pegawai=id_pegawai, officer_name=officer_name, parlimen=parlimen, tarikh=tarikh_siasatan, inserted_by=name,inserted_date=today, active=1
        # )
        # db.session.add(officers_list)
        # db.session.commit()
        complaint_investigation_form = Inquiry(parlimenA=parlimen,tarikh=tarikh_siasatan,
            tarikh_siasatan=tarikh_siasatan,masa_siasatan=time, no_ic_pegawai=id_pegawai,
            lokasi_siasatan=lokasi_siasatan,laporan_siasatan=laporan_siasatan,tindakan=tindakan,
            zon=zon, inserted_by=name,inserted_date=today, active=1, picture1=picture1, picture2=picture2, picture3=picture3, inquiry_type='daily')
        db.session.add(complaint_investigation_form)
        db.session.commit()
        
        inquiry_info = InquiryInformation(inquiry_id=complaint_investigation_form.inquiry_id, no_ic_pegawai=id_pegawai, id_mtb='', officer_name=officer_name, tarikh=tarikh_siasatan, 
            parlimen=parlimen, masa=time, lokasi_siasatan=lokasi_siasatan, lokasi_aduan=lokasi_aduan, 
            inserted_by=name,inserted_date=today, active=1, inquiry_type='daily')
        db.session.add(inquiry_info)
        db.session.commit()
        
        # newCompoundForm = CompoundForm(id_mtb=id_mtb,id_mtk=compound_officer_name, latitude=latitude,longitude=longitude,
        #               parlimen=parlimenA,tarikh=tarikh_siasatan,bulan=bulan,tahun=tahun,waktu=time,
        #               sek82_5=False,sek69=False, sek47_1a=False,sek47_1b=False,sek47_1c = False,sek47_1d = False,sek47_1e = False,sek47_1g = False,sek47_2a = False,sek47_2b = False,uuk8 = False,uuk9 = False,uuk3 = False,
        #               sek46_1b = False,sek46_1c = False,sek46_1d = False,sek46_1e = False,sek46_1f = False,sek46_1g = False,uuk5_a  = False,uuk5_b  = False,uuk5_c = False,uuk33 = False,uuk34 = False,uuk35 = False, zon=zon,
        #               inserted_by=name,inserted_date=today, active=1)
        # db.session.add(newCompoundForm)
        # db.session.commit()
        statement = "Borang siasatan aduan baru berjaya ditambahkan"
        log_info = LogPengguna(id_pengguna=name, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()

        logger.info('Complaint Investigation Form Added')
        response_object = {
                'status': 'success',
                'message': 'complaint_investigation_added',
            }
        return response_object, 201
    except:
        logger.exception("Complaint Investigation not added")
        response_object = {
            'status': 'fail',
            'message': 'complaint_investigation_not_added',
        }
        return response_object, 400
        

""" ===============================<< Add 2nd Complaint Investigation ends >>=============================== """
""" ===============================<< Add 3rd Complaint Investigation starts >>=============================== """
@token_required
def add3rdComplaintInvestigation(data):
    user = get_logged_in_user()
    name = user.no_kad_pengenalan
    parlimen = user.parlimen
    if user.no_kad_pengenalan == 'SUPERADMIN':
        id_mtb=user.no_kad_pengenalan
        id_mtk = 'SUPERADMIN'
        officer_name = 'SuperAdmin'

    else:
        if user.role == 'MerinyuMTB':
            id_mtb=user.no_kad_pengenalan
            mtbUserInfo = db.session.query(OfficersList).filter_by(id_mtb=id_mtb, active=1).all()
            for _ in mtbUserInfo:
                id_mtk = _.id_mtk
                officer_name = _.officer_name
        else:
            id_mtb=''
            id_mtk = user.no_kad_pengenalan
            officer_name = user.nama

    user_type = user.user_type
    role = user.role
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    time = datetime.now(tz).strftime("%H:%M:%S")
    
    pengadu_nama = data.pengadu_nama
    pengadu_alamat = data.pengadu_alamat
    no_rujukan = data.no_rujukan
    no_telefon = data.no_telefon
    emel = data.emel
    no_faksimili = data.no_faksimili
    sumber_aduan = data.sumber_aduan
    lain_lain = data.lain_lain
    tarikh_aduan = data.tarikh_aduan
    tarikh_terima = data.tarikh_terima
    lokasi_aduan = data.lokasi_aduan
    keterangan_aduan = data.keterangan_aduan
    ullasan_penyelia = data.ullasan_penyelia
    ullasan_ketua_seksyen = data.ullasan_ketua_seksyen
    gambar= data.gambar
    cause= data.cause
    
    try:
        # officers_list = OfficersList(
        #     id_mtk=id_mtk, id_mtb=id_mtb, officer_name=officer_name, parlimen=parlimen, tarikh=today, inserted_by=name,inserted_date=today, active=1
        # )
        # db.session.add(officers_list)
        # db.session.commit()
        complaint_investigation_form = Inquiry(
            pengadu_nama=pengadu_nama,pengadu_alamat=pengadu_alamat,no_telefon=no_telefon,emel=emel,no_faksimili=no_faksimili,
            sumber_aduan=sumber_aduan,lain_lain=lain_lain,tarikh_aduan=tarikh_aduan,tarikh_terima=tarikh_terima,no_rujukan=no_rujukan,
            lokasi_aduan=lokasi_aduan,keterangan_aduan=keterangan_aduan,tarikh_siasatan=today,masa_siasatan=time,id_mtb=id_mtb,
            ullasan_penyelia=ullasan_penyelia,ullasan_ketua_seksyen=ullasan_ketua_seksyen,gambar=gambar,cause=cause,
            inserted_by=name,inserted_date=today, active=1)
        db.session.add(complaint_investigation_form)
        db.session.commit()
        
        # inquiry_info = InquiryInformation(
        #     id_mtb=id_mtb, officer_name=officer_name, tarikh=today, parlimen=parlimen, masa=time, lokasi_aduan=lokasi_aduan,borang_siasatan=lokasi_aduan ,inserted_by=name,inserted_date=today, active=1)
        # db.session.add(inquiry_info)
        # db.session.commit()
        
        statement = "Borang siasatan aduan baru berjaya ditambahkan"
        log_info = LogPengguna(id_pengguna=name, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()

        logger.info('Complaint Investigation Form Added')
        response_object = {
                'status': 'success',
                'message': 'complaint_investigation_added',
            }
        return response_object, 201
    except:
        logger.exception("Complaint Investigation not added")
        response_object = {
            'status': 'fail',
            'message': 'complaint_investigation_not_added',
        }
        return response_object, 400
        

""" ===============================<< Add 3rd Complaint Investigation ends >>=============================== """
""" ===============================<< get Complaint Investigation Form starts >>=============================== """

@token_required
def getComplaintInvestigation(data):
    inquiry_id = data.inquiry_id

    try:
        inquiry = db.session.query(Inquiry).filter_by(inquiry_id=inquiry_id, active=1).first()
    except:
        logger.exception('No data found with given id_mtb and tarikh_siasatan')
        response_object = {
                'status': 'fail',
                'message': 'No data found with given id_mtb and tarikh_siasatan',
            }
        return response_object, 404
    logging.info('Inquiry: ' + str(inquiry))
    if inquiry:
        inquiries = []
        pegawai = db.session.query(MasterUser).filter_by(no_kad_pengenalan=inquiry.no_ic_pegawai).first()
        inquiries.append({
            'inquiry_id': inquiry.inquiry_id,
            'parlimen': inquiry.parlimenA,
            'tarikh': inquiry.tarikh,
            'pengadu_nama': inquiry.pengadu_nama,
            'pengadu_alamat': inquiry.pengadu_alamat,
            'no_telefon': inquiry.no_telefon,
            'tarikh_terima_aduan': inquiry.tarikh_terima_aduan,
            'no_rujukan': inquiry.no_rujukan,
            'emel': inquiry.emel,
            'no_faksimili': inquiry.no_faksimili,
            'sumber_aduan': inquiry.sumber_aduan,
            'lain_lain': inquiry.lain_lain,
            'tarikh_aduan': inquiry.tarikh_aduan,
            'lokasi_aduan': inquiry.lokasi_aduan,
            'keterangan_aduan': inquiry.keterangan_aduan,
            'zon': inquiry.zon,
            'tarikh_siasatan': inquiry.tarikh_siasatan,
            'masa_siasatan': inquiry.masa_siasatan,
            'nama_pegawai': pegawai.nama,
            'id_mtb': inquiry.id_mtb,
            'lokasi_siasatan': inquiry.lokasi_siasatan,
            'laporan_siasatan': inquiry.laporan_siasatan,
            'tindakan': inquiry.tindakan,
            'susulan': inquiry.susulan,
            'no_ic_pegawai': inquiry.no_ic_pegawai,
            'jenis_kawasan': inquiry.jenis_kawasan,
            'picture1': inquiry.picture1,
            'picture2': inquiry.picture2,
            'picture3': inquiry.picture3,
            "tarikh_terima":inquiry.tarikh_terima,
            "nama_pegawai":pegawai.nama,
            "sebelum_siasatan":inquiry.sebelum_siasatan,
            "ullasan_penyelia":inquiry.ullasan_penyelia,
            "ullasan_ketua_seksyen":inquiry.ullasan_ketua_seksyen,
            "ullasan_ketua_unit":inquiry.ullasan_ketua_unit,
            "ulasan_timbalan":inquiry.ulasan_timbalan,
            "inquiry_type": inquiry.inquiry_type
        })
        return jsonify(inquiries)

""" ===============================<< get Complaint Investigstion Form ends >>=============================== """
""" ===============================<< Update Complaint Investigation Form starts >>=============================== """

@token_required
def updateComplaintInvestigation(form_id,data):
    user = get_logged_in_user()
    name = user.no_kad_pengenalan
    parlimen = user.parlimen
    user_type = user.user_type

    pengadu_nama=data.pengadu_nama
    pengadu_alamat=data.pengadu_alamat
    no_telefon=data.no_telefon
    tarikh_terima_aduan=data.tarikh_terima_aduan
    emel=data.emel
    no_faksimili=data.no_faksimili
    sumber_aduan=data.sumber_aduan
    lain_lain=data.lain_lain
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
    ulasan_timbalan=data.ulasan_timbalan
    role = user.role
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
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
            complaint_Investigation_obj.lain_lain = lain_lain
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
            complaint_Investigation_obj.ulasan_timbalan = ulasan_timbalan
            complaint_Investigation_obj.updated_date = today
            complaint_Investigation_obj.updated_by = name
            db.session.commit()

            statement = "Borang siasatan aduan "+form_id+" berjaya dikemas kini"
            log_info = LogPengguna(id_pengguna=name, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info("Complaint investigation form updated successfully.")
            response_object = {
                'status': 'success',
                'message': 'complaint_investigation_updated',
            }
            return response_object, 200
        except:
            logger.exception("Complaint investigation form could not be updated.")
            response_object = {
                'status': 'fail',
                'message': 'complaint_investigation_not_updated',
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
    logger.info('Fetching via ' + str(tarikh) + ', ic=' + id_mtb + ', parlimen=' + parlimen)
    try:
        compound_list = []
        for log in CompoundInformation.query.filter_by(tarikh=tarikh,no_ic_pegawai=id_mtb, parlimen=parlimen, active=1):
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
    id_mtb = user.nama
    parlimen = user.parlimen
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
    id_pegawai = data.id_pegawai
    if db.session.query(CompoundInformation).filter_by(no_notis_bas=no_notis_bas).first():
        abort(HTTPStatus.CONFLICT, f"no notis bas {no_notis_bas} is already used")
    user= get_logged_in_user()
    kepada = data.kepada
    company_no = data.company_no
    alamat = data.alamat
                
    parlimen = data.parlimen
    addSeksyen = data.addSeksyen
    butir_butir_kesalahan = data.butir_butir_kesalahan
    tarikh = data.tarikh
    month_num = tarikh.month
    bulan =  calendar.month_abbr[month_num].upper()
    tahun = tarikh.year
    waktu = data.waktu
    tempat = data.tempat
    sek47_1a = data.sek47_1a
    sek47_1c = data.sek47_1c
    sek47_1d = data.sek47_1d
    sek47_1e = data.sek47_1e
    sek47_1g = data.sek47_1g
    sek47_2a = data.sek47_2a
    sek47_2b = data.sek47_2b
    uuk8 = data.uuk8
    uuk9 = data.uuk9
    uuk3 = data.uuk3
    sek46_1b = data.sek46_1b
    sek46_1c = data.sek46_1c
    sek46_1d = data.sek46_1d
    sek46_1e = data.sek46_1e
    sek46_1f = data.sek46_1f
    sek46_1g = data.sek46_1g
    uuk5_a  = data.uuk5_a
    uuk5_b  = data.uuk5_b
    uuk5_c = data.uuk5_c
    uuk33 = data.uuk33
    uuk34 = data.uuk34
    uuk35 = data.uuk35
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        user_type = user.user_type
        role = user.role
        
        coordinate_data = Coordinates.query.filter_by(parlimen=parlimen).first()
        latitude = coordinate_data.latitude
        longitude = coordinate_data.longitude
        
        newCompoundList = CompoundList(id_mtk='',id_mtb='',officer_name='',no_ic_pegawai=id_pegawai,parlimen=parlimen,tarikh=tarikh,inserted_by=id_card_no,inserted_date=today, active=1)
        db.session.add(newCompoundList)
        db.session.commit()

        newCompoundInfo = CompoundInformation(id_mtb='',officer_name='',id_mtk='',no_ic_pegawai=id_pegawai,parlimen=parlimen,tarikh=tarikh,masa=waktu,
                                              no_notis_bas=no_notis_bas,inserted_by=id_card_no,inserted_date=today, active=1)
        db.session.add(newCompoundInfo)
        db.session.commit()
        
        newCompoundForm = CompoundForm(no_notis_bas=no_notis_bas,kepada=kepada,company_no=company_no,alamat=alamat,id_mtb='',officer_name='',id_mtk='', no_ic_pegawai=id_pegawai,
                      parlimen=parlimen,tarikh=tarikh,bulan=bulan,tahun=tahun,waktu=waktu,tempat=tempat,latitude=latitude,longitude=longitude,addSeksyen=addSeksyen,butir_butir_kesalahan=butir_butir_kesalahan,
                      sek82_5=False,sek69=False, sek47_1a=sek47_1a,sek47_1b=False,sek47_1c = sek47_1c,sek47_1d = sek47_1d,sek47_1e = sek47_1e,sek47_1g = sek47_1g,sek47_2a = sek47_2a,sek47_2b = sek47_2b,uuk8 = uuk8,uuk9 = uuk9,uuk3 = uuk3,
                      sek46_1b = sek46_1b,sek46_1c = sek46_1c,sek46_1d = sek46_1d,sek46_1e = sek46_1e,sek46_1f = sek46_1f,sek46_1g = sek46_1g,uuk5_a  = uuk5_a,uuk5_b  = uuk5_b,uuk5_c = uuk5_c,uuk33 = uuk33,uuk34 = uuk34,uuk35 = uuk35,
                      inserted_by=id_card_no,inserted_date=today, active=1)
        
        db.session.add(newCompoundForm)
        db.session.commit()

        statement = "Borang kompaun MTB baru berjaya ditambahkan."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()


        logger.info("MTB Compound Form added Successfully")
        response_object = {
            'status': 'success',
            'message': 'compound_form_added',
        }
        return response_object, 201
    except:
        logger.exception("MTB Compound Form not added")
        response_object = {
            'status': 'fail',
            'message': 'compound_form_not_added',
        }
        return response_object, 400
    
""" ===============================<< Add MTB Compound Form ends =============================== """
""" ===============================<< getMTBCompoundList starts >>=============================== """
@token_required
def getMTBCompoundList():
    user = get_logged_in_user()
    id_mtk = user.nama
    if user.role == 'Superadmin':
        try:
            officers_list = []
            for officer in db.session.query(CompoundList.officer_name,CompoundList.no_ic_pegawai,CompoundList.parlimen).distinct(CompoundList.no_ic_pegawai).filter_by(active=1):
                if officer.no_ic_pegawai:
                    pegawai = db.session.query(MasterUser).filter_by(no_kad_pengenalan=officer.no_ic_pegawai,active=1).first()
                    officers_list.append({
                        'no_ic_pegawai': officer.no_ic_pegawai,
                        'officer_name': pegawai.nama,
                        'parlimen': officer.parlimen,
                    })
            logger.info("Compound list fetched")
            return jsonify(officers_list)

        except:
            logger.exception("Compound list could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Compound list could not be fetched',
            }
            return response_object, 400
    elif user.role == 'MerinyuMTK':
        try:
            officers_list = []
            officer_ids = []
            for officer in db.session.query(MasterUser.no_kad_pengenalan, MasterUser.nama, MasterUser.parlimen, MasterUser.role).distinct(MasterUser.nama).filter_by(zon=user.zon, active=1):
                officer_ids.append(officer.no_kad_pengenalan)

            for officer in db.session.query(CompoundList.no_ic_pegawai,CompoundList.parlimen).distinct(CompoundList.no_ic_pegawai).filter(CompoundList.no_ic_pegawai.in_(officer_ids)):
                pegawai = db.session.query(MasterUser).filter_by(no_kad_pengenalan=officer.no_ic_pegawai).first()
                officers_list.append({
                    'no_ic_pegawai': officer.no_ic_pegawai,
                    'officer_name': pegawai.nama,
                    'parlimen': officer.parlimen,
                })
            logger.info("Officers list fetched")
            return jsonify(officers_list)

        except:
            logger.exception("Compound list could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Compound list could not be fetched',
            }
            return response_object, 400
    elif user.role == 'Analisis,MerinyuMTB,MerinyuMTK':
        try:
            officers_list = []
            for officer in db.session.query(CompoundList.officer_name,CompoundList.parlimen).distinct(CompoundList.officer_name).filter_by(id_mtk=id_mtk, active=1):
                if officer.officer_name != 'SuperAdmin':
                    officers_list.append({
                        'officer_name': officer.officer_name,
                        'parlimen': officer.parlimen,
                    })
            logger.info("Officers list fetched")
            return jsonify(officers_list)

        except:
            logger.exception("Compound list could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Compound list could not be fetched',
            }
            return response_object, 400
    elif user.role == 'MerinyuMTB':
        try:
            officers_list = []
            for officer in db.session.query(CompoundList.officer_name,CompoundList.parlimen).distinct(CompoundList.officer_name).filter_by(no_ic_pegawai=user.no_kad_pengenalan, active=1):
                if officer.officer_name != 'SuperAdmin':
                    officers_list.append({
                        'officer_name': user.nama,
                        'parlimen': officer.parlimen,
                    })
            logger.info("Compound list fetched")
            return jsonify(officers_list)

        except:
            logger.exception("Compound list could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Compound list could not be fetched',
            }
            return response_object, 400
        
    else:
        logger.debug("User Dont have permission to see Compound list")
        response_object = {
            'status': 'fail',
            'message': 'User Dont have permission to see Compound list',
            }
        return response_object, 400 
    
""" ===============================<< getMTBCompoundList ends >>=============================== """
""" ===============================<< getMTBCompoundsTarikh starts >>=============================== """
@token_required
def getMTBCompoundsTarikh(officer_name):
    if not officer_name:
        user = get_logged_in_user()
        officer_name = user.no_kad_pengenalan
    try:
        tarikh_list = []
        for tarikh_data in db.session.query(CompoundList.tarikh).distinct().filter_by(no_ic_pegawai=officer_name,active=1):
            tarikh_list.append(date.strftime(tarikh_data.tarikh, "%Y-%m-%d"))
        logger.info("Compound tarikh fetched")
        return jsonify(tarikh_list)

    except:
        logger.exception("Compound tarikh could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Compound tarikh could not be fetched',
        }
        return response_object, 400
    
""" ===============================<< getMTBCompoundsTarikh ends >>=============================== """
""" ===============================<< listComplaintDate starts >>=============================== """
@token_required
def listComplaintDate():
    user = get_logged_in_user()
    try:
        tarikh_list = []
        for tarikh_data in db.session.query(OfficersList.tarikh).distinct().filter_by(active=1):
            tarikh_list.append({
                "date": date.strftime(tarikh_data.tarikh, "%Y-%m-%d")
            })
        logger.info("list of tarikh fetched")
        return jsonify(tarikh_list)
    except:
        logger.exception("list of tarikh could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'list of tarikh could not be fetched',
        }
        return response_object, 400
    
""" ===============================<< listComplaintDate ends >>=============================== """
""" ===============================<< get MTB Compound Form starts >>=============================== """
@token_required
def getCompoundForm(no_notis_bas):
    try:
        compound_form_data = CompoundForm.query.filter_by(no_notis_bas=no_notis_bas).first()
    except:
        logger.exception('Compound form not found')
        response_object = {
                'status': 'fail',
                'message': f'No Notis Bas {no_notis_bas} does not contain any information',
            }
        return response_object, 404 
    if compound_form_data: 
        try:
            compound_list = []
            for compound_info in CompoundForm.query.filter_by(no_notis_bas=no_notis_bas, active=1):
                officer = MasterUser.query.filter_by(no_kad_pengenalan=compound_info.no_ic_pegawai).first()
                compound_list.append({
                    'no_notis_bas': compound_info.no_notis_bas,
                    'kepada': compound_info.kepada,
                    'company_no': compound_info.company_no,
                    'alamat': compound_info.alamat,
                    'id_mtb': officer.nama,
                    'parlimen': compound_info.parlimen,
                    'lokasi_kompaun': compound_info.lokasi_kompaun,
                    'butir_butir_kesalahan': compound_info.butir_butir_kesalahan,
                    'tarikh': compound_info.tarikh,
                    'waktu': compound_info.waktu,
                    'tempat': compound_info.tempat,
                    'sek47_1a' : compound_info.sek47_1a,
                    'sek47_1c' : compound_info.sek47_1c,
                    'sek47_1d' : compound_info.sek47_1d,
                    'sek47_1e' : compound_info.sek47_1e,
                    'sek47_1g' : compound_info.sek47_1g,
                    'sek47_2a' : compound_info.sek47_2a,
                    'sek47_2b' : compound_info.sek47_2b,
                    'uuk8' : compound_info.uuk8,
                    'uuk9' : compound_info.uuk9,
                    'uuk3' : compound_info.uuk3,
                    'sek46_1b' : compound_info.sek46_1b,
                    'sek46_1c' : compound_info.sek46_1c,
                    'sek46_1d' : compound_info.sek46_1d,
                    'sek46_1e' : compound_info.sek46_1e,
                    'sek46_1f' : compound_info.sek46_1f,
                    'sek46_1g' : compound_info.sek46_1g,
                    'uuk5_a'  : compound_info.uuk5_a,
                    'uuk5_b'  : compound_info.uuk5_b,
                    'uuk5_c' : compound_info.uuk5_c,
                    'uuk33' : compound_info.uuk33,
                    'uuk34' : compound_info.uuk34,
                    'uuk35' : compound_info.uuk35
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
def generateRandomNumber():
    rand_num = randint(10000,999999)
    return rand_num
""" ===============================<< Send Notice starts >>=============================== """
# @token_required
def sendNotice(data):
    # user = get_logged_in_user()
    id_mtb = data.id_mtb
    parlimen = db.session.query(MasterUser).filter_by(nama=id_mtb).first().parlimen
    
    nama_pegawai_merinyu=data.nama_pegawai_merinyu
    lokasi_merinyu=data.lokasi_merinyu
    gambar_lokasi_kerja_photo1=data.gambar_lokasi_kerja_photo1
    gambar_lokasi_kerja_photo2=data.gambar_lokasi_kerja_photo2
    gambar_lokasi_kerja_photo3=data.gambar_lokasi_kerja_photo3
    if gambar_lokasi_kerja_photo1:
        gambar_lokasi_kerja_photo1 = re.sub('[^a-zA-Z0-9.]', '', gambar_lokasi_kerja_photo1)
        sebelum_tarikh_masa = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    else:   
        sebelum_tarikh_masa = None
    if gambar_lokasi_kerja_photo2:
        gambar_lokasi_kerja_photo2 = re.sub('[^a-zA-Z0-9.]', '', gambar_lokasi_kerja_photo2)
        selepas_tarikh_masa = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    else:
        selepas_tarikh_masa = None
    if gambar_lokasi_kerja_photo3:
        gambar_lokasi_kerja_photo3 = re.sub('[^a-zA-Z0-9.]', '', gambar_lokasi_kerja_photo3)
        laporan_tarikh_masa = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    else:
        selepas_tarikh_masa = None
    status_tindakan=data.status_tindakan
    kontraktor_emel=data.kontraktor_emel
    
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type
        role = user.role
        no_siri_np = generateRandomNumber()
        no_siri_np = 'NP'+str(no_siri_np)
        print(no_siri_np)
        for no_siri_np_list in db.session.query(MasterUser).filter(MasterUser.no_kad_pengenalan != None).all():
            if no_siri_np == no_siri_np_list.no_kad_pengenalan:
                no_siri_np = generateRandomNumber()
                no_siri_np = 'NP'+str(no_siri_np)

        
        userInfo= MasterUser(no_kad_pengenalan=no_siri_np,lock_time='9999-12-31 23:59:59',user_type='agenci',role='Agensi',nama_pegawai_merinyu=nama_pegawai_merinyu,
                            lokasi=lokasi_merinyu,parlimen=parlimen,status_tindakan=status_tindakan,active=1)
        # notice_info= Notice(id_mtb=id_mtb,nama_pegawai_merinyu=nama_pegawai_merinyu,lokasi_merinyu=lokasi_merinyu,
        #                     gambar_lokasi_kerja_photo1=gambar_lokasi_kerja_photo1,gambar_lokasi_kerja_photo2=gambar_lokasi_kerja_photo2,
        #                     gambar_lokasi_kerja_photo3=gambar_lokasi_kerja_photo3,status_tindakan=status_tindakan,kontraktor_emel=kontraktor_emel, 
        #                     no_siri_np=no_siri_np, inserted_by=id_card_no,inserted_date=today,active=1)
        agensiFeedbackInfo= AgenciFeedback(no_siri_notis_pemberitahuan=no_siri_np,organisasi='',nama_pegawai_merinyu=nama_pegawai_merinyu,maklum_balas='',
                            gambar_sebelum=gambar_lokasi_kerja_photo1,sebelum_tarikh_masa=sebelum_tarikh_masa,gambar_selepas=gambar_lokasi_kerja_photo2,selepas_tarikh_masa=selepas_tarikh_masa,
                            gambar_laporan=gambar_lokasi_kerja_photo3,katatan=status_tindakan, laporan_tarikh_masa=laporan_tarikh_masa,
                            inserted_by=id_card_no,inserted_date=today,active=1)
        # db.session.add(notice_info)
        db.session.add(userInfo)
        db.session.commit()
        db.session.add(agensiFeedbackInfo)
        db.session.commit()
        statement = "Maklumat notis baru berjaya ditambahkan."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        
    except:
        logger.exception("Notice information could not be saved")
        return "Notice information could not be saved"
    
    TO_EMAIL = kontraktor_emel
    message = MIMEMultipart()
    message['From'] = FROM_EMAIL
    message['To'] = TO_EMAIL
    message['Subject'] = 'Notis Pemberitahuan'
    MAIL_CONTENT = f'''
    Salam Sejahtera,
    
    Nama Pegawai : {nama_pegawai_merinyu}
    Lokasi Merinyu: {lokasi_merinyu}
    Status Tindakan: {status_tindakan}
    Notis Pemberitahuan: {no_siri_np}
    
    Jabatan Kesihatan dan Alam Sekitar
    '''
    if send_email(FROM_EMAIL, TO_EMAIL, 'Notis Pemberitahuan', MAIL_CONTENT):
        logger.info("Notice Sent")
        response_object = {
            "status": "success",
            "message": "notice_sent"
        }
        return response_object
    logger.exception("Notice could not be sent")
    response_object = {
        "status": "fail",
        "message": "notice_not_sent"
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
        logger.info("Graf prestasi bulanan fetched")
        return jsonify(grafPrestasiBulanan_list)
    except:
        logger.exception("graf prestasi bulanan not fetched")
        response_object = {
            "status" : "fail",
            "message" : "graf prestasi bulanan not fetched"
        }
        return response_object, 400
""" ===============================<<Fetch Graf Prestasi Bulanan Ends>>=============================== """
""" ===============================<< getBorangZon starts >>=============================== """
@token_required
def getBorangZon():
    user = get_logged_in_user()
    no_kad_pengenalan = user.no_kad_pengenalan
    try:
        zon_list = []
        if user.role == 'Superadmin':
            zon_list=['Utara','Tengah','Selatan']
        else:
            parlimenInfo = db.session.query(MasterUser).filter_by(no_kad_pengenalan = no_kad_pengenalan).all()
            for _ in parlimenInfo:
                zon_list.append(_.zon)
        logger.info('Borang Parlimen fetched')
        return jsonify(zon_list)
    except:
        logger.exception("Borang parlimen could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Borang Parlimen could not be fetched',
        }
        return response_object, 400
        
""" ===============================<< getBorangZon ends >>=============================== """
""" ===============================<< getBorangParlimen starts >>=============================== """
@token_required
def getBorangParlimen():
    user = get_logged_in_user()
    no_kad_pengenalan = user.no_kad_pengenalan
    try:
        parlimen_list = []
        if user.role == 'Superadmin': parlimen_list=['Segambut','Batu','Kepong','Wangsa Maju','Bukit Bintang','Setiawangsa','Titiwangsa','Seputeh','Lembah Pantai','Cheras','Bandar Tun Razak']
        elif user.role == 'MerinyuMTK':
            if user.zon == 'Utara': parlimen_list=['Segambut','Batu','Kepong', 'Wangsa Maju']
            if user.zon == 'Tengah': parlimen_list=['Bukit Bintang','Setiawangsa','Titiwangsa']
            if user.zon == 'Selatan': parlimen_list=['Seputeh','Lembah Pantai','Cheras', 'Bandar Tun Razak']
        else:
            parlimenInfo = db.session.query(MasterUser).filter_by(no_kad_pengenalan = no_kad_pengenalan).all()
            for _ in parlimenInfo:
                parlimen_list.append(_.parlimen)
        logger.info('Borang Parlimen fetched')
        return jsonify(parlimen_list)
    except:
        logger.exception("Borang parlimen could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Borang Parlimen could not be fetched',
        }
        return response_object, 400
        
""" ===============================<< getBorangParlimen ends >>=============================== """
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
        ukuran_panjang_jejantas_sapuan_6m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jejantas = "6M").count() 
        ukuran_panjang_jejantas_sapuan_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jejantas = "7M").count() 
        ukuran_panjang_jejantas_sapuan_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jejantas = "100 / SKS").count() 
        ukuran_panjang_jejantas_sapuan_sks += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jejantas = "279 / SKS").count() 
        ukuran_panjang_jejantas_sapuan_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_jejantas = "557.4 / IRJ").count() 
        ukuran_panjang_sapuan_TPKK_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_TPKK = "7M").count() 
        ukuran_panjang_sapuan_TPKK_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_TPKK = "298 / SKS").count() 
        ukuran_panjang_sapuan_TPKK_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_TPKK = "IRJ").count()
        ukuran_panjang_sapuan_kewlapangparkir_6m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "3114.50 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "3213 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "1488 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "2439.68 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_6m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "8381.66 / 6M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "2306 / 7M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_7m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "1335.46 / 7M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_7m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "1275.353 / 7M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_7m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "227 / 7M").count() 
        ukuran_panjang_sapuan_kewlapangparkir_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "8440.99 / SKS").count() 
        ukuran_panjang_sapuan_kewlapangparkir_sks += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "1223.43 / SKS").count() 
        ukuran_panjang_sapuan_kewlapangparkir_1s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_sapuan_kaw_lapang_parkir = "950.86 / 1S").count()
        ukuran_panjang_jejantas_cucian_1s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_jejantas = "281.31 / 1S").count() 
        ukuran_panjang_jejantas_cucian_2s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_jejantas = "2S").count() 
        ukuran_panjang_jejantas_cucian_6m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_jejantas = "6M").count() 
        ukuran_panjang_cucian_siarkaki_7m = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_siarkaki = "448 / 7M").count() 
        ukuran_panjang_cucian_siarkaki_7m += OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_siarkaki = "413 / 7M").count() 
        ukuran_panjang_cucian_siarkaki_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_siarkaki = "4151 / IRJ").count() 
        ukuran_panjang_cucilongkan_1s = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_longkang = "1S").count() 
        ukuran_panjang_cucilongkan_irj = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_longkang = "IRJ").count() 
        ukuran_panjang_cucilongkan_sks = OmpBaru.query.filter_by(parlimen=parlimen,ukuran_panjang_cucian_longkang = "SKS").count()
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
    logger.info("Graf Jumlah Kutipan Data Fetched")
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
            "Bukit_Bintang" :  bukit_bintang_count_cucian,
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
    logger.info("Graf Jumlah Kutipan Data Fetched")
    return response, 200

""" ===============================<<Fetch Graf Jumlah Pembersihan Awam Ends >>=============================== """
""" ===============================<< Create Omp Baru starts >>=============================== """
@token_required
def createOmpBaru(data):
    parlimen = data.parlimen
    lokasi = data.lokasi
    kordinat = data.kordinat
    jumlah_unit_premis = data.jumlah_unit_premis
    kekerapan_kutipan_sisa_domestik = data.sisa_domestik
    kekerapan_kutipan_sampah_pukal = data.sampah_pukal
    kekerapan_kutipan_sampah_haram = data.sampah_haram
    ukuran_panjang_sapuan_jalan = data.sapuan_jalan
    ukuran_panjang_sapuan_TPKK = data.sapuan_TPKK
    ukuran_panjang_sapuan_kaw_lapang_parkir = data.sapuan_parkir
    ukuran_panjang_sapuan_jejantas = data.sapuan_jejantas
    ukuran_panjang_cucian_jejantas = data.cucian_jejantas
    ukuran_panjang_cucian_siarkaki = data.cucian_siarkaki
    ukuran_panjang_cucian_siarkaki_berbumbung = data.cucian_siarkaki_berbumbung
    ukuran_panjang_cucian_stesenbas_teksi = data.cucian_stesenbas_teksi
    ukuran_panjang_cucian_longkang = data.cucian_longkang
    ukuran_panjang_potongrumput = data.potong_rumput
    ukuran_panjang_sampahkebun = data.sampah_kebun
    catatan = data.catatan
    rujukan_tarikh_serahan = data.rujukan_tarikh_serahan
    tarikh_semakandi_lapangant_keadeansemata_ada = data.tarikh_semakandi_lapangant_keadeansemata_ada
    tarikh_semakandi_lapangant_keadeansemata_tiada = data.tarikh_semakandi_lapangant_keadeansemata_tiada
    surat_serahan = data.surat_serahan
    kadar = data.kadar
    frekuensi = data.frekuensi

    domestic_category = data.domestic_category
    domestic_total = data.domestic_total
    domestic_freq = data.domestic_freq
    domestic_rate = data.domestic_rate
    pukal_category = data.pukal_category
    pukal_total = data.pukal_total
    pukal_freq = data.pukal_freq
    pukal_rate = data.pukal_rate

    sapuan_domestic_unit = data.sapuan_domestic_unit
    sapuan_domestic_rate = data.sapuan_domestic_rate
    sapuan_domestic_freq = data.sapuan_domestic_freq
    sapuan_komersial_unit = data.sapuan_komersial_unit
    sapuan_komersial_rate = data.sapuan_komersial_rate
    sapuan_komersial_freq = data.sapuan_komersial_freq

    cucian_domestic_unit = data.cucian_domestic_unit
    cucian_domestic_rate = data.cucian_domestic_rate
    cucian_domestic_freq = data.cucian_domestic_freq
    cucian_komersial_unit = data.cucian_komersial_unit
    cucian_komersial_rate = data.cucian_komersial_rate
    cucian_komersial_freq = data.cucian_komersial_freq
    cucian_drain_domestic_unit = data.cucian_drain_domestic_unit
    cucian_drain_domestic_rate = data.cucian_drain_domestic_rate
    cucian_drain_domestic_freq = data.cucian_drain_domestic_freq
    cucian_drain_komersial_unit = data.cucian_drain_komersial_unit
    cucian_drain_komersial_rate = data.cucian_drain_komersial_rate
    cucian_drain_komersial_freq = data.cucian_drain_komersial_freq
    cucian_jejantas_dalam_unit = data.cucian_jejantas_dalam_unit
    cucian_jejantas_dalam_rate = data.cucian_jejantas_dalam_rate
    cucian_jejantas_dalam_freq = data.cucian_jejantas_dalam_freq
    cucian_jejantas_atas_unit = data.cucian_jejantas_atas_unit
    cucian_jejantas_atas_rate = data.cucian_jejantas_atas_rate
    cucian_jejantas_atas_freq = data.cucian_jejantas_atas_freq
    cucian_siar_roof_unit = data.cucian_siar_roof_unit
    cucian_siar_roof_rate = data.cucian_siar_roof_rate
    cucian_siar_roof_freq = data.cucian_siar_roof_freq
    cucian_siar_gulam1_unit = data.cucian_siar_gulam1_unit
    cucian_siar_gulam1_rate = data.cucian_siar_gulam1_rate
    cucian_siar_gulam1_freq = data.cucian_siar_gulam1_freq
    cucian_siar_gulam2_unit = data.cucian_siar_gulam2_unit
    cucian_siar_gulam2_rate = data.cucian_siar_gulam2_rate
    cucian_siar_gulam2_freq = data.cucian_siar_gulam2_freq
    cucian_tandas_unit = data.cucian_tandas_unit
    cucian_tandas_rate = data.cucian_tandas_rate
    cucian_tandas_freq = data.cucian_tandas_freq
    cucian_teksi_rate = data.cucian_teksi_rate
    cucian_teksi_freq = data.cucian_teksi_freq
    cucian_teksi_total = data.cucian_teksi_total

    bersih_lapang_unit = data.bersih_lapang_unit
    bersih_lapang_rate = data.bersih_lapang_rate
    bersih_lapang_freq = data.bersih_lapang_freq
    bersih_tpkk_unit = data.bersih_tpkk_unit
    bersih_tpkk_rate = data.bersih_tpkk_rate
    bersih_tpkk_freq = data.bersih_tpkk_freq
    bersih_penjaja_unit = data.bersih_penjaja_unit
    bersih_penjaja_rate = data.bersih_penjaja_rate
    bersih_penjaja_freq = data.bersih_penjaja_freq
    bersih_pasar_unit = data.bersih_pasar_unit
    bersih_pasar_rate = data.bersih_pasar_rate
    bersih_pasar_freq = data.bersih_pasar_freq
    bersih_pasar_mlm_unit = data.bersih_pasar_mlm_unit
    bersih_pasar_mlm_rate = data.bersih_pasar_mlm_rate
    bersih_pasar_mlm_freq = data.bersih_pasar_mlm_freq

    rumput_unit = data.rumput_unit
    rumput_rate = data.rumput_rate
    rumput_freq = data.rumput_freq

    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type
        role = user.role
        new_omp_baru = OmpBaru(parlimen=parlimen, lokasi=lokasi, kordinat=kordinat, jumlah_unit_premis=jumlah_unit_premis, parlimen_subarea='TERKINI', 
                               kekerapan_kutipan_sisa_domestik=kekerapan_kutipan_sisa_domestik,
                               kekerapan_kutipan_sampah_pukal=kekerapan_kutipan_sampah_pukal,
                               kekerapan_kutipan_sampah_haram=kekerapan_kutipan_sampah_haram,
                               ukuran_panjang_sapuan_jalan=ukuran_panjang_sapuan_jalan,
                               ukuran_panjang_sapuan_TPKK=ukuran_panjang_sapuan_TPKK,
                               ukuran_panjang_sapuan_kaw_lapang_parkir=ukuran_panjang_sapuan_kaw_lapang_parkir,
                               ukuran_panjang_sapuan_jejantas=ukuran_panjang_sapuan_jejantas,
                               ukuran_panjang_cucian_jejantas=ukuran_panjang_cucian_jejantas,
                               ukuran_panjang_cucian_siarkaki=ukuran_panjang_cucian_siarkaki,
                               ukuran_panjang_cucian_siarkaki_berbumbung=ukuran_panjang_cucian_siarkaki_berbumbung,
                               ukuran_panjang_cucian_stesenbas_teksi=ukuran_panjang_cucian_stesenbas_teksi,
                               ukuran_panjang_cucian_longkang=ukuran_panjang_cucian_longkang,
                               ukuran_panjang_potongrumput=ukuran_panjang_potongrumput,
                               ukuran_panjang_sampahkebun=ukuran_panjang_sampahkebun,
                               domestic_freq=domestic_freq, domestic_rate=domestic_rate, domestic_total=domestic_total, domestic_category=domestic_category,
                               pukal_total=pukal_total, pukal_freq=pukal_freq, pukal_rate=pukal_rate, pukal_category=pukal_category,

                               sapuan_domestic_unit=sapuan_domestic_unit, sapuan_domestic_rate=sapuan_domestic_rate, sapuan_domestic_freq=sapuan_domestic_freq,
                               sapuan_komersial_unit=sapuan_komersial_unit, sapuan_komersial_rate=sapuan_komersial_rate, sapuan_komersial_freq=sapuan_komersial_freq,

                               cucian_domestic_unit=cucian_domestic_unit, cucian_domestic_rate=cucian_domestic_rate, cucian_domestic_freq=cucian_domestic_freq,
                               cucian_komersial_unit=cucian_komersial_unit, cucian_komersial_rate=cucian_komersial_rate, cucian_komersial_freq=cucian_komersial_freq,
                               cucian_drain_domestic_unit=cucian_drain_domestic_unit, cucian_drain_domestic_rate=cucian_drain_domestic_rate, cucian_drain_domestic_freq=cucian_drain_domestic_freq,
                               cucian_drain_komersial_unit=cucian_drain_komersial_unit, cucian_drain_komersial_rate=cucian_drain_komersial_rate, cucian_drain_komersial_freq=cucian_drain_komersial_freq,
                               cucian_jejantas_dalam_unit=cucian_jejantas_dalam_unit, cucian_jejantas_dalam_rate=cucian_jejantas_dalam_rate, cucian_jejantas_dalam_freq=cucian_jejantas_dalam_freq,
                               cucian_jejantas_atas_unit=cucian_jejantas_atas_unit, cucian_jejantas_atas_rate=cucian_jejantas_atas_rate, cucian_jejantas_atas_freq=cucian_jejantas_atas_freq,
                               cucian_siar_roof_unit=cucian_siar_roof_unit, cucian_siar_roof_rate=cucian_siar_roof_rate, cucian_siar_roof_freq=cucian_siar_roof_freq,
                               cucian_siar_gulam1_unit=cucian_siar_gulam1_unit, cucian_siar_gulam1_rate=cucian_siar_gulam1_rate, cucian_siar_gulam1_freq=cucian_siar_gulam1_freq,
                               cucian_siar_gulam2_unit=cucian_siar_gulam2_unit, cucian_siar_gulam2_rate=cucian_siar_gulam2_rate, cucian_siar_gulam2_freq=cucian_siar_gulam2_freq,
                               cucian_tandas_unit=cucian_tandas_unit, cucian_tandas_rate=cucian_tandas_rate, cucian_tandas_freq=cucian_tandas_freq,
                               cucian_teksi_rate=cucian_teksi_rate, cucian_teksi_freq=cucian_teksi_freq,cucian_teksi_total=cucian_teksi_total,
                               bersih_lapang_unit=bersih_lapang_unit, bersih_lapang_rate=bersih_lapang_rate, bersih_lapang_freq=bersih_lapang_freq,
                               bersih_tpkk_unit=bersih_tpkk_unit, bersih_tpkk_rate=bersih_tpkk_rate, bersih_tpkk_freq=bersih_tpkk_freq,
                               bersih_penjaja_unit=bersih_penjaja_unit, bersih_penjaja_rate=bersih_penjaja_rate, bersih_penjaja_freq=bersih_penjaja_freq,
                               bersih_pasar_unit=bersih_pasar_unit, bersih_pasar_rate=bersih_pasar_rate, bersih_pasar_freq=bersih_pasar_freq,
                               bersih_pasar_mlm_unit=bersih_pasar_mlm_unit, bersih_pasar_mlm_rate=bersih_pasar_mlm_rate, bersih_pasar_mlm_freq=bersih_pasar_mlm_freq,
                               rumput_unit=rumput_unit, rumput_rate=rumput_rate, rumput_freq=rumput_freq,

                               catatan=catatan,
                               rujuken_tarikh_serahan=rujukan_tarikh_serahan,
                               tarikh_semakandi_lapangant_keadeansemata_ada=tarikh_semakandi_lapangant_keadeansemata_ada,
                               tarikh_semakandi_lapangant_keadeansemata_tiada=tarikh_semakandi_lapangant_keadeansemata_tiada,
                               surat_serahan=surat_serahan, kadar=kadar, frekuensi=frekuensi,
                               inserted_by=id_card_no, inserted_date=now, active=1)
        db.session.add(new_omp_baru)
        db.session.commit()
        
        statement = "Omp Baru berjaya dibuat"
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        logger.info("OMP Baru created.")
        response_object = {
            "status": "success",
            "message": "omp_baru_added"
        }
        return response_object, 200
    except:
        logger.exception("OMP Baru is not created.")
        response_object = {
            'status':'fail',
            'message':'omp_baru_not_added'
        }
        return response_object, 400  
""" ===============================<< Create omp_baru ends >>=============================== """
""" ===============================<< getIdPegawai Starts >>=============================== """
@token_required
def getIdPegawai():
    try:
        user = get_logged_in_user()
        officer_name = user.no_kad_pengenalan
        if user.role == 'Superadmin':
            id_pegawai = OfficersList.query.with_entities(OfficersList.officer_name).distinct().all()
            id_pegawai_list = list(itertools.chain(*id_pegawai))
            for _ in range (0,len(id_pegawai_list)):
                if id_pegawai_list[_] == 'SuperAdmin':
                    id_pegawai_list.pop(_)
            logger.info("ID Pegawai List fetched")
            return id_pegawai_list
        if user.role == 'MerinyuMTK':
            id_pegawai = OfficersList.query.with_entities(OfficersList.officer_name).filter_by(id_mtk=officer_name).distinct().all()
            id_pegawai_list = list(itertools.chain(*id_pegawai))
            logger.info("ID Pegawai List fetched")
            return id_pegawai_list
        if user.role == 'MerinyuMTB':
            id_pegawai = OfficersList.query.with_entities(OfficersList.officer_name).filter_by(id_mtb=officer_name).distinct().all()
            id_pegawai_list = list(itertools.chain(*id_pegawai))
            for _ in range (0,len(id_pegawai_list)):
                if id_pegawai_list[_] == 'SuperAdmin':
                    id_pegawai_list.pop(_)
            logger.info("ID Pegawai List fetched")
            return id_pegawai_list
    except:
        logger.exception("id_pegawai List could not be fetched")
        response_object = {
            "status": "fail",
            "message": "id_pegawai List could not be fetched"
        }
        return response_object, 400
    
""" ===============================<< getIdPegawai Ends >>=============================== """
""" ===============================<< getLokasi Starts >>=============================== """
def getLokasi(parlimen):
    try:
        lokasi = Coordinates.query.filter_by(parlimen=parlimen, active=1).with_entities(Coordinates.lokasi).all()         
        lokasi_list = list(itertools.chain(*lokasi)) 
        logger.info("Lokasi fetched")
        return lokasi_list
        
    except:
        response_object = {
            "status" : "fail",
            "message" : "lokasi not fetched"
        }
        logger.exception("lokasi not fetched")
        return response_object,400 
""" ===============================<< getLokasi Ends >>=============================== """
""" ===============================<< getLapisanFitur Starts >>=============================== """
# @token_required
def getLapisanFitur():
    try:
        lapisan_fitur = PerkhidmatanPusatTong.query.with_entities(PerkhidmatanPusatTong.lapisan_fitur).all()         
        lapisan_fitur_list = list(set(itertools.chain(*lapisan_fitur))) 
        logger.info("lapisan fitur fetched")    
        return lapisan_fitur_list
    
    except:
        response_object = {
            "status" : "fail",
            "message" : "lapisan fitur could not be fetched"
        }
        logger.exception("lapisan fitur could not be fetched")
        return response_object,400    

""" ===============================<< getLapisanFitur Ends >>=============================== """
""" ===============================<< getKategori Starts >>=============================== """

def getKategori(data):
    lapisan_fitur = data.lapisan_fitur
    try:
        kategori = PerkhidmatanPusatTong.query.filter_by(lapisan_fitur=lapisan_fitur).with_entities(PerkhidmatanPusatTong.kategori).all()         
        kategori_list = list(set(itertools.chain(*kategori)))
        kategori_list.sort()

        for kategori in kategori_list:
            if kategori == "":
                kategori_list.remove(kategori)
            if kategori == " ":
                kategori_list.remove(kategori)
            if kategori != "" and kategori != " " and kategori[len(kategori)-1] == " ":
                kategori_list.remove(kategori)
            
        result = []

        if lapisan_fitur == "PUSAT_TONG":
            KATEGORI = ["PERUMAHAN","KOMERSIAL","PUSAT TONG"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "JARINGAN_JALAN_RAYA":
            KATEGORI = ["KOMERSIAL (JALAN UTAMA)","PERUMAHAN","PROTOKOL"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "JARINGAN_LONGKANG":
            KATEGORI = ["LONGKANG MONSUN","LONGKANG TERTUTUP","LONGKANG TERBUKA"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "FASILITI_DBKL":
            KATEGORI = ["MEDAN SELERA","PUSAT KOMUNITI","PUSAT PENJAJA"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "FASILITI_DBKL_TANDAS":
            KATEGORI = ["KOMPLEKS SUKAN","BAZARIA","MEDAN SELERA"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "JEJANTAS":
            KATEGORI = ["BERBUMBUNG","TAK BERBUMBUNG","TIDAK BERBUMBUNG"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "KAWASAN_LAPANG":
            KATEGORI = ["BERUMPUT","LANSKAP","KONKRIT"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "SIAR_KAKI":
            KATEGORI = ["TIDAK BERBUMBUNG","BERBUMBUNG"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "HENTIAN_BAS":
            KATEGORI = ["HENTIAN BAS","BERBUMBUNG","HUB STATION"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "PREMIS":
            KATEGORI = ["KOMERSIAL (JALAN UTAMA)","PERUMAHAN"]
            for i in KATEGORI:
                if i in kategori_list:
                    underscored_str=i.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "TAMAN_PERMAINAN_KANAK_KANAK":
            KATEGORI = ["BERUMPUT","BERUMPUT, TIDAK BERUMPUT","TIDAK BERUMPUT"]
            for i in KATEGORI:
                if i in kategori_list:
                    comma_str = i.replace(",","")
                    underscored_str = comma_str.replace(" ", "_")
                    new_str_f = underscored_str.replace("(", "")
                    new_str = new_str_f.replace(")", "")
                    result.append(new_str)

        if lapisan_fitur == "HENTIAN_TEKSI":
            
            if not kategori_list:
                logger.info("No kategori found.")
                return jsonify(result)

        if lapisan_fitur == "KAWASAN_BERUMPUT_DAN_KAWASAN_HIJAU":
            
            if not kategori_list:
                logger.info("No kategori found.")
                return jsonify(result)

        if lapisan_fitur == "PARKING_TEMPAT_AWAM":
            
            if not kategori_list:
                logger.info("No kategori found.")
                return jsonify(result)

        if lapisan_fitur == "TANDAS_AWAM":
            
            if not kategori_list:
                logger.info("No kategori found.")
                return jsonify(result)

        logger.info("kategori list fetched successfully")        
        return jsonify(result)
    except:
        response_object = {
            "status" : "fail",
            "message" : "kategori not fetched"
        }
        logger.exception("kategori not fetched")
        return response_object,400
    
""" ===============================<< getKategori Ends >>=============================== """
""" ===============================<<Fetch graf PerkhidmatanPusatTong Starts >>=============================== """

def grafPerkhidmatanPusatTong(data):
    lapisan_fitur = data.lapisan_fitur
    try:
        result = []
        parlimen_list = ["LEMBAH PANTAI (P121)","SEGAMBUT","BATU","KEPONG","SEPUTEH","BUKIT BINTANG","BANDAR TUN RAZAK","WANGSA MAJU","CHERAS","TITIWANGSA","SETIAWANGSA"]
        if lapisan_fitur == "PUSAT_TONG":
#1            '''kategori = FASILITI,PERUMAHAN,TONG SAMPAH,KOMERSIAL,PUSAT TONG,RUMAH SAMPAH'''
            for i in parlimen_list:
                PERUMAHAN_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PERUMAHAN", servis_per="YA").count()
                PERUMAHAN_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PERUMAHAN", servis_per="TIDAK").count()
                KOMERSIAL_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KOMERSIAL", servis_per="YA").count()
                KOMERSIAL_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KOMERSIAL", servis_per="TIDAK").count()
                PUSAT_TONG_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PUSAT TONG", servis_per="YA").count()
                PUSAT_TONG_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PUSAT TONG", servis_per="TIDAK").count()
    
                result.append({ 
                    i : {
                            "PERUMAHAN_YA" : PERUMAHAN_YA,
                            "PERUMAHAN_TIDAK" : PERUMAHAN_TIDAK,
                            "KOMERSIAL_YA" : KOMERSIAL_YA,
                            "KOMERSIAL_TIDAK" : KOMERSIAL_TIDAK,
                            "PUSAT_TONG_YA" : PUSAT_TONG_YA,
                            "PUSAT_TONG_TIDAK" : PUSAT_TONG_TIDAK,
                    }
                })
        if lapisan_fitur == "JARINGAN_JALAN_RAYA":
#2            '''kategori = KOMERSIAL (JALAN UTAMA), PERUMAHAN'''
            for i in parlimen_list:
                KOMERSIAL_JALAN_UTAMA_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KOMERSIAL (JALAN UTAMA)", servis_per="YA").count()
                KOMERSIAL_JALAN_UTAMA_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KOMERSIAL (JALAN UTAMA)", servis_per="TIDAK").count()
                PERUMAHAN_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PERUMAHAN", servis_per="YA").count()
                PERUMAHAN_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PERUMAHAN", servis_per="TIDAK").count()
                PROTOKOL_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PROTOKOL", servis_per="YA").count()
                PROTOKOL_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PROTOKOL", servis_per="TIDAK").count()

                result.append({
                    i : {
                        "KOMERSIAL_JALAN_UTAMA_YA" : KOMERSIAL_JALAN_UTAMA_YA,
                        "KOMERSIAL_JALAN_UTAMA_TIDAK" : KOMERSIAL_JALAN_UTAMA_TIDAK,
                        "PERUMAHAN_YA" : PERUMAHAN_YA,
                        "PERUMAHAN_TIDAK" : PERUMAHAN_TIDAK,
                        "PROTOKOL_YA" : PROTOKOL_YA,
                        "PROTOKOL_TIDAK" : PROTOKOL_TIDAK
                    }
                })

        if lapisan_fitur == "JARINGAN_LONGKANG":
#3            '''kategori = LONGKANG TERBUKA, LONGKANG TERTUTUP, LONGKANG MONSUN'''
            for i in parlimen_list:
                LONGKANG_MONSUN_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="LONGKANG MONSUN", servis_per="YA").count()
                LONGKANG_MONSUN_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="LONGKANG MONSUN", servis_per="TIDAK").count()
                LONGKANG_TERTUTUP_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="LONGKANG TERTUTUP", servis_per="YA").count()
                LONGKANG_TERTUTUP_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="LONGKANG TERTUTUP", servis_per="TIDAK").count()
                LONGKANG_TERBUKA_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="LONGKANG TERBUKA", servis_per="YA").count()
                LONGKANG_TERBUKA_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="LONGKANG TERBUKA", servis_per="TIDAK").count()
        
                result.append({
                    i : {
                        "LONGKANG_MONSUN_YA" : LONGKANG_MONSUN_YA,
                        "LONGKANG_MONSUN_TIDAK" : LONGKANG_MONSUN_TIDAK,
                        "LONGKANG_TERTUTUP_YA" : LONGKANG_TERTUTUP_YA,
                        "LONGKANG_TERTUTUP_TIDAK" : LONGKANG_TERTUTUP_TIDAK,
                        "LONGKANG_TERBUKA_YA" : LONGKANG_TERBUKA_YA,
                        "LONGKANG_TERBUKA_TIDAK" : LONGKANG_TERBUKA_TIDAK
                    }
                })

        if lapisan_fitur == "FASILITI_DBKL":
#4            '''kategori = PUSAT PENJAJA, MEDAN SELERA, KOMPLEKS SUKAN BANGSAR, PUSAT KOMUNITI, PASAR AWAM (BERSTRUKTUR), BAZARIA, PERPUSTAKAAN AWAM,KOLAM RENANG'''
            for i in parlimen_list:
                MEDAN_SELERA_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="MEDAN SELERA", servis_per="YA").count()
                MEDAN_SELERA_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="MEDAN SELERA", servis_per="TIDAK").count()
                PUSAT_KOMUNITI_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PUSAT KOMUNITI", servis_per="YA").count()
                PUSAT_KOMUNITI_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PUSAT KOMUNITI", servis_per="TIDAK").count()
                PUSAT_PENJAJA_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PUSAT PENJAJA", servis_per="YA").count()
                PUSAT_PENJAJA_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PUSAT PENJAJA", servis_per="TIDAK").count()
        
                result.append({
                    i : {
                        "MEDAN_SELERA_YA" : MEDAN_SELERA_YA,
                        "MEDAN_SELERA_TIDAK" : MEDAN_SELERA_TIDAK,
                        "PUSAT_KOMUNITI_YA" : PUSAT_KOMUNITI_YA,
                        "PUSAT_KOMUNITI_TIDAK" : PUSAT_KOMUNITI_TIDAK,
                        "PUSAT_PENJAJA_YA" : PUSAT_PENJAJA_YA,
                        "PUSAT_PENJAJA_TIDAK" : PUSAT_PENJAJA_TIDAK
                    }
                })

        if lapisan_fitur == "FASILITI_DBKL_TANDAS":
#5            '''kategori = no catagorie found'''
            for i in parlimen_list:
                KOMPLEKS_SUKAN_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KOMPLEKS SUKAN", servis_per="YA").count()
                KOMPLEKS_SUKAN_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KOMPLEKS SUKAN", servis_per="TIDAK").count()
                BAZARIA_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BAZARIA", servis_per="YA").count()
                BAZARIA_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BAZARIA", servis_per="TIDAK").count()
                MEDAN_SELERA_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="MEDAN SELERA", servis_per="YA").count()
                MEDAN_SELERA_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="MEDAN SELERA", servis_per="TIDAK").count()
        
                result.append({
                    i : {
                        "KOMPLEKS_SUKAN_YA" : KOMPLEKS_SUKAN_YA,
                        "KOMPLEKS_SUKAN_TIDAK" : KOMPLEKS_SUKAN_TIDAK,
                        "BAZARIA_YA" : BAZARIA_YA,
                        "BAZARIA_TIDAK" : BAZARIA_TIDAK,
                        "MEDAN_SELERA_YA" : MEDAN_SELERA_YA,
                        "MEDAN_SELERA_TIDAK" : MEDAN_SELERA_TIDAK
                    }
                })


        if lapisan_fitur == "JEJANTAS":
#6            '''kategori = BERBUMBUNG'''
            for i in parlimen_list:
                BERBUMBUNG_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERBUMBUNG", servis_per="YA").count()
                BERBUMBUNG_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERBUMBUNG", servis_per="TIDAK").count()
                TAK_BERBUMBUNG_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="TAK BERBUMBUNG", servis_per="YA").count()
                TAK_BERBUMBUNG_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="TAK BERBUMBUNG", servis_per="TIDAK").count()
                TIDAK_BERBUMBUNG_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="TIDAK BERBUMBUNG", servis_per="YA").count()
                TIDAK_BERBUMBUNG_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="TIDAK BERBUMBUNG", servis_per="TIDAK").count()
                
                result.append({
                    i : {
                        "BERBUMBUNG_YA" : BERBUMBUNG_YA,
                        "BERBUMBUNG_TIDAK" : BERBUMBUNG_TIDAK,
                        "TAK_BERBUMBUNG_YA" : TAK_BERBUMBUNG_YA,
                        "TAK_BERBUMBUNG_TIDAK" : TAK_BERBUMBUNG_TIDAK,
                        "TIDAK_BERBUMBUNG_YA" : TIDAK_BERBUMBUNG_YA,
                        "TIDAK_BERBUMBUNG_TIDAK" : TIDAK_BERBUMBUNG_TIDAK
                    }
                })

        if lapisan_fitur == "KAWASAN_LAPANG":
#7            '''kategori = LANDSKAP, LANSKAP, KONKRIT, KAWASAN, PARKING, BERUMPUT'''
            for i in parlimen_list:
                BERUMPUT_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERUMPUT", servis_per="YA").count()
                BERUMPUT_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERUMPUT", servis_per="TIDAK").count()
                LANSKAP_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="LANSKAP", servis_per="YA").count()
                LANSKAP_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="LANSKAP", servis_per="TIDAK").count()
                KONKRIT_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KONKRIT", servis_per="YA").count()
                KONKRIT_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KONKRIT", servis_per="TIDAK").count()
            
                result.append({
                    i : {
                        "BERUMPUT_YA" : BERUMPUT_YA,
                        "BERUMPUT_TIDAK" : BERUMPUT_TIDAK,
                        "LANSKAP_YA" : LANSKAP_YA,
                        "LANSKAP_TIDAK" : LANSKAP_TIDAK,
                        "KONKRIT_YA" : KONKRIT_YA,
                        "KONKRIT_TIDAK" : KONKRIT_TIDAK,
                    }
                })

        if lapisan_fitur == "SIAR_KAKI":
#8            '''kategori = TIDAK BERBUMBUNG, BERBUMBUNG'''
            for i in parlimen_list:
                TIDAK_BERBUMBUNG_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="TIDAK BERBUMBUNG", servis_per="YA").count()
                TIDAK_BERBUMBUNG_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="TIDAK BERBUMBUNG", servis_per="TIDAK").count()
                BERBUMBUNG_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERBUMBUNG", servis_per="YA").count()
                BERBUMBUNG_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERBUMBUNG", servis_per="TIDAK").count()
                
                result.append({
                    i : {
                        "TIDAK_BERBUMBUNG_YA" : TIDAK_BERBUMBUNG_YA,
                        "TIDAK_BERBUMBUNG_TIDAK" : TIDAK_BERBUMBUNG_TIDAK,
                        "BERBUMBUNG_YA" : BERBUMBUNG_YA,
                        "BERBUMBUNG_TIDAK" : BERBUMBUNG_TIDAK,
                    }
                })

        if lapisan_fitur == "HENTIAN_BAS":
#9            '''kategori = HENTIAN BAS'''
            for i in parlimen_list:
                HENTIAN_BAS_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="HENTIAN BAS", servis_per="YA").count()
                HENTIAN_BAS_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="HENTIAN BAS", servis_per="TIDAK").count()
                BERBUMBUNG_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERBUMBUNG", servis_per="YA").count()
                BERBUMBUNG_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERBUMBUNG", servis_per="TIDAK").count()
                HUB_STATION_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="HUB STATION", servis_per="YA").count()
                HUB_STATION_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="HUB STATION", servis_per="TIDAK").count()
            
                result.append({
                    i : {
                        "HENTIAN_BAS_YA" : HENTIAN_BAS_YA,
                        "HENTIAN_BAS_TIDAK" : HENTIAN_BAS_TIDAK,
                        "BERBUMBUNG_YA" : BERBUMBUNG_YA,
                        "BERBUMBUNG_TIDAK" : BERBUMBUNG_TIDAK,
                        "HUB_STATION_YA" : HUB_STATION_YA,
                        "HUB_STATION_TIDAK" : HUB_STATION_TIDAK
                    }
                })

        if lapisan_fitur == "PREMIS":
#10            '''kategori = KOMERSIAL (JALAN UTAMA), PERUMAHAN'''
            for i in parlimen_list:
                KOMERSIAL_JALAN_UTAMA_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KOMERSIAL (JALAN UTAMA)", servis_per="YA").count()
                KOMERSIAL_JALAN_UTAMA_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="KOMERSIAL (JALAN UTAMA)", servis_per="TIDAK").count()
                PERUMAHAN_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PERUMAHAN", servis_per="YA").count()
                PERUMAHAN_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="PERUMAHAN", servis_per="TIDAK").count()
            
                result.append({
                    i : {
                        "KOMERSIAL_JALAN_UTAMA_YA" : KOMERSIAL_JALAN_UTAMA_YA,
                        "KOMERSIAL_JALAN_UTAMA_TIDAK" : KOMERSIAL_JALAN_UTAMA_TIDAK,
                        "PERUMAHAN_YA" : PERUMAHAN_YA,
                        "PERUMAHAN_TIDAK" : PERUMAHAN_TIDAK,
                    }
                })

        if lapisan_fitur == "TAMAN_PERMAINAN_KANAK_KANAK":
#11            '''kategori = BERUMPUT, TIDAK BERUMPUT, LANSKAP, [BERUMPUT, TIDAK BERUMPUT]'''
            for i in parlimen_list:
                BERUMPUT_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERUMPUT", servis_per="YA").count()
                BERUMPUT_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERUMPUT", servis_per="TIDAK").count()
                BERUMPUT_TIDAK_BERUMPUT_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERUMPUT, TIDAK BERUMPUT", servis_per="YA").count()
                BERUMPUT_TIDAK_BERUMPUT_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="BERUMPUT, TIDAK BERUMPUT", servis_per="TIDAK").count()
                TIDAK_BERUMPUT_YA = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="TIDAK BERUMPUT", servis_per="YA").count()
                TIDAK_BERUMPUT_TIDAK = PerkhidmatanPusatTong.query.filter_by(parlimen=i,lapisan_fitur=lapisan_fitur, kategori="TIDAK BERUMPUT", servis_per="TIDAK").count()
            
                result.append({
                    i : {
                        "BERUMPUT_YA" : BERUMPUT_YA,
                        "BERUMPUT_TIDAK" : BERUMPUT_TIDAK,
                        "BERUMPUT_TIDAK_BERUMPUT_YA" : BERUMPUT_TIDAK_BERUMPUT_YA,
                        "BERUMPUT_TIDAK_BERUMPUT_TIDAK" : BERUMPUT_TIDAK_BERUMPUT_TIDAK,
                        "TIDAK_BERUMPUT_YA" : TIDAK_BERUMPUT_YA,
                        "TIDAK_BERUMPUT_TIDAK" : TIDAK_BERUMPUT_TIDAK,
                    }
                })

        if lapisan_fitur == "HENTIAN_TEKSI":
#12            '''kategori = No kategori found'''
            kategori = db.session.query(PerkhidmatanPusatTong).filter(PerkhidmatanPusatTong.lapisan_fitur==lapisan_fitur,PerkhidmatanPusatTong.kategori != " ").all()
            if not kategori:
                response_object = {
                    "status" : "fail",
                    "message" : "No kategori found for HENTIAN TEKSI"
                }
                logger.info("No kategori found for HENTIAN TEKSI")
                return response_object,400  

        if lapisan_fitur == "KAWASAN_BERUMPUT_DAN_KAWASAN_HIJAU":
#13            '''kategori = No kategori found'''
            kategori = db.session.query(PerkhidmatanPusatTong).filter(PerkhidmatanPusatTong.lapisan_fitur==lapisan_fitur,PerkhidmatanPusatTong.kategori != " ").all()
            if not kategori:
                response_object = {
                    "status" : "fail",
                    "message" : "No kategori found for KAWASAN BERUMPUT DAN KAWASAN HIJAU"
                }
                logger.info("No kategori found for KAWASAN BERUMPUT DAN KAWASAN HIJAU")
                return response_object,400

        if lapisan_fitur == "PARKING_TEMPAT_AWAM":
#14            '''kategori = No kategori found'''
            kategori = db.session.query(PerkhidmatanPusatTong).filter(PerkhidmatanPusatTong.lapisan_fitur==lapisan_fitur,PerkhidmatanPusatTong.kategori != " ").all()
            if not kategori:
                response_object = {
                    "status" : "fail",
                    "message" : "No kategori found for PARKING TEMPAT AWAM"
                }
                logger.info("No kategori found for PARKING TEMPAT AWAM")
                return response_object,400


        if lapisan_fitur == "TANDAS_AWAM":
#15            '''kategori = No kategori found'''
            kategori = db.session.query(PerkhidmatanPusatTong).filter(PerkhidmatanPusatTong.lapisan_fitur==lapisan_fitur,PerkhidmatanPusatTong.kategori != " ").all()
            if not kategori:
                response_object = {
                    "status" : "fail",
                    "message" : "No kategori found for TANDAS AWAM"
                }
                logger.info("No kategori found for TANDAS AWAM")
                return response_object,400  

        logger.info("ya,tidak count for each parlimen fetched")
        return jsonify(result)   
    except:
        response_object = {
            "status" : "fail",
            "message" : "ya,tidak count for each parlimen not fetched"
        }
        logger.exception("ya,tidak count for each parlimen not fetched")
        return response_object,400
    
""" ===============================<< Fetch graf PerkhidmatanPusatTong ends >>=============================== """        
""" ===============================<<Fetch Google Analytics Report starts >>=============================== """ 

def getGoogleAnalyticsReport():
    try:
        url="/public"
        daysago=str(datetime.now() + timedelta(days=-6))

        credentials = ServiceAccountCredentials.from_json_keyfile_name('app/main/util/client_secrets_new.json', ['https://www.googleapis.com/auth/analytics.readonly'])

        #Create a service object
        http = credentials.authorize(httplib2.Http())
        service = build('analytics', 'v4', http=http, discoveryServiceUrl=('https://analyticsreporting.googleapis.com/$discovery/rest'))
        response = service.reports().batchGet(
            body={
                "reportRequests": [
                {
                    "viewId": "243416109", 
                    "samplingLevel": "DEFAULT",
                    "filtersExpression": "ga:pagePath==" +url, 
                    "dateRanges": [
                    {
                        "startDate": daysago[0:10],
                        "endDate": "today"
                    }
                    ],
                    "metrics": [
                    {
                        "expression": "ga:pageviews",
                        "alias": ""
                    }
                    ],
                    "dimensions": [
                    {'name': 'ga:date'}
                    ]
                }
                ]
            }
        ).execute()
        
        #create two empty lists that will hold our dimentions and sessions data
        dim = []
        val = []
        date = []
        
        #Extract Data
        for report in response.get('reports', []):
        
            columnHeader = report.get('columnHeader', {})
            dimensionHeaders = columnHeader.get('dimensions', [])
            metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
            rows = report.get('data', {}).get('rows', [])
        
            for row in rows:
        
                dimensions = row.get('dimensions', [])
                dateRangeValues = row.get('metrics', [])
        
                for header, dimension in zip(dimensionHeaders, dimensions):
                    dim.append(dimension)
        
                for i, values in enumerate(dateRangeValues):
                    for metricHeader, value in zip(metricHeaders, values.get('values')):
                        val.append(int(value))
        
        #Sort Data
        # val.reverse()
        # dim.reverse()
        
        df = pd.DataFrame() 
        df["Pageviews"]=val
        for row in dim:
            datetimeobject = datetime.strptime(row,'%Y%m%d')
            date.append(datetimeobject.strftime("%d/%m"))
        df["date"]=date
        df=df[["date","Pageviews"]]

        # df_list = df.values.tolist()
        # df_list = list(df.values.flatten())
        df_list = json.loads(df.to_json(orient='records'))
        for i in range(len(df_list)):
            print(df_list[i])
            print(datetime.today().strftime("%d/%m"))
            if datetime.today().strftime("%d/%m") == df_list[i]['date']:
                df_list[i]['date'] = "Today"
            
        logger.info("Google Analytics Report fetched successfully.")
        return df_list
    except:
        logger.exception("Google Analytics Report could not be fetched.")
        response_object = {
            "status": "fail",
            "message": "Google Analytics Report could not be fetched."
        }
        return response_object, 400
    
""" ===============================<< Fetch Google Analytics Report ends >>=============================== """ 
""" ===============================<< dailyViewReport starts >>=============================== """ 

def dailyViewReport():
    try:
        url="/public"
        daysago=str(datetime.now() + timedelta(days=-6))

        credentials = ServiceAccountCredentials.from_json_keyfile_name('app/main/util/client_secrets_new.json', ['https://www.googleapis.com/auth/analytics.readonly'])

        #Create a service object
        http = credentials.authorize(httplib2.Http())
        service = build('analytics', 'v4', http=http, discoveryServiceUrl=('https://analyticsreporting.googleapis.com/$discovery/rest'))
        response = service.reports().batchGet(
            body={
                "reportRequests": [
                {
                    "viewId": "243407740", 
                    "samplingLevel": "DEFAULT",
                    "filtersExpression": "ga:pagePath==" +url, 
                    "dateRanges": [
                    {
                        "startDate": daysago[0:10],
                        "endDate": "today"
                    }
                    ],
                    "metrics": [
                    {
                        "expression": "ga:pageviews",
                        "alias": ""
                    }
                    ],
                    "dimensions": [
                    {'name': 'ga:date'}
                    ]
                }
                ]
            }
        ).execute()
        
        #create two empty lists that will hold our dimentions and sessions data
        dim = []
        val = []
        date = []
        
        #Extract Data
        for report in response.get('reports', []):
        
            columnHeader = report.get('columnHeader', {})
            dimensionHeaders = columnHeader.get('dimensions', [])
            metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
            rows = report.get('data', {}).get('rows', [])
        
            for row in rows:
        
                dimensions = row.get('dimensions', [])
                dateRangeValues = row.get('metrics', [])
        
                for header, dimension in zip(dimensionHeaders, dimensions):
                    dim.append(dimension)
        
                for i, values in enumerate(dateRangeValues):
                    for metricHeader, value in zip(metricHeaders, values.get('values')):
                        val.append(int(value))
        
        #Sort Data
        # val.reverse()
        # dim.reverse()
        
        df = pd.DataFrame() 
        df["Pageviews"]=val
        for row in dim:
            datetimeobject = datetime.strptime(row,'%Y%m%d')
            date.append(datetimeobject.strftime("%d/%m/%Y"))
        df["date"]=date
        df=df[["date","Pageviews"]]

        # df_list = df.values.tolist()
        # df_list = list(df.values.flatten())
        df_list = json.loads(df.to_json(orient='records'))
        for i in range(len(df_list)):
            if datetime.today().strftime("%d/%m/%Y") == df_list[i]['date']:
                df_list[i]['date'] = "Today"
            
        logger.info("Daily View Report fetched successfully.")
        return df_list
    except:
        logger.exception("Daily View Report could not be fetched.")
        response_object = {
            "status": "fail",
            "message": "Daily View Report could not be fetched."
        }
        return response_object, 400
    
""" ===============================<< dailyViewReport ends >>=============================== """ 
""" ===============================<< Get Monthly Performance starts >>=============================== """ 

def getMonthlyPerformance(data):
    zon = data.zon
    nama_mtk = data.nama_mtk
    bulan = data.bulan
    tahun = data.tahun
    try:
        bulan_int = list(calendar.month_abbr).index(bulan)
        date_list = []
        all_mtb_list = []
        final = {}
        date0,date1,date2,date3,date4,date5,date6,date7,date8,date9,date10,date11,date12,date13,date14,date15,date16,date17,date18,date19,date20,date21,date22,date23,date24,date25,date26,date27,date28,date29,date30 = ([] for i in range(31))
        
        date_arr = CompoundForm.query.filter(and_(extract('year', CompoundForm.tarikh) == tahun,extract('month', CompoundForm.tarikh) == bulan_int),CompoundForm.zon==zon,CompoundForm.id_mtk==nama_mtk).all() 
        for i in date_arr:
            date = i.tarikh
            all_mtb_list.append(i.id_mtb)
            date_day = date.strftime("%d")
            date_list.append(date)
            
        unique_date_list = list(set(date_list))
        unique_all_mtb_list = list(set(all_mtb_list))
        final['mtb_list'] = unique_all_mtb_list
        unique_date_list.sort()
        
        for date in unique_date_list:
            mtb = CompoundForm.query.filter_by(tarikh=date,zon=zon,id_mtk=nama_mtk).with_entities(CompoundForm.id_mtb).all()         
            mtb_date_list = list(set(itertools.chain(*mtb)))
            mtb_not_this_date_list = [i for i in unique_all_mtb_list if i not in mtb_date_list]
            day = date.strftime("%d")
            day1 = int(day)
            
            if day1 == 1:
                date0.append('tarikh')
                date0.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date0.append(i)
                    date0.append(True)
                for i in mtb_not_this_date_list:
                    date0.append(i)
                    date0.append(False)
                    
            if day1 == 2:
                date1.append('tarikh')
                date1.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date1.append(i)
                    date1.append(True)
                for i in mtb_not_this_date_list:
                    date1.append(i)
                    date1.append(False)
                    
            if day1 == 3:
                date2.append('tarikh')
                date2.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date2.append(i)
                    date2.append(True)
                for i in mtb_not_this_date_list:
                    date2.append(i)
                    date2.append(False)
                    
            if day1 == 4:
                date3.append('tarikh')
                date3.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date3.append(i)
                    date3.append(True)
                for i in mtb_not_this_date_list:
                    date3.append(i)
                    date3.append(False)
                    
            if day1 == 5:
                date4.append('tarikh')
                date4.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date4.append(i)
                    date4.append(True)
                for i in mtb_not_this_date_list:
                    date4.append(i)
                    date4.append(False)
                    
            if day1 == 6:
                date5.append('tarikh')
                date5.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date5.append(i)
                    date5.append(True)
                for i in mtb_not_this_date_list:
                    date5.append(i)
                    date5.append(False)
                    
            if day1 == 7:
                date6.append('tarikh')
                date6.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date6.append(i)
                    date6.append(True)
                for i in mtb_not_this_date_list:
                    date6.append(i)
                    date6.append(False)
                    
            if day1 == 8:
                date7.append('tarikh')
                date7.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date7.append(i)
                    date7.append(True)
                for i in mtb_not_this_date_list:
                    date7.append(i)
                    date7.append(False)
                    
            if day1 == 9:
                date8.append('tarikh')
                date8.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date8.append(i)
                    date8.append(True)
                for i in mtb_not_this_date_list:
                    date8.append(i)
                    date8.append(False)
                    
            if day1 == 10:
                date9.append('tarikh')
                date9.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date9.append(i)
                    date9.append(True)
                for i in mtb_not_this_date_list:
                    date9.append(i)
                    date9.append(False)
                    
            if day1 == 11:
                date10.append('tarikh')
                date10.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date10.append(i)
                    date10.append(True)
                for i in mtb_not_this_date_list:
                    date10.append(i)
                    date10.append(False)
                    
            if day1 == 12:
                date11.append('tarikh')
                date11.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date11.append(i)
                    date11.append(True)
                for i in mtb_not_this_date_list:
                    date11.append(i)
                    date11.append(False)
                    
            if day1 == 13:
                date12.append('tarikh')
                date12.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date12.append(i)
                    date12.append(True)
                for i in mtb_not_this_date_list:
                    date12.append(i)
                    date12.append(False)
                    
            if day1 == 14:
                date13.append('tarikh')
                date13.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date13.append(i)
                    date13.append(True)
                for i in mtb_not_this_date_list:
                    date13.append(i)
                    date13.append(False)
                    
            if day1 == 15:
                date14.append('tarikh')
                date14.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date14.append(i)
                    date14.append(True)
                for i in mtb_not_this_date_list:
                    date14.append(i)
                    date14.append(False)
                    
            if day1 == 16:
                date15.append('tarikh')
                date15.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date15.append(i)
                    date15.append(True)
                for i in mtb_not_this_date_list:
                    date15.append(i)
                    date15.append(False)
                    
            if day1 == 17:
                date16.append('tarikh')
                date16.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date16.append(i)
                    date16.append(True)
                for i in mtb_not_this_date_list:
                    date16.append(i)
                    date16.append(False)
                    
            if day1 == 18:
                date17.append('tarikh')
                date17.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date17.append(i)
                    date17.append(True)
                for i in mtb_not_this_date_list:
                    date17.append(i)
                    date17.append(False)
                    
            if day1 == 19:
                date18.append('tarikh')
                date18.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date18.append(i)
                    date18.append(True)
                for i in mtb_not_this_date_list:
                    date18.append(i)
                    date18.append(False)
                    
            if day1 == 20:
                date19.append('tarikh')
                date19.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date19.append(i)
                    date19.append(True)
                for i in mtb_not_this_date_list:
                    date19.append(i)
                    date19.append(False)
                    
            if day1 == 21:
                date20.append('tarikh')
                date20.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date20.append(i)
                    date20.append(True)
                for i in mtb_not_this_date_list:
                    date20.append(i)
                    date20.append(False)
                    
            if day1 == 22:
                date21.append('tarikh')
                date21.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date21.append(i)
                    date21.append(True)
                for i in mtb_not_this_date_list:
                    date21.append(i)
                    date21.append(False)
                    
            if day1 == 23:
                date22.append('tarikh')
                date22.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date22.append(i)
                    date22.append(True)
                for i in mtb_not_this_date_list:
                    date22.append(i)
                    date22.append(False)
                    
            if day1 == 24:
                date23.append('tarikh')
                date23.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date23.append(i)
                    date23.append(True)
                for i in mtb_not_this_date_list:
                    date23.append(i)
                    date23.append(False)
                    
            if day1 == 25:
                date24.append('tarikh')
                date24.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date24.append(i)
                    date24.append(True)
                for i in mtb_not_this_date_list:
                    date24.append(i)
                    date24.append(False)
                    
            if day1 == 26:
                date25.append('tarikh')
                date25.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date25.append(i)
                    date25.append(True)
                for i in mtb_not_this_date_list:
                    date25.append(i)
                    date25.append(False)
                    
            if day1 == 27:
                date26.append('tarikh')
                date26.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date26.append(i)
                    date26.append(True)
                for i in mtb_not_this_date_list:
                    date26.append(i)
                    date26.append(False)
                    
            if day1 == 28:
                date27.append('tarikh')
                date27.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date27.append(i)
                    date27.append(True)
                for i in mtb_not_this_date_list:
                    date27.append(i)
                    date27.append(False)
                    
            if day1 == 29:
                date28.append('tarikh')
                date28.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date28.append(i)
                    date28.append(True)
                for i in mtb_not_this_date_list:
                    date28.append(i)
                    date28.append(False)
                    
            if day1 == 30:
                date29.append('tarikh')
                date29.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date29.append(i)
                    date29.append(True)
                for i in mtb_not_this_date_list:
                    date29.append(i)
                    date29.append(False)
                    
            if day1 == 31:
                date30.append('tarikh')
                date30.append(f'{date.day} {calendar.month_name[bulan_int]} {tahun}')
                for i in mtb_date_list:
                    date30.append(i)
                    date30.append(True)
                for i in mtb_not_this_date_list:
                    date30.append(i)
                    date30.append(False)
        result = []            
        # if not date0:
        #     for i in unique_all_mtb_list:
        #         date0.append(i)
        #         date0.append(False)
        #     date0_dict = {date0[i]:date0[i+1] for i in range(0, len(date0),2)}
        if date0:
            date0_dict = {date0[i]:date0[i+1] for i in range(0, len(date0),2)}
            if date0_dict != {}:
                result.append(date0_dict)
        # if not date1:
        #     for i in unique_all_mtb_list:
        #         date1.append(i)
        #         date1.append(False)
        #     date1_dict = {date1[i]:date1[i+1] for i in range(0, len(date1),2)}
        if date1:
            date1_dict = {date1[i]:date1[i+1] for i in range(0, len(date1),2)}
            if date1_dict != {}:
                result.append(date1_dict)    
        # if not date2:
        #     for i in unique_all_mtb_list:
        #         date2.append(i)
        #         date2.append(False)
        #     date2_dict = {date2[i]:date2[i+1] for i in range(0, len(date2),2)}
        if date2:
            date2_dict = {date2[i]:date2[i+1] for i in range(0, len(date2),2)}
            if date2_dict != {}:
                result.append(date2_dict)    
        # if not date3:
        #     for i in unique_all_mtb_list:
        #         date3.append(i)
        #         date3.append(False)
        #     date3_dict = {date3[i]:date3[i+1] for i in range(0, len(date3),2)}
        if date3:
            date3_dict = {date3[i]:date3[i+1] for i in range(0, len(date3),2)}
            if date3_dict != {}:
                result.append(date3_dict)    
        # if not date4:
        #     for i in unique_all_mtb_list:
        #         date4.append(i)
        #         date4.append(False)
        #     date4_dict = {date4[i]:date4[i+1] for i in range(0, len(date4),2)}
        if date4:
            date4_dict = {date4[i]:date4[i+1] for i in range(0, len(date4),2)}
            if date4_dict != {}:
                result.append(date4_dict)    
        # if not date5:
        #     for i in unique_all_mtb_list:
        #         date5.append(i)
        #         date5.append(False)
        #     date5_dict = {date5[i]:date5[i+1] for i in range(0, len(date5),2)}
        if date5:
            date5_dict = {date5[i]:date5[i+1] for i in range(0, len(date5),2)}
            if date5_dict != {}:
                result.append(date5_dict)    
        # if not date6:
        #     for i in unique_all_mtb_list:
        #         date6.append(i)
        #         date6.append(False)
        #     date6_dict = {date6[i]:date6[i+1] for i in range(0, len(date6),2)}
        if date6:
            date6_dict = {date6[i]:date6[i+1] for i in range(0, len(date6),2)}
            if date6_dict != {}:
                result.append(date6_dict)
        # if not date7:
        #     for i in unique_all_mtb_list:
        #         date7.append(i)
        #         date7.append(False)
        #     date7_dict = {date7[i]:date7[i+1] for i in range(0, len(date7),2)}
        if date7:
            date7_dict = {date7[i]:date7[i+1] for i in range(0, len(date7),2)}
            if date7_dict != {}:
                result.append(date7_dict)
            # if not date8:
        #     for i in unique_all_mtb_list:
        #         date8.append(i)
        #         date8.append(False)
        #     date8_dict = {date8[i]:date8[i+1] for i in range(0, len(date8),2)}
        if date8:
            date8_dict = {date8[i]:date8[i+1] for i in range(0, len(date8),2)}
            if date8_dict != {}:
                result.append(date8_dict)
            # if not date9:
        #     for i in unique_all_mtb_list:
        #         date9.append(i)
        #         date9.append(False)
        #     date9_dict = {date9[i]:date9[i+1] for i in range(0, len(date9),2)}
        if date9:
            date9_dict = {date9[i]:date9[i+1] for i in range(0, len(date9),2)}
            if date9_dict != {}:
                result.append(date9_dict)
        # if not date10:
        #     for i in unique_all_mtb_list:
        #         date10.append(i)
        #         date10.append(False)
        #     date10_dict = {date10[i]:date10[i+1] for i in range(0, len(date10),2)}
        if date10:
            date10_dict = {date10[i]:date10[i+1] for i in range(0, len(date10),2)}
            if date10_dict != {}:
                result.append(date10_dict)
        # if not date11:
        #     for i in unique_all_mtb_list:
        #         date11.append(i)
        #         date11.append(False)
        #     date11_dict = {date11[i]:date11[i+1] for i in range(0, len(date11),2)}
        if date11:
            date11_dict = {date11[i]:date11[i+1] for i in range(0, len(date11),2)}
            if date11_dict != {}:
                result.append(date11_dict)
        # if not date12:
        #     for i in unique_all_mtb_list:
        #         date12.append(i)
        #         date12.append(False)
        #     date12_dict = {date12[i]:date12[i+1] for i in range(0, len(date12),2)}
        if date12:
            date12_dict = {date12[i]:date12[i+1] for i in range(0, len(date12),2)}
            if date12_dict != {}:
                result.append(date12_dict)
        # if not date13:
        #     for i in unique_all_mtb_list:
        #         date13.append(i)
        #         date13.append(False)
        #     date13_dict = {date13[i]:date13[i+1] for i in range(0, len(date13),2)}
        if date13:
            date13_dict = {date13[i]:date13[i+1] for i in range(0, len(date13),2)}
            if date13_dict != {}:
                result.append(date13_dict)
        # if not date14:
        #     for i in unique_all_mtb_list:
        #         date14.append(i)
        #         date14.append(False)
        #     date14_dict = {date14[i]:date14[i+1] for i in range(0, len(date14),2)}
        if date14:
            date14_dict = {date14[i]:date14[i+1] for i in range(0, len(date14),2)}
            if date14_dict != {}:
                result.append(date14_dict)
        # if not date15:
        #     for i in unique_all_mtb_list:
        #         date15.append(i)
        #         date15.append(False)
        #     date15_dict = {date15[i]:date15[i+1] for i in range(0, len(date15),2)}
        if date15:
            date15_dict = {date15[i]:date15[i+1] for i in range(0, len(date15),2)}
            if date15_dict != {}:
                result.append(date15_dict)
        # if not date16:
        #     for i in unique_all_mtb_list:
        #         date16.append(i)
        #         date16.append(False)
        #     date16_dict = {date16[i]:date16[i+1] for i in range(0, len(date16),2)}
        if date16:
            date16_dict = {date16[i]:date16[i+1] for i in range(0, len(date16),2)}
            if date16_dict != {}:
                result.append(date16_dict)
        # if not date17:
        #     for i in unique_all_mtb_list:
        #         date17.append(i)
        #         date17.append(False)
        #     date17_dict = {date17[i]:date17[i+1] for i in range(0, len(date17),2)}
        if date17:
            date17_dict = {date17[i]:date17[i+1] for i in range(0, len(date17),2)}
            if date17_dict != {}:
                result.append(date17_dict)
        # if not date18:
        #     for i in unique_all_mtb_list:
        #         date18.append(i)
        #         date18.append(False)
        #     date18_dict = {date18[i]:date18[i+1] for i in range(0, len(date18),2)}
        if date18:
            date18_dict = {date18[i]:date18[i+1] for i in range(0, len(date18),2)}
            if date18_dict != {}:
                result.append(date18_dict)
        # if not date19:
        #     for i in unique_all_mtb_list:
        #         date19.append(i)
        #         date19.append(False)
        #     date19_dict = {date19[i]:date19[i+1] for i in range(0, len(date19),2)}
        if date19:
            date19_dict = {date19[i]:date19[i+1] for i in range(0, len(date19),2)}
            if date19_dict != {}:
                result.append(date19_dict)
        # if not date20:
        #     for i in unique_all_mtb_list:
        #         date20.append(i)
        #         date20.append(False)
        #     date20_dict = {date20[i]:date20[i+1] for i in range(0, len(date20),2)}
        if date20:
            date20_dict = {date20[i]:date20[i+1] for i in range(0, len(date20),2)}
            if date20_dict != {}:
                result.append(date20_dict)
        # if not date21:
        #     for i in unique_all_mtb_list:
        #         date21.append(i)
        #         date21.append(False)
        #     date21_dict = {date21[i]:date21[i+1] for i in range(0, len(date21),2)}
        if date21:
            date21_dict = {date21[i]:date21[i+1] for i in range(0, len(date21),2)}
            if date21_dict != {}:
                result.append(date21_dict)
        # if not date22:
        #     for i in unique_all_mtb_list:
        #         date22.append(i)
        #         date22.append(False)
        #     date22_dict = {date22[i]:date22[i+1] for i in range(0, len(date22),2)}
        if date22:
            date22_dict = {date22[i]:date22[i+1] for i in range(0, len(date22),2)}
            if date22_dict != {}:
                result.append(date22_dict)
        # if not date23:
        #     for i in unique_all_mtb_list:
        #         date23.append(i)
        #         date23.append(False)
        #     date23_dict = {date23[i]:date23[i+1] for i in range(0, len(date23),2)}
        if date23:
            date23_dict = {date23[i]:date23[i+1] for i in range(0, len(date23),2)}
            if date23_dict != {}:
                result.append(date23_dict)
        # if not date24:
        #     for i in unique_all_mtb_list:
        #         date24.append(i)
        #         date24.append(False)
        #     date24_dict = {date24[i]:date24[i+1] for i in range(0, len(date24),2)}
        if date24:
            date24_dict = {date24[i]:date24[i+1] for i in range(0, len(date24),2)}
            if date24_dict != {}:
                result.append(date24_dict)
        # if not date25:
        #     for i in unique_all_mtb_list:
        #         date25.append(i)
        #         date25.append(False)
        #     date25_dict = {date25[i]:date25[i+1] for i in range(0, len(date25),2)}
        if date25:
            date25_dict = {date25[i]:date25[i+1] for i in range(0, len(date25),2)}
            if date25_dict != {}:
                result.append(date25_dict)
        # if not date26:
        #     for i in unique_all_mtb_list:
        #         date26.append(i)
        #         date26.append(False)
        #     date26_dict = {date26[i]:date26[i+1] for i in range(0, len(date26),2)}
        if date26:
            date26_dict = {date26[i]:date26[i+1] for i in range(0, len(date26),2)}
            if date26_dict != {}:
                result.append(date26_dict)
        # if not date27:
        #     for i in unique_all_mtb_list:
        #         date27.append(i)
        #         date27.append(False)
        #     date27_dict = {date27[i]:date27[i+1] for i in range(0, len(date27),2)}
        if date27:
            date27_dict = {date27[i]:date27[i+1] for i in range(0, len(date27),2)}
            if date27_dict != {}:
                result.append(date27_dict)
        # if not date28:
        #     for i in unique_all_mtb_list:
        #         date28.append(i)
        #         date28.append(False)
        #     date28_dict = {date28[i]:date28[i+1] for i in range(0, len(date28),2)}
        if date28:
            date28_dict = {date28[i]:date28[i+1] for i in range(0, len(date28),2)}
            if date28_dict != {}:
                result.append(date28_dict)
        # if not date29:
        #     for i in unique_all_mtb_list:
        #         date29.append(i)
        #         date29.append(False)
        #     date29_dict = {date29[i]:date29[i+1] for i in range(0, len(date29),2)}
        if date29:
            date29_dict = {date29[i]:date29[i+1] for i in range(0, len(date29),2)}
            if date29_dict != {}:
                result.append(date29_dict)
        # if not date30:
        #     for i in unique_all_mtb_list:
        #         date30.append(i)
        #         date30.append(False)
        #     date30_dict = {date30[i]:date30[i+1] for i in range(0, len(date30),2)}
        if date30:
            date30_dict = {date30[i]:date30[i+1] for i in range(0, len(date30),2)}
            if date30_dict != {}:
                result.append(date30_dict)
        
        
        logger.info("Monthly Performance fetched successfully.")
        final['monthly_data'] = result
        return final
        
    except:
        logger.exception("Monthly Performance could not be fetched.")
        response_obj = {
            "status" : "fail",
            "message" : "Monthly Performance could not be fetched."
        }
        return response_obj, 400

""" ===============================<< Get Monthly Performance Ends >>=============================== """ 
""" ===============================<< getNamaMTK Starts >>=============================== """ 

def getNamaMTK(data):
    zon = data.zon
    try:
        mtk = OfficersList.query.with_entities(MasterUser.nama).distinct().filter_by(zon=zon,role='MerinyuMTK').all()
        mtk_list = list(itertools.chain(*mtk))
        
        logger.info("Mtk list fetched successfully.")
        return mtk_list
    
    except:
        logger.exception("Mtk list could not be fetched.")
        response_obj = {
            "status" : "fail",
            "message" : "Mtk list could not be fetched."
        }
        return response_obj, 400
""" ===============================<< getNamaMTK Ends >>=============================== """
""" ===============================<<Fetch map co-ordinates starts >>=============================== """ 

def fetchMapCoordinates(data):
    # id_mtb = 'MTB'+data.id_mtk[3:]
    id_mtk = data.id_mtk
    zon = data.zon
    mtb_info = db.session.query(CompoundForm.id_mtb).distinct().filter_by(zon=zon).all()
    mtb_list = []
    for i in mtb_info:
        mtb_list.append(i.id_mtb)
    final = {}
    finale = []
    print(mtb_list)
    for id_mtb in mtb_list:
        
        try:
            mtb_coordinates = []
            for coordinate in CompoundForm.query.filter_by(id_mtb=id_mtb, zon=zon, active=1):
                mtb_coordinates.append({
                    
                    "latitude" : coordinate.latitude,
                    "longitude" : coordinate.longitude
                })
            if mtb_coordinates != []:
                initial_list = []
                initial_list.append(mtb_coordinates)
                final[f'{id_mtb}'] =  initial_list
                
        except:
            logger.exception("Coordinates could not be fetched")
            response_object = {
                'status': 'fail',
                'message': 'Coordinates could not be fetched',
            }
            return response_object, 400
        initial_list = []
    # finale.append(final.copy())
    logger.info("Map co-ordinates fetched successfully.")
    return final
    
    
""" ===============================<<Fetch map co-ordinates ends >>=============================== """
""" ===============================<< Register New User by Admin >>=============================== """

def adminUserAdd(data):
    name = data.name.upper()
    nama_pengguna = data.nama_pengguna
    email = data.email
    password = data.password

    if MasterUser.find_by_email(email):
        abort(HTTPStatus.CONFLICT,"email_exists", status="fail")
    if MasterUser.find_by_nama_pengguna(nama_pengguna):
            abort(HTTPStatus.CONFLICT,"user_exists", status="fail")
    if MasterUser.find_by_nama(name):
            abort(HTTPStatus.CONFLICT,"user_exists", status="fail")
            
    try:
        user_type = 'dbkl'
        parlimen = ''
        role = 'Analisis'
        lock_time = '9999-12-31 23:59:59.000'
        updated_user = MasterUser(
            nama=nama_pengguna, no_kad_pengenalan=name, nama_pengguna=name, alamat_emel=email, kata_laluan=password, user_type=user_type, role=role, parlimen=parlimen, lock_time=lock_time)
            # nama=name, no_kad_pengenalan=nama_pengguna, nama_pengguna=nama_pengguna, alamat_emel=email, password=password, user_type=user_type, role=role)
        db.session.add(updated_user)
        
        db.session.commit()
        logger.info("User Registered")
        response = {
            'status': 'success',
            'message': 'user_added'
        }
        return response, 201
    except:
        logger.exception("User not registered")
        response_object = {
            'status': 'fail',
            'message': 'user_not_added',
        }
        return response_object, 409
        
""" ===============================<< Register New User by Admin >>=============================== """
""" ===============================<< Compound Analysis >>=============================== """

def getMonthlyAnalysis(year, month):
    monthlyDataDict = {}
    monthlyData = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month).all()
    sek82_5,sek69,sek47_1a,sek47_1b,sek47_1d,sek47_1e,sek47_1g,sek47_2a,uuk8,uuk9,uuk3,sek46_1b,sek46_1c,sek46_1d,sek46_1e,sek46_1g,uuk33,uuk34,uuk35 = (0,)*19
    if monthlyData != []:
        sek82_5 = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek82_5 = True).count()
        sek69 = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek69 = True).count()
        sek47_1a = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek47_1a = True).count()
        sek47_1b = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek47_1b = True).count()
        sek47_1d = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek47_1d = True).count()
        sek47_1e = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek47_1e = True).count()
        sek47_1g = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek47_1g = True).count()
        sek47_2a = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek47_2a = True).count()
        uuk8 = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, uuk8 = True).count()
        uuk9 = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, uuk9 = True).count()
        uuk3 = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, uuk3 = True).count()
        sek46_1b = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek46_1b = True).count()
        sek46_1c = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek46_1c = True).count()
        sek46_1d = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek46_1d = True).count()
        sek46_1e = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek46_1e = True).count()
        sek46_1g = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, sek46_1g = True).count()
        uuk33 = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, uuk33 = True).count()
        uuk34 = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, uuk34 = True).count()
        uuk35 = db.session.query(CompoundForm).filter_by(tahun=year, bulan=month, uuk35 = True).count()
    total = sek82_5+sek69+sek47_1a+sek47_1b+sek47_1d+sek47_1e+sek47_1g+sek47_2a+uuk8+uuk9+uuk3+sek46_1b+sek46_1c+sek46_1d+sek46_1e+sek46_1g+uuk33+uuk34+uuk35
    monthlyDataDict['sek82_5'] = sek82_5
    monthlyDataDict['sek69'] = sek69
    monthlyDataDict['sek47_1a'] = sek47_1a
    monthlyDataDict['sek47_1b'] = sek47_1b
    monthlyDataDict['sek47_1d'] = sek47_1d
    monthlyDataDict['sek47_1e'] = sek47_1e
    monthlyDataDict['sek47_1g'] = sek47_1g
    monthlyDataDict['sek47_2a'] = sek47_2a
    monthlyDataDict['uuk8'] = uuk8
    monthlyDataDict['uuk9'] = uuk9
    monthlyDataDict['uuk3'] = uuk3
    monthlyDataDict['sek46_1b'] = sek46_1b
    monthlyDataDict['sek46_1c'] = sek46_1c
    monthlyDataDict['sek46_1d'] = sek46_1d
    monthlyDataDict['sek46_1e'] = sek46_1e
    monthlyDataDict['sek46_1g'] = sek46_1g
    monthlyDataDict['uuk33'] = uuk33
    monthlyDataDict['uuk34'] = uuk34
    monthlyDataDict['uuk35'] = uuk35
    monthlyDataDict['total'] = total
    return monthlyDataDict

def monthlyTotalCount(year):
    monthlyTotalCountDict = {}
    monthlyData = db.session.query(CompoundForm).filter_by(tahun=year).all()
    sek82_5,sek69,sek47_1a,sek47_1b,sek47_1d,sek47_1e,sek47_1g,sek47_2a,uuk8,uuk9,uuk3,sek46_1b,sek46_1c,sek46_1d,sek46_1e,sek46_1g,uuk33,uuk34,uuk35 = (0,)*19
    if monthlyData != []:
        sek82_5 = db.session.query(CompoundForm).filter_by(tahun=year, sek82_5 = True).count()
        sek69 = db.session.query(CompoundForm).filter_by(tahun=year, sek69 = True).count()
        sek47_1a = db.session.query(CompoundForm).filter_by(tahun=year, sek47_1a = True).count()
        sek47_1b = db.session.query(CompoundForm).filter_by(tahun=year, sek47_1b = True).count()
        sek47_1d = db.session.query(CompoundForm).filter_by(tahun=year, sek47_1d = True).count()
        sek47_1e = db.session.query(CompoundForm).filter_by(tahun=year, sek47_1e = True).count()
        sek47_1g = db.session.query(CompoundForm).filter_by(tahun=year, sek47_1g = True).count()
        sek47_2a = db.session.query(CompoundForm).filter_by(tahun=year, sek47_2a = True).count()
        uuk8 = db.session.query(CompoundForm).filter_by(tahun=year, uuk8 = True).count()
        uuk9 = db.session.query(CompoundForm).filter_by(tahun=year, uuk9 = True).count()
        uuk3 = db.session.query(CompoundForm).filter_by(tahun=year, uuk3 = True).count()
        sek46_1b = db.session.query(CompoundForm).filter_by(tahun=year, sek46_1b = True).count()
        sek46_1c = db.session.query(CompoundForm).filter_by(tahun=year, sek46_1c = True).count()
        sek46_1d = db.session.query(CompoundForm).filter_by(tahun=year, sek46_1d = True).count()
        sek46_1e = db.session.query(CompoundForm).filter_by(tahun=year, sek46_1e = True).count()
        sek46_1g = db.session.query(CompoundForm).filter_by(tahun=year, sek46_1g = True).count()
        uuk33 = db.session.query(CompoundForm).filter_by(tahun=year, uuk33 = True).count()
        uuk34 = db.session.query(CompoundForm).filter_by(tahun=year, uuk34 = True).count()
        uuk35 = db.session.query(CompoundForm).filter_by(tahun=year, uuk35 = True).count()
    total = sek82_5+sek69+sek47_1a+sek47_1b+sek47_1d+sek47_1e+sek47_1g+sek47_2a+uuk8+uuk9+uuk3+sek46_1b+sek46_1c+sek46_1d+sek46_1e+sek46_1g+uuk33+uuk34+uuk35
    monthlyTotalCountDict['sek82_5_total'] = sek82_5
    monthlyTotalCountDict['sek69_total'] = sek69
    monthlyTotalCountDict['sek47_1a_total'] = sek47_1a
    monthlyTotalCountDict['sek47_1b_total'] = sek47_1b
    monthlyTotalCountDict['sek47_1d_total'] = sek47_1d
    monthlyTotalCountDict['sek47_1e_total'] = sek47_1e
    monthlyTotalCountDict['sek47_1g_total'] = sek47_1g
    monthlyTotalCountDict['sek47_2a_total'] = sek47_2a
    monthlyTotalCountDict['uuk8_total'] = uuk8
    monthlyTotalCountDict['uuk9_total'] = uuk9
    monthlyTotalCountDict['uuk3_total'] = uuk3
    monthlyTotalCountDict['sek46_1b_total'] = sek46_1b
    monthlyTotalCountDict['sek46_1c_total'] = sek46_1c
    monthlyTotalCountDict['sek46_1d_total'] = sek46_1d
    monthlyTotalCountDict['sek46_1e_total'] = sek46_1e
    monthlyTotalCountDict['sek46_1g_total'] = sek46_1g
    monthlyTotalCountDict['uuk33_total'] = uuk33
    monthlyTotalCountDict['uuk34_total'] = uuk34
    monthlyTotalCountDict['uuk35_total'] = uuk35
    monthlyTotalCountDict['total_total'] = total
    return monthlyTotalCountDict


@token_required    
def compoundAnalysis():
    user = get_logged_in_user()
    try:
        if user.role == 'Superadmin' or user.role == 'Analisis' or user.role == 'Kewangan' or user.role == 'Analisis,MerinyuMTB,MerinyuMTK':
            """
            print(db.session.query(CompoundForm.tahun).distinct().count())
            for year_info in db.session.query(CompoundForm.tahun).distinct():
                compoundAnalysisDict['year'] = year_info.tahun
                print("year_info.tahun",year_info.tahun)
            """

            curr_year = datetime.now().year
            monthlyAnalysisDict = {}
            monthlyAnalysisList = []
            monthlyCountDict = {}
            # print(db.session.query(CompoundForm.bulan).distinct().filter_by(tahun=curr_year).count())
            month_list = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
            # for month_info in db.session.query(CompoundForm.bulan).filter_by(tahun=curr_year).distinct():
            for month_info in month_list:
                # print("month_info.bulan",month_info.bulan)
                month = month_info
                year = curr_year
                if month == 'JAN':
                    monthlyAnalysisDict['month'] = 'January'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'FEB':
                    monthlyAnalysisDict['month'] = 'February'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'MAR':
                    monthlyAnalysisDict['month'] = 'March'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'APR':
                    monthlyAnalysisDict['month'] = 'April'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'MAY':
                    monthlyAnalysisDict['month'] = 'May'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'JUN':
                    monthlyAnalysisDict['month'] = 'June'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'JUL':
                    monthlyAnalysisDict['month'] = 'July'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'AUG':
                    monthlyAnalysisDict['month'] = 'August'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'SEP':
                    monthlyAnalysisDict['month'] = 'September'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'OCT':
                    monthlyAnalysisDict['month'] = 'October'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'NOV':
                    monthlyAnalysisDict['month'] = 'November'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                if month == 'DEC':
                    monthlyAnalysisDict['month'] = 'December'
                    monthlyAnalysisDict['monthlydata'] = getMonthlyAnalysis(year,month)
                monthlyAnalysisList.append(monthlyAnalysisDict.copy())
            
            monthlyCountDict['totalData'] = monthlyTotalCount(curr_year)
            monthlyAnalysisList.append(monthlyCountDict)
            logger.info("Compound Anlysis Fetched")
            return monthlyAnalysisList
        else:
            response = dict(status= 'fail', message='not_authorized')
            return response, 401
    except:
        logger.exception("Compound Anlysis Could Not Be Fetched")
        response = dict(status= 'fail', message='Compound Anlysis Could Not Be Fetched')
        return response, 400

""" ===============================<< Compound Analysis >>=============================== """
@token_required
def getCompoundCount():
    user = get_logged_in_user()
    try:
        if user.role == 'Superadmin' or user.role == 'Analisis' or user.role == 'Kewangan' or user.role == 'Analisis,MerinyuMTB,MerinyuMTK':
            curr_year = datetime.now().year
            parlimenDict ={}
            parlimenList=[]
            monthlyTotalCountDict = {}
            monthlyFinalCountDict = {}
            monthlyFinalCountList = []
            for parlimen_info in db.session.query(CompoundForm.parlimen).distinct().filter_by(tahun=curr_year):
                monthlyCountDict = {}
                yearlyCountList = []
                parlimenDict['parlimen']=  parlimen_info.parlimen
                january = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='JAN').count()
                february = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='FEB').count()
                march = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='MAR').count()
                april = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='APR').count()
                may = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='MAY').count()
                june = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='JUN').count()
                july = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='JUL').count()
                august = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='AUG').count()
                september = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='SEP').count()
                october = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='OCT').count()
                november = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='NOV').count()
                december = db.session.query(CompoundForm).filter_by(parlimen=parlimen_info.parlimen, bulan='DEC').count()
                yearly_total = january+february+march+april+may+june+july+august+september+october+november+december
                monthlyCountDict['January'] = january
                monthlyCountDict['February'] = february 
                monthlyCountDict['March'] = march
                monthlyCountDict['April'] = april
                monthlyCountDict['May'] = may
                monthlyCountDict['June'] = june
                monthlyCountDict['July'] = july
                monthlyCountDict['August'] = august
                monthlyCountDict['September'] = september
                monthlyCountDict['October'] = october
                monthlyCountDict['November'] = november
                monthlyCountDict['December'] = december
                monthlyCountDict['total'] = yearly_total
                yearlyCountList.append(monthlyCountDict.copy())
                parlimenDict['dataCount'] = yearlyCountList
                parlimenList.append(parlimenDict.copy())
            total_january = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='JAN').count()
            total_february = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='FEB').count()
            total_march = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='MAR').count()
            total_april = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='APR').count()
            total_may = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='MAY').count()
            total_june = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='JUN').count()
            total_july = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='JUL').count()
            total_august = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='AUG').count()
            total_september = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='SEP').count()
            total_october = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='OCT').count()
            total_november = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='NOV').count()
            total_december = db.session.query(CompoundForm).filter_by(tahun=curr_year, bulan='DEC').count()
            monthlyFinalCountDict['parlimen']=  'Jumlah'
            monthlyTotalCountDict['January'] = total_january
            monthlyTotalCountDict['February'] = total_february
            monthlyTotalCountDict['March'] = total_march
            monthlyTotalCountDict['April'] = total_april
            monthlyTotalCountDict['May'] = total_may
            monthlyTotalCountDict['June'] = total_june
            monthlyTotalCountDict['July'] = total_july
            monthlyTotalCountDict['August'] = total_august
            monthlyTotalCountDict['September'] = total_september
            monthlyTotalCountDict['October'] = total_october
            monthlyTotalCountDict['November'] = total_november
            monthlyTotalCountDict['December'] = total_december
            monthlyTotalCountDict['total'] = total_january + total_february + total_march + total_april + total_may + total_june + total_july + total_august + total_september + total_october + total_november + total_december
            monthlyFinalCountList.append(monthlyTotalCountDict)
            monthlyFinalCountDict['dataCount'] = monthlyFinalCountList

            parlimenList.append(monthlyFinalCountDict)
            logger.info("Compound Count Fetched")
            return parlimenList
        else:
            response = dict(status= 'fail', message='not_authorized')
            return response, 401
    except:
        logger.exception("Compound Count Could Not Be Fetched")
        response = dict(status= 'fail', message='Compound Count Could Not Be Fetched')
        return response, 400
""" ===============================<< Compound Analysis >>=============================== """
""" ===============================<< getParlimen Starts >>=============================== """
# @token_required
def getParlimen():
    try:
        parlimen = MapData.query.distinct().with_entities(MapData.parlimen).all()         
        parlimen_list = list(itertools.chain(*parlimen)) 
        logger.info("Parlimen List fetched")
        return parlimen_list
    except:
        logger.exception("parlimen list could not be fetched")
        response = dict(status= 'fail', message='parlimen list could not be fetched')
        return response,400 
""" ===============================<< getParlimen Ends >>=============================== """
""" ===============================<< getNamaJalan Starts >>=============================== """
# @token_required
def getNamaJalan(parlimen):
    try:
        nama_jalan = MapData.query.distinct().filter_by(parlimen=parlimen).with_entities(MapData.nama_jalan).all()         
        nama_jalan_list = list(itertools.chain(*nama_jalan)) 
        logger.info("Nama Jalan fetched")
        return nama_jalan_list
    except:
        logger.exception("Nama Jalan list could not be fetched")
        response = dict(status= 'fail', message='Nama Jalan list could not be fetched')
        return response,400 
""" ===============================<< getNamaJalan Ends >>=============================== """
""" ===============================<< getNamaTaman Starts >>=============================== """
# @token_required
def getNamaTaman(data):
    parlimen = data.parlimen
    nama_jalan = data.nama_jalan
    try:
        nama_taman = MapData.query.distinct().filter_by(parlimen=parlimen,nama_jalan=nama_jalan).with_entities(MapData.nama_taman).all()         
        nama_taman_list = list(itertools.chain(*nama_taman)) 
        logger.info("Nama Taman fetched")
        return nama_taman_list
    except:
        logger.exception("Nama Taman list could not be fetched")
        response = dict(status= 'fail', message='Nama Taman list could not be fetched')
        return response,400 
""" ===============================<< getNamaTaman Ends >>=============================== """
""" ===============================<< getNamaKawasan Starts >>=============================== """
# @token_required
def getNamaKawasan(data):
    parlimen = data.parlimen
    nama_taman = data.nama_taman
    nama_jalan = data.nama_jalan
    try:
        nama_kawasan = MapData.query.distinct().filter_by(parlimen=parlimen,nama_taman=nama_taman,nama_jalan=nama_jalan).with_entities(MapData.nama_kawasan).all()         
        nama_kawasan_list = list(itertools.chain(*nama_kawasan)) 
        logger.info("Nama Kawasan fetched")
        return nama_kawasan_list
    except:
        logger.exception("Nama Kawasan list could not be fetched")
        response = dict(status= 'fail', message='Nama Kawasan list could not be fetched')
        return response,400 
""" ===============================<< getNamaKawasan Ends >>=============================== """
""" ===============================<< getMapLapisanFitur Starts >>=============================== """
# @token_required
def getMapLapisanFitur(data):
    parlimen = data.parlimen
    nama_taman = data.nama_taman
    nama_jalan = data.nama_jalan
    nama_kawasan = data.nama_kawasan
    try:
        # lapisan_fitur = MapData.query.distinct().filter_by(parlimen=parlimen,nama_taman=nama_taman,nama_jalan=nama_jalan,nama_kawasan=nama_kawasan).with_entities(MapData.lapisan_fitur).all()         
        lapisan_fitur = MapData.query.distinct().with_entities(MapData.lapisan_fitur).all()         
        lapisan_fitur_list = list(set(itertools.chain(*lapisan_fitur))) 
        return lapisan_fitur_list
        logger.info("lapisan fitur fetched")
        
    except:
        logger.exception("lapisan fitur not fetched")
        response = dict(status= 'fail', message='lapisan fitur not fetched')
        return response,400
""" ===============================<< getMapLapisanFitur Ends >>=============================== """
""" ===============================<< getPetaKawasan Starts >>=============================== """
# @token_required
def getPetaKawasan(data):
    try:
        parlimen = data.parlimen
        nama_taman = data.nama_taman
        nama_jalan = data.nama_jalan
        nama_kawasan = data.nama_kawasan
        lapisan_fitur = data.lapisan_fitur
        servis_perkhidmatan_jkas = data.servis_perkhidmatan_jkas
        coordinateList = []

        if servis_perkhidmatan_jkas == 'Kutipan Sisa Pepejal':
            petaKawasanList = db.session.query(MapData).filter_by(parlimen=parlimen,nama_taman=nama_taman,nama_jalan=nama_jalan,nama_kawasan=nama_kawasan,lapisan_fitur=lapisan_fitur,servis_per='YA').all()         
            if petaKawasanList != []:
                for coordinateInfo in petaKawasanList:
                    coordinateList.append({
                        "latitude": coordinateInfo.latitude,
                        "longitude": coordinateInfo.longitude
                    })
        if servis_perkhidmatan_jkas == 'Pembersihan Awam':
            petaKawasanList = db.session.query(MapData).filter_by(parlimen=parlimen,nama_taman=nama_taman,nama_jalan=nama_jalan,nama_kawasan=nama_kawasan,lapisan_fitur=lapisan_fitur,servis_per='TIDAK').all()         
            if petaKawasanList != []:
                for coordinateInfo in petaKawasanList:
                    coordinateList.append({
                        "latitude": coordinateInfo.latitude,
                        "longitude": coordinateInfo.longitude
                    })
        logger.info("Peta Kawasan fetched")
        return coordinateList
        
    except:
        logger.exception("Peta Kawasan could not be fetched")
        response = dict(status= 'fail', message='Peta Kawasan could could not be fetched')
        return response,400
""" ===============================<< getPetaKawasan Ends >>=============================== """
""" ===============================<< getJadualKutipan Starts >>=============================== """
def getJadualKutipan(data):
    try:
        parlimen = data.parlimen
        nama_taman = data.nama_taman
        nama_jalan = data.nama_jalan
        nama_kawasan = data.nama_kawasan
        lapisan_fitur = data.lapisan_fitur
        kekerapan = data.kekerapan
        jadualKutipan = []
        if kekerapan == 'SAMPAH PUKAL':
            sampahPukalDataList = db.session.query(MapData).filter(MapData.parlimen==parlimen,MapData.nama_taman==nama_taman,MapData.nama_jalan==nama_jalan,MapData.nama_kawasan==nama_kawasan,MapData.lapisan_fitur==lapisan_fitur,MapData.kekerapan!='').all()         
            if sampahPukalDataList != []:
                for each_sampah_pukal_data in sampahPukalDataList:
                    jadualKutipan.append({
                        "latitude": each_sampah_pukal_data.latitude,
                        "longitude": each_sampah_pukal_data.longitude,
                        "parlimen": each_sampah_pukal_data.parlimen,
                        "taman": each_sampah_pukal_data.nama_taman,
                        "jalan": each_sampah_pukal_data.nama_jalan,
                        "kawasan": each_sampah_pukal_data.nama_kawasan,
                        "aktiviti": '',
                        "kekerapan": each_sampah_pukal_data.kekerapan,
                    })
        if kekerapan == 'SISA DOMESTIK':
            sisaDomesDataList = db.session.query(MapData).filter(MapData.parlimen==parlimen,MapData.nama_taman==nama_taman,MapData.nama_jalan==nama_jalan,MapData.nama_kawasan==nama_kawasan,MapData.lapisan_fitur==lapisan_fitur,MapData.kekerapan_0!='').all()         
            if sisaDomesDataList != []:
                for each_sampah_pukal_data in sisaDomesDataList:
                    jadualKutipan.append({
                        "latitude": each_sampah_pukal_data.latitude,
                        "longitude": each_sampah_pukal_data.longitude,
                        "parlimen": each_sampah_pukal_data.parlimen,
                        "taman": each_sampah_pukal_data.nama_taman,
                        "jalan": each_sampah_pukal_data.nama_jalan,
                        "kawasan": each_sampah_pukal_data.nama_kawasan,
                        "aktiviti": '',
                        "kekerapan": each_sampah_pukal_data.kekerapan_0,
                    })
        logger.info("Jadual Kutipa fetched")
        return jadualKutipan
        
    except:
        logger.exception("Jadual Kutipa could not be fetched")
        response = dict(status= 'fail', message='Jadual Kutipa could could not be fetched')
        return response,400
""" ===============================<< getJadualKutipan Ends >>=============================== """
""" ===============================<< get2ndPetaKawasan Starts >>=============================== """
# @token_required
def get2ndPetaKawasan(data):
    try:
        parlimen = data.parlimen
        nama_taman = data.nama_taman
        nama_jalan = data.nama_jalan
        nama_kawasan = data.nama_kawasan
        lapisan_fitur = data.lapisan_fitur
        servis_perkhidmatan_jkas = data.servis_perkhidmatan_jkas
        coordinateList = []

        if servis_perkhidmatan_jkas == 'Kutipan Sisa Pepejal':
            petaKawasanList = db.session.query(MapData).filter_by(parlimen=parlimen,nama_taman=nama_taman,nama_jalan=nama_jalan,nama_kawasan=nama_kawasan,lapisan_fitur=lapisan_fitur,servis_per='YA').all()         
            if petaKawasanList != []:
                for coordinateInfo in petaKawasanList:
                    coordinateList.append({
                        "latitude": coordinateInfo.latitude,
                        "longitude": coordinateInfo.longitude,
                        "servis_perkhidmatan_jkas": coordinateInfo.servis_per,
                    })
        if servis_perkhidmatan_jkas == 'Pembersihan Awam':
            petaKawasanList = db.session.query(MapData).filter_by(parlimen=parlimen,nama_taman=nama_taman,nama_jalan=nama_jalan,nama_kawasan=nama_kawasan,lapisan_fitur=lapisan_fitur,servis_per='TIDAK').all()         
            if petaKawasanList != []:
                for coordinateInfo in petaKawasanList:
                    coordinateList.append({
                        "latitude": coordinateInfo.latitude,
                        "longitude": coordinateInfo.longitude,
                        "servis_perkhidmatan_jkas": coordinateInfo.servis_per,
                    })
        logger.info("2nd Peta Kawasan fetched")
        return coordinateList
        
    except:
        logger.exception("2nd Peta Kawasan could not be fetched")
        response = dict(status= 'fail', message='2nd Peta Kawasan could could not be fetched')
        return response,400
""" ===============================<< get2ndPetaKawasan Ends >>=============================== """
""" ===============================<< getJadualPembersihan Starts >>=============================== """
def getJadualPembersihan(data):
    try:
        parlimen = data.parlimen
        nama_taman = data.nama_taman
        nama_jalan = data.nama_jalan
        nama_kawasan = data.nama_kawasan
        lapisan_fitur = data.lapisan_fitur
        aktiviti = data.aktiviti
        jadualKutipan = []
        if aktiviti == 'SAPUAN':
            sapuanDataList = db.session.query(MapData).filter(MapData.parlimen==parlimen,MapData.nama_taman==nama_taman,MapData.nama_jalan==nama_jalan,MapData.nama_kawasan==nama_kawasan,MapData.lapisan_fitur==lapisan_fitur,MapData.kekerapan_2!='').all()         
            print(sapuanDataList)
            if sapuanDataList != []:
                for each_sampah_pukal_data in sapuanDataList:
                    jadualKutipan.append({
                        "latitude": each_sampah_pukal_data.latitude,
                        "longitude": each_sampah_pukal_data.longitude,
                        "parlimen": each_sampah_pukal_data.parlimen,
                        "taman": each_sampah_pukal_data.nama_taman,
                        "jalan": each_sampah_pukal_data.nama_jalan,
                        "kawasan": each_sampah_pukal_data.nama_kawasan,
                        "aktiviti": each_sampah_pukal_data.kekerapan_2,
                        "kekerapan": each_sampah_pukal_data.kekerapan,
                    })
        if aktiviti == 'CUCIAN':
            cucianDataList = db.session.query(MapData).filter(MapData.parlimen==parlimen,MapData.nama_taman==nama_taman,MapData.nama_jalan==nama_jalan,MapData.nama_kawasan==nama_kawasan,MapData.lapisan_fitur==lapisan_fitur,MapData.kekerapan_4!='').all()         
            if cucianDataList != []:
                for each_sampah_pukal_data in cucianDataList:
                    jadualKutipan.append({
                        "latitude": each_sampah_pukal_data.latitude,
                        "longitude": each_sampah_pukal_data.longitude,
                        "parlimen": each_sampah_pukal_data.parlimen,
                        "taman": each_sampah_pukal_data.nama_taman,
                        "jalan": each_sampah_pukal_data.nama_jalan,
                        "kawasan": each_sampah_pukal_data.nama_kawasan,
                        "aktiviti": each_sampah_pukal_data.kekerapan_4,
                        "kekerapan": each_sampah_pukal_data.kekerapan,
                    })
        if aktiviti == 'CUCI LONGKANG':
            sisaDomesDataList = db.session.query(MapData).filter(MapData.parlimen==parlimen,MapData.nama_taman==nama_taman,MapData.nama_jalan==nama_jalan,MapData.nama_kawasan==nama_kawasan,MapData.lapisan_fitur==lapisan_fitur,MapData.kekerapan_5!='').all()         
            if sisaDomesDataList != []:
                for each_sampah_pukal_data in sisaDomesDataList:
                    jadualKutipan.append({
                        "latitude": each_sampah_pukal_data.latitude,
                        "longitude": each_sampah_pukal_data.longitude,
                        "parlimen": each_sampah_pukal_data.parlimen,
                        "taman": each_sampah_pukal_data.nama_taman,
                        "jalan": each_sampah_pukal_data.nama_jalan,
                        "kawasan": each_sampah_pukal_data.nama_kawasan,
                        "aktiviti": each_sampah_pukal_data.kekerapan_5,
                        "kekerapan": each_sampah_pukal_data.kekerapan,
                    })
        if aktiviti == 'POTONG RUMPUT':
            sisaDomesDataList = db.session.query(MapData).filter(MapData.parlimen==parlimen,MapData.nama_taman==nama_taman,MapData.nama_jalan==nama_jalan,MapData.nama_kawasan==nama_kawasan,MapData.lapisan_fitur==lapisan_fitur,MapData.kekerapan_6!='').all()         
            if sisaDomesDataList != []:
                for each_sampah_pukal_data in sisaDomesDataList:
                    jadualKutipan.append({
                        "latitude": each_sampah_pukal_data.latitude,
                        "longitude": each_sampah_pukal_data.longitude,
                        "parlimen": each_sampah_pukal_data.parlimen,
                        "taman": each_sampah_pukal_data.nama_taman,
                        "jalan": each_sampah_pukal_data.nama_jalan,
                        "kawasan": each_sampah_pukal_data.nama_kawasan,
                        "aktiviti": each_sampah_pukal_data.kekerapan_6,
                        "kekerapan": each_sampah_pukal_data.kekerapan,
                    })
        if aktiviti == 'SAMPAH KEBUN':
            sisaDomesDataList = db.session.query(MapData).filter(MapData.parlimen==parlimen,MapData.nama_taman==nama_taman,MapData.nama_jalan==nama_jalan,MapData.nama_kawasan==nama_kawasan,MapData.lapisan_fitur==lapisan_fitur,MapData.kekerapan_0!='').all()         
            if sisaDomesDataList != []:
                for each_sampah_pukal_data in sisaDomesDataList:
                    jadualKutipan.append({
                        "latitude": each_sampah_pukal_data.latitude,
                        "longitude": each_sampah_pukal_data.longitude,
                        "parlimen": each_sampah_pukal_data.parlimen,
                        "taman": each_sampah_pukal_data.nama_taman,
                        "jalan": each_sampah_pukal_data.nama_jalan,
                        "kawasan": each_sampah_pukal_data.nama_kawasan,
                        "aktiviti": each_sampah_pukal_data.kekerapan_0,
                        "kekerapan": each_sampah_pukal_data.kekerapan,
                    })
        logger.info("Jadual Kutipa fetched")
        return jadualKutipan
        
    except:
        logger.exception("Jadual Kutipa could not be fetched")
        response = dict(status= 'fail', message='Jadual Kutipa could could not be fetched')
        return response,400
""" ===============================<< getJadualPembersihan Ends >>=============================== """
""" ===============================<< randomSearch Starts >>=============================== """

def randomSearch(data):
    try:
        search_body = data.search_body
        if db.session.query(MapData).filter_by(nama_jalan=search_body).all() != []:
            namaJalanData = db.session.query(MapData).filter_by(nama_jalan=search_body).all()
            namaJalanCoordinateList = []
            for eachNamaJalan in namaJalanData:
                namaJalanCoordinateList.append({
                    "latitude" : eachNamaJalan.latitude,
                    "longitude" : eachNamaJalan.longitude,
                })
            logger.info("Coordinates for Nama Jalan fetched")
            return namaJalanCoordinateList
        if db.session.query(MapData).filter_by(nama_taman=search_body).all() != []:
            namaTamanData = db.session.query(MapData).filter_by(nama_taman=search_body).all()
            namaTamanCoordinateList = []
            for eachNamaTaman in namaTamanData:
                namaTamanCoordinateList.append({
                    "latitude" : eachNamaTaman.latitude,
                    "longitude" : eachNamaTaman.longitude,
                })
            logger.info("Coordinates for Nama Taman fetched")
            return namaTamanCoordinateList
        if db.session.query(MapData).filter_by(nama_kawasan=search_body).all() != []:
            namaKawasanData = db.session.query(MapData).filter_by(nama_kawasan=search_body).all()
            namaKawasanCoordinateList = []
            for eachNamaKawasan in namaKawasanData:
                namaKawasanCoordinateList.append({
                    "latitude" : eachNamaKawasan.latitude,
                    "longitude" : eachNamaKawasan.longitude,
                })
            logger.info("Coordinates for Nama Kawasan fetched")
            return namaKawasanCoordinateList
    except:
        logger.exception("Search Could Not Be Performed")
        response = dict(status= 'fail', message='Search Could Not Be Performed')
        return response,400
""" ===============================<< randomSearch Ends >>=============================== """

def getMTB(data):
    try:
        officer_name = data.officer_name
        id_mtb = db.session.query(MasterUser).filter_by(nama=officer_name).first().no_kad_pengenalan
        response = []
        logger.info("MTB id fetched successfully")
        response.append(id_mtb)
        return response
    except:
        logger.exception("MTB id could not be fetched")   
        response = dict(status= 'fail', message='MTB id could not be fetched')
        return response,
        

def getMTBOfficer(data):
    try:
        id_mtb = data.id_mtb
        offcier_name = db.session.query(MasterUser).filter_by(no_kad_pengenalan=id_mtb).first().nama
        response = []
        logger.info("MTB officer name fetched successfully")
        response.append(offcier_name)
        return response
    except:
        logger.exception("MTB officer name could not be fetched")   
        response = dict(status= 'fail', message='MTB officer name could not be fetched')
        return response,400