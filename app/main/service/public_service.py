""" Business logic for /auth API endpoints."""
from http import HTTPStatus
import os, json, sys, string, requests, secrets, random, re
from random import randint
from datetime import date, datetime, timedelta
import urllib.request
from flask import current_app, jsonify, session, request, redirect, send_file
from flask_restx import abort
from sqlalchemy import exc
from twilio.rest import Client
import pytz
import itertools
import smtplib
from sqlalchemy import desc
from app.main import db
from .decorators import token_required
from app.main.models.models import (
    MasterUser, PublicAnnouncement, PublicManual, PhotoGallery, PublicApplicationList, PublicApplicationDetails,
    DetailedMeeting, PublicSiteVisitInfo, NonComplianceForm, PublicRating, Coordinates, LogPengguna, OtpStore, BlacklistedToken)
from app.main.util.datetime_util import remaining_fromtimestamp, format_timespan_digits
from sqlalchemy.exc import *
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import setting
from werkzeug.utils import secure_filename
import logging
from applogger import logger

SMTP_MAIL = os.environ.get('SMTP_MAIL')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
UI_URL = os.environ.get('UI_URL')
PUBLIC_PHOTO_FOLDER = os.environ.get('PUBLIC_PHOTO_FOLDER')
PUBLIC_DOC_FOLDER = os.environ.get('PUBLIC_DOC_FOLDER')
PRIVATE_PHOTO_FOLDER = os.environ.get('PRIVATE_PHOTO_FOLDER')
PRIVATE_DOC_FOLDER = os.environ.get('PRIVATE_DOC_FOLDER')
tz = pytz.timezone('Asia/Kuala_Lumpur')

""" ===============================<< Get Announcement starts >>==============================="""

def getAnnouncement(language):
    try:
        filter_after = date.today() - timedelta(days = 90)
        public_announcement_list = []
        for announce in PublicAnnouncement.query.filter(PublicAnnouncement.date >= filter_after, PublicAnnouncement.language == language, PublicAnnouncement.active == 1).order_by(desc(PublicAnnouncement.date)).limit(3):
            public_announcement_list.append({
                'announcement_heading': announce.announcement_heading,
                'announcement_id': announce.announcement_id,
                'announcement': announce.announcement,
                'announcement_path': announce.announcement_path,
                'date': date.strftime(announce.date, "%Y-%m-%d"),
            })
        logger.info("Announcement Fetched")
        return jsonify(public_announcement_list)
    except:
        logger.exception("Announcement could not be Fetched")
        response_object = {
            'status': 'fail',
            'message': 'Announcement list could not be fetched.',
        }
        return response_object, 400
    
""" ===============================<< Get Announcement ends >>==============================="""
""" ===============================<< Create Announcement starts >>==============================="""
@token_required
def createAnnouncement(data):
    announcement_heading = data.announcement_heading
    announcement = data.announcement
    announcement_path = data.announcement_path
    language = data.language
    announcement_path = re.sub('[^a-zA-Z0-9.]', '', announcement_path)
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    if user.user_type == 'SuperAdmin':
        try:
            announcement_info = [{"announcement_heading": f"{announcement_heading}", "announcement": f"{announcement}",  "announcement_path": f"{announcement_path}", "language": f"{language}", "date": f"{today}", "inserted_by": f"{id_card_no}", "inserted_date": f"{today}"}]
            for i in announcement_info:
                db.session.add(PublicAnnouncement(**i))
                db.session.commit()
            logger.info("Announcement added successfully.")
            
            statement = "Pengumuman berjaya ditambahkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            response_object = {
                'status': 'success',
                'message': 'announcement_added',
            }
            return response_object, 201
        except:
            logger.exception("Announcement could not be added")
            response_object = {
                'status': 'fail',
                'message': 'announcement_not_added',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'not_authorized',
            }
        return response_object, 400
    
""" ===============================<< Create Announcement ends >>==============================="""
""" ===============================<< Update Announcement starts >>==============================="""
@token_required
def updateAnnouncement(data, announcement_id):
    announcement_heading = data.announcement_heading
    announcement = data.announcement
    announcement_path = data.announcement_path
    announcement_path = re.sub('[^a-zA-Z0-9.]', '', announcement_path)
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    
    if user.user_type == 'SuperAdmin' and PublicAnnouncement.find_by_announcement_id(announcement_id):
        try:
            public_announcement_obj = PublicAnnouncement.query.filter_by(announcement_id=announcement_id, active=1).first()
            public_announcement_obj.announcement_heading = announcement_heading
            public_announcement_obj.announcement = announcement
            public_announcement_obj.announcement_path = announcement_path
            public_announcement_obj.date = today
            public_announcement_obj.updated_date = today
            public_announcement_obj.updated_by = id_card_no
            db.session.commit()
            
            logger.info(f"Announcement : {announcement_id} updated successfully.")
            
            statement = f"Pengumuman : {announcement_id} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            
            response_object = {
                'status':'success',
                'message': 'announcement_updated',
            }
            return response_object, 201
        except:
            logger.exception("Announcement could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'announcement_not_updated',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'not_authorized',
            }
        return response_object, 400
    
""" ===============================<< Update Announcement ends >>==============================="""
""" ===============================<< Delete Announcement starts >>===============================  """
@token_required
def deleteAnnouncement(data):
    user = get_logged_in_user()
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    id_card_no = user.no_kad_pengenalan
    announcement_id_list = data.announcement_id.split(",")
    try:
        if user.user_type == 'SuperAdmin':
            for announcement_id in announcement_id_list:
                if PublicAnnouncement.query.filter_by(announcement_id=announcement_id).first():
                    PublicAnnouncement.query.filter_by(announcement_id=announcement_id).first().active = 0
                
            db.session.commit()

            statement = f"Pengumuman : {announcement_id_list} berjaya dipadamkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            logger.info(f"Announcement : {announcement_id_list} deleted successfully.")

            response_object = {
                "status": "success",
                "message": "announcement_deleted",
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 

    except:
        logger.exception("Announcement could not be deleted")
        response_object = {
            "status": "fail",
            "message": "announcement_not_deleted"
        }
        return response_object, 400
            
""" ===============================<< Delete Announcement ends >>===============================  """
""" ===============================<< Get Manual starts >>==============================="""

def getManual(language):
    try:
        public_mannual_list = []
        for manual in PublicManual.query.filter_by(active=1, language=language).order_by(desc(PublicManual.inserted_date)).limit(2):
            public_mannual_list.append({
                'manual_id': manual.mannual_id,
                'manual_heading': manual.manual_heading,
                'manual_body': manual.manual_body,
                'manual_path': manual.manual_path,
            })
        logger.info("Manual Fetched")
        return jsonify(public_mannual_list)
    except:
        logger.exception("Manual could not be Fetched")
        response_object = {
            'status': 'fail',
            'message': 'Manual list could not be fetched.',
        }
        return response_object, 400
    
""" ===============================<< Get Manual ends >>==============================="""
""" ===============================<< Create Manual starts >>==============================="""
@token_required
def createManual(data):
    manual_heading = data.manual_heading
    manual_body = data.manual_body
    manual_path = data.manual_path
    language = data.language
    manual_path = re.sub('[^a-zA-Z0-9.]', '', manual_path)
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    if user.user_type == 'SuperAdmin':
        try:
            manual_info = [{"manual_heading": f"{manual_heading}", "manual_body": f"{manual_body}", "manual_path": f"{manual_path}", "language":f"{language}", "inserted_by": f"{id_card_no}", "inserted_date": f"{now}"}]
            for i in manual_info:
                db.session.add(PublicManual(**i))
            db.session.commit()
            logger.info("Manual added successfully.")
            
            statement = "Manual berjaya ditambahkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'manual_added',
            }
            return response_object, 201
        except:
            logger.exception("Manual could not be added")
            response_object = {
                'status': 'fail',
                'message': 'manual_not_added'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'not_authorized'
            }
        return response_object, 400
    
""" ===============================<< Create Manual ends >>==============================="""
""" ===============================<< Update Manual starts >>==============================="""
@token_required
def updateManual(data, mannual_id):
    manual_heading = data.manual_heading
    manual_body = data.manual_body
    manual_path = data.manual_path
    manual_path = re.sub('[^a-zA-Z0-9.]', '', manual_path)
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    
    if user.user_type == 'SuperAdmin' and PublicManual.find_by_manual_id(mannual_id):
        try:
            public_manual_obj = PublicManual.query.filter_by(mannual_id=mannual_id, active=1).first()
            public_manual_obj.manual_heading = manual_heading
            public_manual_obj.manual_body = manual_body
            public_manual_obj.manual_path = manual_path
            public_manual_obj.date = today
            public_manual_obj.updated_date = today
            public_manual_obj.updated_by = id_card_no
            db.session.commit()
            
            logger.info(f"Manual : {mannual_id} updated successfully.")
            
            statement = f"Manual : {mannual_id} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            
            response_object = {
                'status':'success',
                'message': 'manual_updated',
            }
            return response_object, 201
        except:
            logger.exception("Manual could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'manual_not_updated',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'not_authorized',
            }
        return response_object, 400
    
""" ===============================<< Update Manual ends >>==============================="""
""" ===============================<< Delete Manual starts >>===============================  """
@token_required
def deleteManual(data):

    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    manual_id = data.manual_id

    try:
        if user.user_type == 'SuperAdmin':
            
            if PublicManual.query.filter_by(mannual_id=manual_id).first():
                data = PublicManual.query.filter_by(mannual_id=manual_id).first()
                db.session.delete(data)
            db.session.commit()
            
            statement = f"Manual {manual_id} berjaya dipadamkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            logger.info(f"Manual {manual_id} deleted successfully.")

            response_object = {
                "status": "success",
                "message": "manual_deleted"
            }
            return response_object, 200
        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            }            

    except:
        logger.exception("Manual could not be deleted")
        response_object = {
            "status": "fail",
            "message": "manual_not_deleted"
        }
        return response_object, 400
            
""" ===============================<< Delete Manual ends >>===============================  """
""" ===============================<< Get Gallery Photo starts >>==============================="""

def getGalleryPhoto():
    try:
        photo_gallery_list = []
        for photo in PhotoGallery.query.filter_by(active=1).order_by(desc(PhotoGallery.inserted_date)).all():
            photo_gallery_list.append({
                'photo_id': photo.photo_id,
                'photo_path': photo.photo_path,
            })
        logger.info("Gallery Photo Fetched")
        return jsonify(photo_gallery_list)
    except:
        logger.exception("Gallery Photo could not be Fetched")
        response_object = {
            'status': 'fail',
            'message': 'Photo Gallery List could not be fetched.',
        }
        return response_object, 400
    
    
""" ===============================<< Get Gallery Photo ends >>==============================="""
""" ===============================<< Add Gallery Photo starts >>==============================="""
@token_required
def addGalleryPhoto(data):
    photo_path = data.photo_path
    photo_path = re.sub('[^a-zA-Z0-9.]', '', photo_path)
    photo_path = '/jkas_resourses/free/images/'+photo_path
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    if user.user_type == 'SuperAdmin':
        try:
            photo_info = [{"photo_path": f"{photo_path}", "inserted_by": f"{id_card_no}", "inserted_date": f"{now}"}]
            for i in photo_info:
                db.session.add(PhotoGallery(**i))
            db.session.commit()
            logger.info("Gallery Photo added successfully.")
            
            statement = "Foto Galeri berjaya ditambahkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'galleryphoto_added',
            }
            return response_object, 201
        except:
            logger.exception("Gallery Photo could not be added")
            response_object = {
                'status': 'fail',
                'message': 'galleryphoto_not_added'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'not_authorized'
            }
        return response_object, 400
    
""" ===============================<< Add Gallery Photo ends >>==============================="""
""" ===============================<< Delete Gallery Photo starts >>===============================  """
@token_required
def deleteGalleryPhoto(data):

    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    photo_id = data.photo_id

    try:
        if user.user_type == 'SuperAdmin':
            
            if PhotoGallery.query.filter_by(photo_id=photo_id).first():
                data = PhotoGallery.query.filter_by(photo_id=photo_id).first()
                db.session.delete(data)
            db.session.commit()
            
            statement = f"Foto Galeri {photo_id} berjaya dipadamkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            logger.info(f"Gallery Photo {photo_id} deleted successfully.")

            response_object = {
                "status": "success",
                "message": "galleryphoto_deleted"
            }
            return response_object, 200
        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            }            

    except:
        logger.exception("Gallery Photo could not be deleted")
        response_object = {
            "status": "fail",
            "message": "galleryphoto_not_deleted"
        }
        return response_object, 400
            
""" ===============================<< Delete Gallery Photo ends >>===============================  """
""" ===============================<< Registration of new user starts >>==============================="""

def triggerRegistration(data):
    name = data.name
    id_card_no = data.id_card_no.upper()
    email = data.email
    password = data.password
    
    if MasterUser.find_by_email(email):
        abort(HTTPStatus.CONFLICT,"email_exists", status="fail")
    if MasterUser.find_by_id_card(id_card_no):
            abort(HTTPStatus.CONFLICT,"user_exists", status="fail")
    if MasterUser.find_by_nama(name):
            abort(HTTPStatus.CONFLICT,"user_exists", status="fail")
    return register(name, id_card_no, email, password)


def register(name, id_card_no, email, password):

    randotp = randint(100000, 999999)
    session['randotp'] = randotp
    if OtpStore.find_by_id_card_no(id_card_no):
        OtpStore.query.filter(OtpStore.no_kad_pengenalan == id_card_no).delete()
        db.session.commit()
    otp_list = [{"no_kad_pengenalan": f"{id_card_no}", "otp": f"{randotp}", "name": f"{name}",  "email": f"{email}",  "psswd": f"{password}"}]
    for i in otp_list:
        db.session.add(OtpStore(**i))
    db.session.commit()
    TO_EMAIL = email
    MAIL_CONTENT = f'''
    Salam Sejahtera,

    Anda telah membuat pendaftaran akses masuk ke dalam sistem iwastekl@dbkl.gov.my. Maklumat anda adalah seperti berikut :-
    ID Pengguna: {id_card_no}
    Nama: {name}
    Kod OTP : {randotp}

    Sekiranya pihak anda tidak membuat sebarang permohonan, sila abaikan email ini dan sekiranya mempunyai sebarang pertanyaan lanjut, Sila hubungi pihak Jabatan Kesihatan dan Alam Sekitar, Dewan Bandaraya Kuala Lumpur (DBKL) di talian seperti di bawah:
    Tel : +603-03-2027 5300
    Email: jkas@dbkl.gov.my
    Alamat: KM 4, Jalan Cheras, 56100 Kuala Lumpur.

    Terima Kasih.
    -Pentadbir Sistem-
    '''
    try:
        response = requests.post("https://jkashelper.azurewebsites.net/api/jkasemailsender", verify=False, json={
            "from": FROM_EMAIL,
            "to": TO_EMAIL,
            "subject": "Emel OTP",
            "content": MAIL_CONTENT
        })

        if response.status_code != 200:
            logger.exception("JKAS Helper returns " + str(response.status_code))
            raise Exception("Failed to send mail")
        logger.info("Mail Sent")
        response_object = {
            "status": "success",
            "message": "otp_sent"
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
    id_card_no = data.id_card_no.upper()
    user_type = 'public'
    role = 'Orang Awam'
    lock_time = datetime(9999, 12, 31, 12, 59, 59)
    try:
        user = OtpStore.find_by_id_card_no(id_card_no)
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
            updated_user = MasterUser(nama=name, nama_pengguna=id_card_no, no_kad_pengenalan=id_card_no, alamat_emel=email, kata_laluan=password, lock_time = lock_time, user_type=user_type, role=role)
            db.session.add(updated_user)
            OtpStore.query.filter(OtpStore.no_kad_pengenalan == id_card_no).delete()
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
    id_card_no = data.id_card_no.upper()
    password = data.password
    lock_flag = data.lock_flag
    now = datetime.now()
    user = MasterUser.find_by_id_card(id_card_no)
    if user:
        print(user.lock_time)
        diff = now - user.lock_time
        lock_login = False
        print(diff.days)
        print(diff.seconds)
        if int(diff.days) >= 0 and int(diff.seconds) < 180:
            print("positive")
            lock_login = True
            lock_time = 180 - diff.seconds

    logging.info("By pass login...")
    if True:
        access_token = user.encode_access_token()
        logger.info("Logged In successfully.")
        nama = user.nama
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type
        role = user.role
        
        statement = "Log masuk berjaya."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        
        return _create_auth_successful_response(
            token=access_token.decode(),
            status_code=HTTPStatus.OK,
            message="login_success",
            user=nama,
        )       

    if not user:
        logger.info("Wrong ID Card No")
        abort(HTTPStatus.UNAUTHORIZED,"invalid_cred", status="fail")
    elif not MasterUser.find_by_kata_laluan(id_card_no, password) and lock_flag == False:
        if lock_login == True:
            abort(HTTPStatus.UNAUTHORIZED,f"account_locked_{lock_time}", status="fail")
        logger.info("Wrong Password")
        abort(HTTPStatus.UNAUTHORIZED,"invalid_cred", status="fail")
        
    elif not MasterUser.find_by_kata_laluan(id_card_no, password) and lock_flag == True:
        if lock_login == True:
            abort(HTTPStatus.UNAUTHORIZED,f"account_locked_{lock_time}", status="fail")
        user.lock_time = now
        db.session.commit()
        logger.info("Wrong Password")
        abort(HTTPStatus.UNAUTHORIZED,"invalid_cred", status="fail")
        
    elif user.user_type == 'admin' or user.user_type == 'public' or user.user_type=='SuperAdmin' and user.active==1:
        if lock_login == True:
            abort(HTTPStatus.UNAUTHORIZED,f"account_locked_{lock_time}", status="fail")
        else:
            access_token = user.encode_access_token()
            logger.info("Logged In successfully.")
            nama = user.nama
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            user_type = user.user_type
            role = user.role
            
            statement = "Log masuk berjaya."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            
            return _create_auth_successful_response(
                token=access_token.decode(),
                status_code=HTTPStatus.OK,
                message="login_success",
                user=nama,
            )       
    else:
        response_object = {
                'status': 'fail',
                'message': 'invalid_cred',
        }
        return response_object, 403


def _create_auth_successful_response(token, status_code, message, user):
    response = jsonify(
        user = user,
        status="success",
        message=message,
        access_token=token,
        token_type="bearer",
        expires_in=_get_token_expire_time(),
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
        password = user.kata_laluan
        log_list = []
        for logs in LogPengguna.query.filter_by(id_pengguna=id_card_no).order_by(desc(LogPengguna.tarikh)):
            log_list.append({
                'id_card_no': id_card_no,
                'username': username,
                'name': name,
                'role': role,
                'email': email,
                'password': password,
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
    response_dict = dict(status="success", message="Logged out successfully.")
    return response_dict, HTTPStatus.OK

""" ===============================<< User logout process ends >>=============================== """
""" ===============================<< Forgot password starts >>=============================== """

def forgotPassword(data):
    id_card_no = data.id_card_no.upper()
    if MasterUser.find_by_id_card(id_card_no):
        reset_password_token = secrets.token_hex(20)
        user = MasterUser.find_by_id_card(id_card_no)
        user.reset_password_token = reset_password_token
        db.session.commit()
        email = user.alamat_emel
        lang = data.lang
        return make_forgot_mail(id_card_no, email, lang, reset_password_token)
    
    elif MasterUser.find_by_email(id_card_no):
        reset_password_token = secrets.token_hex(20)
        user = MasterUser.find_by_email(id_card_no)
        user.reset_password_token = reset_password_token
        db.session.commit()
        email = id_card_no
        lang = data.lang
        return make_forgot_mail(id_card_no, email, lang, reset_password_token)
    
    else:
        logger.info("Email or ID Card Not  Present")
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
    {UI_URL}/{lang}/public/resetpassword?token={reset_password_token}
    

    Jabatan Kesihatan dan Alam Sekitar
    '''
    message.attach(MIMEText(MAIL_CONTENT, 'plain'))
    try:
        mail_session = smtplib.SMTP('smtp.gmail.com', 587)
        mail_session.starttls()
        mail_session.login(SMTP_MAIL, SMTP_PASSWORD)
        text = message.as_string()
        mail_session.sendmail(FROM_EMAIL, TO_EMAIL, text)
        mail_session.quit()
        logger.info("Mail Sent with reset password token")
        response_object = {
            'status': 'success',
            'message': 'reset_pwd_mail_sent'
            }
        return response_object, 200
    except:
        logger.exception("could not be sent mail")
        response_object = {
            'status': 'fail',
            'message': 'Could not sent reset pasword link'
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
        logger.exception('No user not found with the reset password token')
        response_object = {
            'status': 'fail',
            'message': 'No user not found with the reset password token !'
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
""" ===============================<< List Application starts >>===============================  """

@token_required
def viewApplicationList():
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    if user.user_type == 'public':
        try:
            application_list = []
            for app in PublicApplicationList.query.filter_by(no_kad_pengenalan=id_card_no,active=1).order_by(desc(PublicApplicationList.inserted_date)):
                status_lawatan_tapak = db.session.query(PublicSiteVisitInfo).filter_by(no_siri_permohonan=app.no_siri_permohonan).first().keputusan_lawatan_tapak
                application_list.append({
                    'application_id': app.application_id,
                    'no_siri_permohonan': app.no_siri_permohonan,
                    'tarikh_permohonan': date.strftime(app.tarikh_permohonan, "%Y-%m-%d"),
                    'dokumen_senarai': app.dokumen_senarai,
                    'status_semakan_dokumen': app.status_semakan_dokumen,
                    'mesyuarat_permohanan_serahan_kawasan': app.mesyuarat_permohanan_serahan_kawasan,
                    'maklumat_lawatan_tapak_id': app.maklumat_lawatan_tapak_id,
                    'status_Lawatan_Tapak': status_lawatan_tapak,
                    'surat_penyerahan_kawasan': app.surat_penyerahan_kawasan,
                })
            logger.info("Application list fetched.")
            return jsonify(application_list)
        except:
            logger.exception('Application list could not be fetched.')
            response_object = {
                'status': 'fail',
                'message': 'Application list could not be fetched.',
            }
            return response_object, 400
    if user.user_type == 'SuperAdmin':
        try:
            application_list = []
            for app in db.session.query(PublicApplicationList).order_by(desc(PublicApplicationList.inserted_date)):
                status_lawatan_tapak = db.session.query(PublicSiteVisitInfo).filter_by(no_siri_permohonan=app.no_siri_permohonan).first().keputusan_lawatan_tapak
                application_list.append({
                    'application_id': app.application_id,
                    'no_siri_permohonan': app.no_siri_permohonan,
                    'tarikh_permohonan': date.strftime(app.tarikh_permohonan,"%Y-%m-%d"),
                    'dokumen_senarai': app.dokumen_senarai,
                    'status_semakan_dokumen': app.status_semakan_dokumen,
                    'mesyuarat_permohanan_serahan_kawasan': app.mesyuarat_permohanan_serahan_kawasan,
                    'maklumat_lawatan_tapak_id': app.maklumat_lawatan_tapak_id,
                    'status_Lawatan_Tapak': status_lawatan_tapak,
                    'surat_penyerahan_kawasan': app.surat_penyerahan_kawasan,
                    'active': app.active,
                })
            logger.info("Application list fetched.")
            return jsonify(application_list)
        except:
            logger.exception('Application list could not be fetched.')
            response_object = {
                'status': 'fail',
                'message': 'Application list could not be fetched.',
            }
            return response_object, 400

""" ===============================<< view Application List ends >>===============================  """
""" ===============================<< update Application List ends >>===============================  """
@token_required
def updateApplicationList(no_siri_permohonan, data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type 
    role = user.role
    surat_penyerahan_kawasan = data.surat_penyerahan_kawasan
    surat_penyerahan_kawasan = re.sub('[^a-zA-Z0-9.]', '', surat_penyerahan_kawasan)
                                      
    if user.user_type == 'SuperAdmin' or user.user_type == 'public':
        try:
            app_info = db.session.query(PublicApplicationList).filter_by(no_siri_permohonan=no_siri_permohonan).first()
            app_info.surat_penyerahan_kawasan = surat_penyerahan_kawasan
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
""" ===============================<< update Application List ends >>===============================  """
""" ===============================<< Delete Application List starts >>===============================  """

@token_required
def deleteApplicationList(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    app_id_list = data.app_id_list.split(",")
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type  
    role = user.role
    try:
        for i in app_id_list:
            if PublicApplicationList.query.filter_by(application_id=i).first():
                PublicApplicationList.query.filter_by(application_id=i).first().active = 0
                
        db.session.commit()
        
        statement = f"Senarai aplikasi : {app_id_list} berjaya dipadamkan."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        
        logger.info(f"Application list : {app_id_list} deleted successfully.")
        response_object = {
            "status": "success",
            "message": f"Application list : {app_id_list} deleted successfully."
        }
        return response_object, 200
    except:
        logger.exception("Application list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Application list could not be Deleted"
        }
        return response_object, 400
            
""" ===============================<< Delete Application List ends >>===============================  """
""" ===============================<< Submit Application starts >>===============================  """

@token_required
def submitApplication(data):
    kutipan_sampah = data.kutipan_sampah
    sapuan_jalan = data.sapuan_jalan
    cucian_longkang = data.cucian_longkang
    pemotongan_rumput = data.pemotongan_rumput
    dinyatakan_nama_bangunan = data.dinyatakan_nama_bangunan
    strata_title = data.strata_title
    hak_milik_kekal = data.hak_milik_kekal
    nama_jalan = data.nama_jalan
    panjang_jalan_mengikut_nama_jalan = data.panjang_jalan_mengikut_nama_jalan
    panjang_longkang = data.panjang_longkang
    luas_kawasan_berumput = data.luas_kawasan_berumput
    luas_kawasan_TPKK = data.luas_kawasan_TPKK
    parkir_area = data.parkir_area
    
    surat_permohonan_perkhidmatan_pembersihan_dokumen_temp = data.surat_permohonan_perkhidmatan_pembersihan_dokumen
    if surat_permohonan_perkhidmatan_pembersihan_dokumen_temp:
        surat_permohonan_perkhidmatan_pembersihan_dokumen_list = surat_permohonan_perkhidmatan_pembersihan_dokumen_temp.split(",")
        surat_permohonan_perkhidmatan_pembersihan_dokumen_temp_list = []
        for i in surat_permohonan_perkhidmatan_pembersihan_dokumen_list:
            surat_permohonan_perkhidmatan_pembersihan_dokumen_temp = re.sub('[^a-zA-Z0-9.]', '', i)
            surat_permohonan_perkhidmatan_pembersihan_dokumen_temp = surat_permohonan_perkhidmatan_pembersihan_dokumen_temp
            surat_permohonan_perkhidmatan_pembersihan_dokumen_temp_list.append(surat_permohonan_perkhidmatan_pembersihan_dokumen_temp)
        surat_permohonan_perkhidmatan_pembersihan_dokumen_temp = ""
        for i in surat_permohonan_perkhidmatan_pembersihan_dokumen_temp_list:
            surat_permohonan_perkhidmatan_pembersihan_dokumen_temp += i+','

    surat_salinan_CF_dokumen_temp = data.surat_salinan_CF_dokumen
    if surat_salinan_CF_dokumen_temp:
        surat_salinan_CF_dokumen_list = surat_salinan_CF_dokumen_temp.split(",")
        surat_salinan_CF_dokumen_temp_list = []
        for i in surat_salinan_CF_dokumen_list:
            surat_salinan_CF_dokumen_temp = re.sub('[^a-zA-Z0-9.]', '', i)
            surat_salinan_CF_dokumen_temp = surat_salinan_CF_dokumen_temp
            surat_salinan_CF_dokumen_temp_list.append(surat_salinan_CF_dokumen_temp)
        surat_salinan_CF_dokumen_temp = ""
        for i in surat_salinan_CF_dokumen_temp_list:
            surat_salinan_CF_dokumen_temp += i+','
    
    salinan_status_pembanginan_dokumen_temp = data.salinan_status_pembanginan_dokumen
    if salinan_status_pembanginan_dokumen_temp:
        salinan_status_pembanginan_dokumen_list = salinan_status_pembanginan_dokumen_temp.split(",")
        salinan_status_pembanginan_dokumen_temp_list = []
        for i in salinan_status_pembanginan_dokumen_list:
            salinan_status_pembanginan_dokumen_temp = re.sub('[^a-zA-Z0-9.]', '', i)
            salinan_status_pembanginan_dokumen_temp = salinan_status_pembanginan_dokumen_temp
            salinan_status_pembanginan_dokumen_temp_list.append(salinan_status_pembanginan_dokumen_temp)
        salinan_status_pembanginan_dokumen_temp = ""
        for i in salinan_status_pembanginan_dokumen_temp_list:
            salinan_status_pembanginan_dokumen_temp += i+','
            
    bagi_status_pembangunan_dokumen_temp = data.bagi_status_pembangunan_dokumen
    if bagi_status_pembangunan_dokumen_temp:
        bagi_status_pembangunan_dokumen_list = bagi_status_pembangunan_dokumen_temp.split(",")
        bagi_status_pembangunan_dokumen_temp_list = []
        for i in bagi_status_pembangunan_dokumen_list:
            bagi_status_pembangunan_dokumen_temp = re.sub('[^a-zA-Z0-9.]', '', i)
            bagi_status_pembangunan_dokumen_temp = bagi_status_pembangunan_dokumen_temp
            bagi_status_pembangunan_dokumen_temp_list.append(bagi_status_pembangunan_dokumen_temp)
        bagi_status_pembangunan_dokumen_temp = ""
        for i in bagi_status_pembangunan_dokumen_temp_list:
            bagi_status_pembangunan_dokumen_temp += i+','

    dinyatakan_jenis_sistem_temp = data.dinyatakan_jenis_sistem
    if dinyatakan_jenis_sistem_temp:
        dinyatakan_jenis_sistem_list = dinyatakan_jenis_sistem_temp.split(",")
        dinyatakan_jenis_sistem_temp_list = []
        for i in dinyatakan_jenis_sistem_list:
            dinyatakan_jenis_sistem_temp = re.sub('[^a-zA-Z0-9.]', '', i)
            dinyatakan_jenis_sistem_temp = dinyatakan_jenis_sistem_temp
            dinyatakan_jenis_sistem_temp_list.append(dinyatakan_jenis_sistem_temp)
        dinyatakan_jenis_sistem_temp = ""
        for i in dinyatakan_jenis_sistem_temp_list:
            dinyatakan_jenis_sistem_temp += i+','
    confirm = data.confirm
       
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type  
        role = user.role
        app_srl_no = 'PSPPA'+''.join(random.choices(string.digits, k=4)) + \
                                     ''.join(random.choices(
                                         string.ascii_uppercase, k=2))
        if PublicApplicationDetails.find_by_app_srl_no(app_srl_no):
            return submitApplication()
        new_application_details = PublicApplicationDetails(kutipan_sampah=kutipan_sampah, sapuan_jalan=sapuan_jalan, cucian_longkang=cucian_longkang,
                                                pemotongan_rumput=pemotongan_rumput, dinyatakan_nama_bangunan=dinyatakan_nama_bangunan,
                                                strata_title=strata_title, hak_milik_kekal=hak_milik_kekal, nama_jalan=nama_jalan,
                                                panjang_jalan_mengikut_nama_jalan=panjang_jalan_mengikut_nama_jalan, panjang_longkang=panjang_longkang,
                                                luas_kawasan_berumput=luas_kawasan_berumput, luas_kawasan_TPKK=luas_kawasan_TPKK, parkir_area=parkir_area,
                                                surat_permohonan_perkhidmatan_pembersihan_dokumen=surat_permohonan_perkhidmatan_pembersihan_dokumen_temp[:-1],
                                                surat_salinan_CF_dokumen=surat_salinan_CF_dokumen_temp[:-1], salinan_status_pembanginan_dokumen=salinan_status_pembanginan_dokumen_temp[:-1],
                                                bagi_status_pembangunan_dokumen=bagi_status_pembangunan_dokumen_temp[:-1],
                                                no_siri_permohonan=app_srl_no, no_kad_pengenalan=id_card_no,
                                                inserted_by=id_card_no,dinyatakan_jenis_sistem=dinyatakan_jenis_sistem_temp[:-1],confirm=confirm,inserted_date=today, active=1)

        db.session.add(new_application_details)
        db.session.commit()
        new_application_list = PublicApplicationList(no_kad_pengenalan=id_card_no, no_siri_permohonan=app_srl_no, maklumat_lawatan_tapak_id=app_srl_no, dokumen_senarai=app_srl_no, status_semakan_dokumen=False, mesyuarat_permohanan_serahan_kawasan='', text='',
                                                     inserted_by=id_card_no, inserted_date=now, active=1)
        db.session.add(new_application_list)
        db.session.commit()
        
        new_detailed_meeting = DetailedMeeting(no_siri_permohonan=app_srl_no, tarikh_mesyuarat='',masa_mesyuarat='',tempat_mesyuarat='', inserted_by=id_card_no, inserted_date=now, active=1)
        db.session.add(new_detailed_meeting)
        db.session.commit()
        
        new_site_visit_info = PublicSiteVisitInfo(no_siri_permohonan=app_srl_no, tarikh=today,lawatan_tapak='',tarikh_lawatan_tapak='', keputusan_lawatan_tapak='',makalumat_ketidakpatuhan='',maklum_balas_ketidakpatuhan='',
                                                inserted_by=id_card_no, inserted_date=now, active=1)
        db.session.add(new_site_visit_info)
        db.session.commit()

        statement = f"Permohonan {app_srl_no} berjaya dihantar."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        
        logger.info(f"Application {app_srl_no} submitted successfully.")
        response_object = {
            'status': 'success',
            'message': 'application_added',
            'app_srl_no': f'{app_srl_no}'
            }
        return response_object, 201
    except:
        logger.exception("Application not added")
        response_object = {
            'status': 'fail',
            'message': 'application_not_added',
        }
        return response_object, 400


""" ===============================<< Submit Application ends >>===============================  """
""" ===============================<< view Application Details starts >>===============================  """

@token_required
def viewApplicationDetails():
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    if user.user_type == 'public':
        try:
            application_details = []
            for app in PublicApplicationDetails.query.filter_by(no_kad_pengenalan=id_card_no, active=1):
                application_details.append({
                    'no_kad_pengenalan': app.no_kad_pengenalan,
                    'kutipan_sampah': app.kutipan_sampah,
                    'sapuan_jalan': app.sapuan_jalan,
                    'cucian_longkang': app.cucian_longkang,
                    'pemotongan_rumput': app.pemotongan_rumput,
                    'dinyatakan_nama_bangunan': app.dinyatakan_nama_bangunan,
                    'strata_title': app.strata_title,
                    'hak_milik_kekal': app.hak_milik_kekal,
                    'nama_jalan': app.nama_jalan,
                    'panjang_jalan_mengikut_nama_jalan': app.panjang_jalan_mengikut_nama_jalan,
                    'panjang_longkang': app.panjang_longkang,
                    'luas_kawasan_berumput': app.luas_kawasan_berumput,
                    'luas_kawasan_TPKK': app.luas_kawasan_TPKK,
                    'parkir_area': app.parkir_area,
                    'surat_permohonan_perkhidmatan_pembersihan_dokumen': app.surat_permohonan_perkhidmatan_pembersihan_dokumen,
                    'surat_salinan_CF_dokumen': app.surat_salinan_CF_dokumen,
                    'salinan_status_pembanginan_dokumen': app.salinan_status_pembanginan_dokumen,
                    'bagi_status_pembangunan_dokumen': app.bagi_status_pembangunan_dokumen,
                    'surat_permohonan_perkhidmatan_pembersihan_status': app.surat_permohonan_perkhidmatan_pembersihan_status,
                    'surat_salinan_CF_status': app.surat_salinan_CF_status,
                    'salinan_status_pembanginan_status': app.salinan_status_pembanginan_status,
                    'bagi_status_pembangunan_status': app.bagi_status_pembangunan_status,
                    'surat_permohonan_perkhidmatan_pembersihan_catatan': app.surat_permohonan_perkhidmatan_pembersihan_catatan,
                    'surat_salinan_CF_catatan': app.surat_salinan_CF_catatan,
                    'salinan_status_pembanginan_catatan': app.salinan_status_pembanginan_catatan,
                    'bagi_status_pembangunan_catatan': app.bagi_status_pembangunan_catatan,
                    'status_dokumen_keseluruhan': app.status_dokumen_keseluruhan,
                    'no_siri_permohonan': app.no_siri_permohonan,
                })
            logger.info("Application deatils fetched.")
            return application_details
        except:
            logger.exception('Application deatils could not be fetched.')
            response_object = {
                'status': 'fail',
                'message': 'Application list could not be fetched.',
            }
            return response_object, 400
    if user.user_type == 'SuperAdmin':
        try:
            application_details = []
            for app in db.session.query(PublicApplicationDetails):
                application_details.append({
                    'no_kad_pengenalan': app.no_kad_pengenalan,
                    'kutipan_sampah': app.kutipan_sampah,
                    'sapuan_jalan': app.sapuan_jalan,
                    'cucian_longkang': app.cucian_longkang,
                    'pemotongan_rumput': app.pemotongan_rumput,
                    'dinyatakan_nama_bangunan': app.dinyatakan_nama_bangunan,
                    'strata_title': app.strata_title,
                    'hak_milik_kekal': app.hak_milik_kekal,
                    'nama_jalan': app.nama_jalan,
                    'panjang_jalan_mengikut_nama_jalan': app.panjang_jalan_mengikut_nama_jalan,
                    'panjang_longkang': app.panjang_longkang,
                    'luas_kawasan_berumput': app.luas_kawasan_berumput,
                    'luas_kawasan_TPKK': app.luas_kawasan_TPKK,
                    'parkir_area': app.parkir_area,
                    'surat_permohonan_perkhidmatan_pembersihan_dokumen': app.surat_permohonan_perkhidmatan_pembersihan_dokumen,
                    'surat_salinan_CF_dokumen': app.surat_salinan_CF_dokumen,
                    'salinan_status_pembanginan_dokumen': app.salinan_status_pembanginan_dokumen,
                    'bagi_status_pembangunan_dokumen': app.bagi_status_pembangunan_dokumen,
                    'surat_permohonan_perkhidmatan_pembersihan_status': app.surat_permohonan_perkhidmatan_pembersihan_status,
                    'surat_salinan_CF_status': app.surat_salinan_CF_status,
                    'salinan_status_pembanginan_status': app.salinan_status_pembanginan_status,
                    'bagi_status_pembangunan_status': app.bagi_status_pembangunan_status,
                    'surat_permohonan_perkhidmatan_pembersihan_catatan': app.surat_permohonan_perkhidmatan_pembersihan_catatan,
                    'surat_salinan_CF_catatan': app.surat_salinan_CF_catatan,
                    'salinan_status_pembanginan_catatan': app.salinan_status_pembanginan_catatan,
                    'bagi_status_pembangunan_catatan': app.bagi_status_pembangunan_catatan,
                    'status_dokumen_keseluruhan': app.status_dokumen_keseluruhan,
                    'no_siri_permohonan': app.no_siri_permohonan,
                })
            logger.info("Application deatils fetched.")
            return application_details
        except:
            logger.exception('Application deatils could not be fetched.')
            response_object = {
                'status': 'fail',
                'message': 'Application list could not be fetched.',
            }
            return response_object, 400


""" ===============================<< view Application Details ends >>===============================  """

""" ===============================<< Site Visit Information starts >>===============================  """

@token_required
def sitevisitInformation(app_srl_no):
    user = get_logged_in_user()
    if user.role == 'Orang Awam':
    
        try:
            public_site_visit_info = PublicSiteVisitInfo.query.filter_by(no_siri_permohonan=app_srl_no, active=1).all()
        except:
            logger.exception('No Site Visit Information Found with Serial No')
            response_object = {
                    'status': 'fail',
                    'message': f'No Site Visit Information Found with Serial No. {app_srl_no}',
                }
            return response_object, 404
        if public_site_visit_info:
            try:
                site_info_list = []
                for site in PublicSiteVisitInfo.query.filter_by(no_siri_permohonan=app_srl_no, active=1):
                    site_info_list.append({
                        'site_id': site.site_id,
                        'no_siri_permohonan': site.no_siri_permohonan,
                        'tarikh': date.strftime(site.tarikh, "%Y-%m-%d"),
                        'lawatan_tapak': site.lawatan_tapak,
                        'tarikh_lawatan_tapak': date.strftime(site.tarikh_lawatan_tapak, "%Y-%m-%d"),
                        'keputusan_lawatan_tapak': site.keputusan_lawatan_tapak,
                        'makalumat_ketidakpatuhan': site.makalumat_ketidakpatuhan,
                        'maklum_balas_ketidakpatuhan': site.maklum_balas_ketidakpatuhan,
                    })
                logger.info("Site Visit Info Fetched")
                return jsonify(site_info_list)
            except:
                
                logger.exception("Site Visit Info could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': f'No Site Visit Information Found with Serial No. {app_srl_no}',
                }
                return response_object, 404
        else:
            response_object = {
                    'status': 'fail',
                    'message': f'No Site Visit Information Found with Serial No. {app_srl_no}',
                }
            return response_object, 404
    if user.role == 'Superadmin' or user.role == 'Pentadbir':
        try:
            public_site_visit_info = PublicSiteVisitInfo.query.filter_by(no_siri_permohonan=app_srl_no, active=1).all()
        except:
            logger.exception('No Site Visit Information Found with Serial No')
            response_object = {
                    'status': 'fail',
                    'message': f'No Site Visit Information Found with Serial No. {app_srl_no}',
                }
            return response_object, 404
        if public_site_visit_info:
            try:
                site_info_list = []
                for site in PublicSiteVisitInfo.query.filter_by(no_siri_permohonan=app_srl_no, active=1):
                    site_info_list.append({
                        'site_id': site.site_id,
                        'no_siri_permohonan': site.no_siri_permohonan,
                        'tarikh': date.strftime(site.tarikh, "%Y-%m-%d"),
                        'lawatan_tapak': site.lawatan_tapak,
                        'tarikh_lawatan_tapak': date.strftime(site.tarikh_lawatan_tapak, "%Y-%m-%d"),
                        'keputusan_lawatan_tapak': site.keputusan_lawatan_tapak,
                        'makalumat_ketidakpatuhan': site.makalumat_ketidakpatuhan,
                        'maklum_balas_ketidakpatuhan': site.maklum_balas_ketidakpatuhan,
                        'active': site.active,
                    })
                logger.info("Site Visit Info Fetched")
                return jsonify(site_info_list)
            except:
                
                logger.exception("Site Visit Info could not be fetched")
                response_object = {
                    'status': 'fail',
                    'message': f'No Site Visit Information Found with Serial No. {app_srl_no}',
                }
                return response_object, 404
        else:
            response_object = {
                    'status': 'fail',
                    'message': f'No Site Visit Information Found with Serial No. {app_srl_no}',
                }
            return response_object, 404


""" ===============================<< Site Visit Information ends >>===============================  """
""" ===============================<< Update Site Visit Information starts >>===============================  """

@token_required
def updateSiteVisitInformation(site_id,data):

    try:
        site_visit = db.session.query(PublicSiteVisitInfo).filter_by(site_id=site_id, active=1).one()
    except:
        logger.exception('Site Visit Info not found with site_id')
        response_object = {
                'status': 'fail',
                'message': 'Site Visit Info not found with site_id',
            }
        return response_object, 404
    if site_visit:
        try:
            user = get_logged_in_user()
            id_card_no = user.no_kad_pengenalan
            today = date.today()
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            user_type = user.user_type
            role = user.role
            site_visit.tarikh = data.tarikh
            site_visit.lawatan_tapak = data.lawatan_tapak
            site_visit.keputusan_lawatan_tapak = data.keputusan_lawatan_tapak
            maklum_balas_ketidakpatuhan = data.maklum_balas_ketidakpatuhan
            makalumat_ketidakpatuhan = data.makalumat_ketidakpatuhan
            if maklum_balas_ketidakpatuhan:
                maklum_balas_ketidakpatuhan = re.sub('[^a-zA-Z0-9.]', '', maklum_balas_ketidakpatuhan)
            if makalumat_ketidakpatuhan:
                makalumat_ketidakpatuhan = re.sub('[^a-zA-Z0-9.]', '', makalumat_ketidakpatuhan)
            site_visit.maklum_balas_ketidakpatuhan = maklum_balas_ketidakpatuhan
            site_visit.makalumat_ketidakpatuhan = makalumat_ketidakpatuhan
            site_visit.updated_by = id_card_no
            site_visit.updated_date = today
            db.session.commit()
            
            statement = f"Item maklumat lawatan laman web {site_id} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            logger.info(f"Site visit information item {site_id} updated successfully.")
            response_object = {
                'status': 'success',
                'message': 'site_visit_updated',
            }
            return response_object, 201
        except:
            logger.exception("Site Visit Info could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'site_visit_not_updated',
            }
            return response_object, 404
    else:
        response_object = {
                'status': 'fail',
                'message': 'site_visit_not_updated',
            }
        return response_object, 404
   
""" ===============================<< Update Site Visit Information ends >>===============================  """
""" ===============================<< Delete Site Visit Information starts >>===============================  """

@token_required
def deleteSiteVisitInformation(data):
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    today = date.today()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    user_type = user.user_type
    role = user.role
    site_visit_id_list = data.site_visit_id_list.split(",")
    try:
        if user.user_type == 'SuperAdmin':
            for i in site_visit_id_list:
                if PublicSiteVisitInfo.query.filter_by(site_id=i).first():
                    PublicSiteVisitInfo.query.filter_by(site_id=i).first().active = 0
                    
            db.session.commit()
            
            statement = f"Maklumat lawatan laman web : {site_visit_id_list} berjaya dipadamkan."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            logger.info(f"Site visit information : {site_visit_id_list} deleted successfully.")
            
            response_object = {
                "status": "success",
                "message": f"site_visit_deleted"
            }
            return response_object, 200
        else:
            response_object = {
                "status": "fail",
                "message": "not_authorized"
            } 
    except:
        logger.exception("Site Visit Information list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "site_visit_not_deleted"
        }
        return response_object, 400
            
""" ===============================<< Delete Site Visit Information ends >>===============================  """
""" ===============================<< Add Non Compliance Form starts >>===============================  """

@token_required
def addNonComplianceForm(data):
    site_id = data.site_id
    site_visit = db.session.query(PublicSiteVisitInfo).filter_by(site_id=site_id).first()
    no_siri_permohonan = site_visit.no_siri_permohonan
    pengesahan_peneriman = data.pengesahan_peneriman
    nama = data.nama
    alamat = data.alamat
    tarikh = data.tarikh
    lawatan_tapak_tarikh = data.lawatan_tapak_tarikh
    bertempat_di = data.bertempat_di
    wakil = data.wakil
    kad_pengenalan = data.kad_pengenalan
    peratusan_permis_adalah_kurang_daripada_50 = data.peratusan_permis_adalah_kurang_daripada_50
    kawasan_itu_kotor_dan_perlu_dibersihkan = data.kawasan_itu_kotor_dan_perlu_dibersihkan
    tiada_kemudahan_stopper_untuk_tayar_trak = data.tiada_kemudahan_stopper_untuk_tayar_trak
    tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah = data.tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah
    tiada_garisan_kuning_di_hadapan_rumah_sampah = data.tiada_garisan_kuning_di_hadapan_rumah_sampah
    tong_sampah_tidak_mencukupi_mengikut_spesifikasi = data.tong_sampah_tidak_mencukupi_mengikut_spesifikasi
    turning_point_tidak_mengikut_spesifikasi = data.turning_point_tidak_mengikut_spesifikasi
    mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai = data.mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai

    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type    
        role = user.role
        newNonCompliance = NonComplianceForm(
            no_siri_permohonan=no_siri_permohonan,
            pengesahan_peneriman=pengesahan_peneriman,nama=nama,alamat=alamat,tarikh=tarikh,lawatan_tapak_tarikh=lawatan_tapak_tarikh,bertempat_di=bertempat_di,
            wakil=wakil,kad_pengenalan=kad_pengenalan,peratusan_permis_adalah_kurang_daripada_50=peratusan_permis_adalah_kurang_daripada_50,
            kawasan_itu_kotor_dan_perlu_dibersihkan=kawasan_itu_kotor_dan_perlu_dibersihkan,tiada_kemudahan_stopper_untuk_tayar_trak=tiada_kemudahan_stopper_untuk_tayar_trak,
            tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah=tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah,tiada_garisan_kuning_di_hadapan_rumah_sampah=tiada_garisan_kuning_di_hadapan_rumah_sampah,
            tong_sampah_tidak_mencukupi_mengikut_spesifikasi=tong_sampah_tidak_mencukupi_mengikut_spesifikasi,turning_point_tidak_mengikut_spesifikasi=turning_point_tidak_mengikut_spesifikasi,
            mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai=mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai,
            inserted_by=id_card_no,site_id=site_id, inserted_date=today, active=1)
        db.session.add(newNonCompliance)
        site_visit.makalumat_ketidakpatuhan = 'borang_ketidakpatuhan'
        db.session.commit()
        non_compliance_id = newNonCompliance.non_compliance_id
        statement = f"Item ketidakpatuhan {non_compliance_id} berjaya ditambahkan."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()

        logger.info(f"Non compliance item {non_compliance_id} added successfully.")
        response_object = {
            'status': 'success',
            'message': 'non_compliance_form_added',
        }
        return response_object, 201
    except:
        logger.exception("Non Compliance Form not added")
        response_object = {
            'status': 'fail',
            'message': 'non_compliance_form_not_added',
        }
        return response_object, 400


""" ===============================<< Add Non Compliance Form ends >>===============================  """
""" ===============================<< Get Non Compliance Form Starts >>===============================  """

@token_required
def getNonComplianceForm(site_id):
    try:
        non_compliance_form = db.session.query(NonComplianceForm).filter_by(non_compliance_id=site_id, active=1).all()
        non_compliance_info_list = []
        
        if non_compliance_form != []:
            user = get_logged_in_user()
            id_card_no = user.no_kad_pengenalan
            for nonComplianceInfo in NonComplianceForm.query.filter_by(non_compliance_id=site_id, active=1):
                non_compliance_info_list.append({
                    'non_compliance_id': nonComplianceInfo.non_compliance_id,
                    'pengesahan_peneriman': nonComplianceInfo.pengesahan_peneriman,
                    'nama': nonComplianceInfo.nama,
                    'alamat': nonComplianceInfo.alamat,
                    'tarikh': date.strftime(nonComplianceInfo.tarikh, "%Y-%m-%d"),
                    'lawatan_tapak_tarikh': date.strftime(nonComplianceInfo.lawatan_tapak_tarikh, "%Y-%m-%d"),
                    'bertempat_di': nonComplianceInfo.bertempat_di,
                    'wakil': nonComplianceInfo.wakil,
                    'kad_pengenalan': nonComplianceInfo.kad_pengenalan,
                    'peratusan_permis_adalah_kurang_daripada_50': nonComplianceInfo.peratusan_permis_adalah_kurang_daripada_50,
                    'kawasan_itu_kotor_dan_perlu_dibersihkan': nonComplianceInfo.kawasan_itu_kotor_dan_perlu_dibersihkan,
                    'tiada_kemudahan_stopper_untuk_tayar_trak': nonComplianceInfo.tiada_kemudahan_stopper_untuk_tayar_trak,
                    'tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah': nonComplianceInfo.tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah,
                    'tiada_garisan_kuning_di_hadapan_rumah_sampah': nonComplianceInfo.tiada_garisan_kuning_di_hadapan_rumah_sampah,
                    'tong_sampah_tidak_mencukupi_mengikut_spesifikasi': nonComplianceInfo.tong_sampah_tidak_mencukupi_mengikut_spesifikasi,
                    'turning_point_tidak_mengikut_spesifikasi': nonComplianceInfo.turning_point_tidak_mengikut_spesifikasi,
                    'mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai': nonComplianceInfo.mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai
                })
            logger.info("Non Compliance Form Fetched")
            return jsonify(non_compliance_info_list)
        else:
            return jsonify(non_compliance_info_list)
            
    except:
        logger.exception("Non Compliance could not be Fetched")
        response_object = {
            'status': 'fail',
            'message': 'Non Compliance Info could not be fetched.',
        }
        return response_object, 400
    
 
""" ===============================<< Get Non Compliance Form ends >>===============================  """
""" ===============================<< Update Non Compliance Form starts >>===============================  """

@token_required
def updateNonComplianceForm(non_compliance_id,data):
    
    try:
        non_compliance = db.session.query(NonComplianceForm).filter_by(non_compliance_id=non_compliance_id, active=1).one()
    except:
        logger.exception('Non Compliance Form not found with non_compliance_id')
        response_object = {
                'status': 'fail',
                'message': 'Non Compliance Form  not found with non_compliance_id',
            }
        return response_object, 404
    if non_compliance:
        try:
            user = get_logged_in_user()
            id_card_no = user.no_kad_pengenalan
            today = date.today()
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            user_type = user.user_type    
            role = user.role
            non_compliance.pengesahan_peneriman = data.pengesahan_peneriman
            non_compliance.nama = data.nama
            non_compliance.alamat = data.alamat
            non_compliance.tarikh = data.tarikh
            non_compliance.lawatan_tapak_tarikh = data.lawatan_tapak_tarikh
            non_compliance.bertempat_di = data.bertempat_di
            non_compliance.wakil = data.wakil
            non_compliance.kad_pengenalan = non_compliance.kad_pengenalan
            non_compliance.peratusan_permis_adalah_kurang_daripada_50 = data.peratusan_permis_adalah_kurang_daripada_50
            non_compliance.kawasan_itu_kotor_dan_perlu_dibersihkan = data.kawasan_itu_kotor_dan_perlu_dibersihkan
            non_compliance.tiada_kemudahan_stopper_untuk_tayar_trak = data.tiada_kemudahan_stopper_untuk_tayar_trak
            non_compliance.tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah = data.tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah
            non_compliance.tiada_garisan_kuning_di_hadapan_rumah_sampah = data.tiada_garisan_kuning_di_hadapan_rumah_sampah
            non_compliance.tong_sampah_tidak_mencukupi_mengikut_spesifikasi = data.tong_sampah_tidak_mencukupi_mengikut_spesifikasi
            non_compliance.turning_point_tidak_mengikut_spesifikasi = data.turning_point_tidak_mengikut_spesifikasi
            non_compliance.mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai = data.mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai
            non_compliance.updated_by = id_card_no
            non_compliance.updated_date = today
            db.session.commit()
            
            statement = f"Item ketidakpatuhan {non_compliance_id} berjaya dikemas kini."
            log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
            db.session.add(log_info)
            db.session.commit()
            logger.info(f"Non compliance item {non_compliance_id} updated successfully.")
            response_object = {
                'status': 'success',
                'message': 'non_compliance_form_updated',
            }
            return response_object, 201
        except:
            logger.exception("Non Compliance Form could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'non_compliance_form_not_updated',
            }
            return response_object, 404
    else:
        response_object = {
                'status': 'fail',
                'message': 'non_compliance_form_not_updated',
            }
        return response_object, 404
   
""" ===============================<< Update Non Compliance Form ends >>===============================  """
""" ===============================<< Submit Rating starts >>===============================  """

@token_required
def submitRating(data):
    star = data.star
    feedback = data.feedback
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        user_type = user.user_type  
        role = user.role
        newRating = PublicRating(
            no_kad_pengenalan=id_card_no, star_rating=star, feedback_message=feedback, inserted_by=id_card_no, inserted_date=today, active=1)
        db.session.add(newRating)
        db.session.commit()
        statement = f"Penarafan {star} berjaya dihantar."
        log_info = LogPengguna(id_pengguna=id_card_no, tarikh=now, aktiviti=statement, user_type=user_type, role=role)
        db.session.add(log_info)
        db.session.commit()
        logger.info(f"Rating {star} submitted successfully.")
        response_object = {
            'status': 'success',
            'message': 'rating_added',
        }
        return response_object, 201
    except:
        logger.exception("Rating could not be be Submitted")
        response_object = {
            'status': 'fail',
            'message': 'rating_not_added',
        }
        return response_object, 400
    
""" ===============================<< Submit Rating ends >>===============================  """
""" ===============================<< Upload File Starts >>===============================  """

PHOTO_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
DOC_EXTENSIONS = set(['pdf'])
def allowed_photo(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in PHOTO_EXTENSIONS 
def allowed_doc(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in DOC_EXTENSIONS
  
def uploadFile(files):
   
    if files.filename == '':
        response_object = {
            'status': 'fail',
            'message': 'No file selected',
        }
        return response_object, 404
    if files and allowed_photo(files.filename):
        logger.info("Uploading Image")
        try:
            
            filename = secure_filename(files.filename)
            filename = re.sub('[^a-zA-Z0-9.]', '', filename)
            files.save(os.path.join(os.environ.get('PRIVATE_PHOTO_FOLDER'), filename))
            logger.info("Image Upload Successfull")
            response_object = { 
                'status': 'success',
                'message': 'Photo uploaded successfully',
            }
            return response_object, 201         
        except:
            logger.exception("Image Upload Failed")
            response_object = {
                'status': 'fail',
                'message': 'Something went wrong',
            }
            return response_object, 400
    elif files and allowed_doc(files.filename):
        logger.info("Document Upload")
        try:
            filename = secure_filename(files.filename)
            filename = re.sub('[^a-zA-Z0-9.]', '', filename)
            files.save(os.path.join(os.environ.get('PRIVATE_DOC_FOLDER'), filename))
            logger.info("Document Upload Successfull")
            response_object = { 
                'status': 'success',
                'message': 'Document uploaded successfully',
            }
            return response_object, 201         
        except:
            logger.exception("Document Upload Failed")
            response_object = {
                'status': 'fail',
                'message': 'Something went wrong',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'Allowed image types are -> png, jpg, jpeg, gif',
            }
        return response_object, 400

""" ===============================<< Upload File Ends >>===============================  """
""" ===============================<< Get Coordinates Starts >>===============================  """

def getCoordinates(data):
    parlimen = data.parlimen
    taman = data.taman
    try:
        coordinate_list = []
        for data in Coordinates.query.filter_by(parlimen=parlimen,taman=taman,active=1):
            coordinate_list.append({
                'Lokasi': data.lokasi,
                'latitude': data.latitude,
                'longitude': data.longitude
            })
        logger.info("Coordinates fetched successfully.")
        return jsonify(coordinate_list)
    except:
        logger.exception("Coordinates could not be fetched")
        response_object = {
            "status": "fail",
            "message": "Coordinates could not be fetched"
        }
        return response_object, 404

""" ===============================<< Get Coordinates Ends >>===============================  """
""" ===============================<< Map of Kawasan Perkhidmatan Starts >>===============================  """

def mapKawasanPerkhidmatan(data):
    parlimen = data.parlimen
    try:
        result = []
        for i in Coordinates.query.filter_by(parlimen=parlimen).all():
            result.append({
                "Parlimen Name" : parlimen,
                "lokasi" : [
                    {
                        "Lokasi" : i.lokasi,
                        "latitude" : i.latitude,
                        "longitude" : i.longitude,
                    }
                ]
            })
        logger.info("Coordinates fetched successfully.")
        return jsonify(result)
    except:
        logger.exception("Coordinates could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Coordinates could not be fetched',
            }
        return response_object, 400
    
""" ===============================<< Map of Kawasan Perkhidmatan Ends >>===============================  """
""" ===============================<< Upload File Starts >>===============================  """

PHOTO_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
DOC_EXTENSIONS = set(['pdf'])
def allowed_photo(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in PHOTO_EXTENSIONS 
def allowed_doc(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in DOC_EXTENSIONS
  
def uploadFreeFile(files):
   
    if files.filename == '':
        response_object = {
            'status': 'fail',
            'message': 'No file selected',
        }
        return response_object, 404
    if files and allowed_photo(files.filename):
        logger.info("Uploading Image")
        try:
            
            filename = secure_filename(files.filename)
            filename = re.sub('[^a-zA-Z0-9.]', '', filename)
            files.save(os.path.join(os.environ.get('PUBLIC_PHOTO_FOLDER'), filename))
            logger.info("Image Upload Successfull")
            response_object = { 
                'status': 'success',
                'message': 'Photo uploaded successfully',
            }
            return response_object, 201         
        except:
            logger.exception("Image Upload Failed")
            response_object = {
                'status': 'fail',
                'message': 'Something went wrong',
            }
            return response_object, 400
    elif files and allowed_doc(files.filename):
        logger.info("Document Upload")
        try:
            filename = secure_filename(files.filename)
            filename = re.sub('[^a-zA-Z0-9.]', '', filename)
            files.save(os.path.join(os.environ.get('PUBLIC_DOC_FOLDER'), filename))
            logger.info("Document Upload Successfull")
            response_object = { 
                'status': 'success',
                'message': 'Document uploaded successfully',
            }
            return response_object, 201         
        except:
            logger.exception("Document Upload Failed")
            response_object = {
                'status': 'fail',
                'message': 'Something went wrong',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'Allowed image types are -> png, jpg, jpeg, gif',
            }
        return response_object, 400

""" ===============================<< Upload File Ends >>===============================  """
@token_required
def getPublicUSerInfo():
    try:
        user = get_logged_in_user()
        user_info = dict(id_card_no = user.no_kad_pengenalan,username = user.nama,email= user.alamat_emel, password= user.kata_laluan)
        logger.info(f"{user.no_kad_pengenalan} : User Info Fetched")
        return user_info
    except:
        logger.exception("User Info Could Not Be Fetched")
        response_object = dict(status='fail',message='User Info Could Not Be Fetched')
        return response_object, 400

def updatePublicUserInfo(data):
    user = get_logged_in_user()
    if data.email != '' and user.alamat_emel != data.email:
        if MasterUser.find_by_email(data.email):
            abort(HTTPStatus.CONFLICT,"email_exists", status="fail")
    if data.username != '' and user.nama != data.username:
        if MasterUser.find_by_nama(data.username):
            abort(HTTPStatus.CONFLICT,"user_exists", status="fail")
    try:
        username = data.username
        email = data.email
        password = data.password
        if data.username == '':
            username = user.nama
        if data.email == '':
            email = user.alamat_emel
        if data.password == '':
            password = user.kata_laluan
        
        user.nama = username
        user.alamat_emel = email
        user.kata_laluan = password

        db.session.commit()
        logger.info("Public User Info Updated")
        response_object = dict(status='success',message='Public User Info Updated')
        return response_object, 200
    except:
        logger.exception("Public User Info Could Not Be Updated")
        response_object = dict(status='fail',message='Public User Info Could Not Be Updated')
        return response_object, 400