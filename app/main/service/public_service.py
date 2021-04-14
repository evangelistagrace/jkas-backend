""" Business logic for /auth API endpoints."""
from http import HTTPStatus
import os, json, sys, string, requests, secrets, random, re
from random import randint
from datetime import date, timedelta
import urllib.request
from flask import current_app, jsonify, session, request, redirect
from flask_restx import abort
from twilio.rest import Client
import itertools
import smtplib
from app.main import db
from .decorators import token_required
from app.main.models.token_blacklist import BlacklistedToken
from app.main.models.models import (
    MasterUser, PublicAnnouncement, PublicManual, PhotoGallery, PublicApplicationList, PublicApplicationDetails, MeetingArea, MeetingPdfPath,
    PublicSiteVisitInfo, NonComplianceForm, SiteVisitPdfPath, PublicRating, AgensiFeedback, AgencyJobPaymentClaim, Coordinates, OtpStore)
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
FROM_TITLE = os.environ.get('FROM_TITLE')
FROM_EMAIL = os.environ.get('FROM_EMAIL')

""" ===============================<< Get Announcement starts >>==============================="""

def getAnnouncement():
    try:
        filter_after = date.today() - timedelta(days = 90)
        public_announcement_list = []
        for announce in PublicAnnouncement.query.filter(PublicAnnouncement.date >= filter_after, PublicAnnouncement.active == 1).all():
            public_announcement_list.append({
                'announcement_heading': announce.announcement_heading,
                'announcement_id': announce.announcement_id,
                'announcement': announce.announcement,
                'date': date.strftime(announce.date, "%Y-%m-%d"),
            })
        logger.info("Public Announcement Fetched")
        return jsonify(public_announcement_list)
    except:
        logger.exception("Public Announcement could not be Fetched")
        response_object = {
            'status': 'fail',
            'message': 'Announcement list could not be fetched.',
        }
        return response_object, 400
    
""" ===============================<< Get Announcement ends >>==============================="""
""" ===============================<< Create Announcement starts >>==============================="""

def createAnnouncement(data):
    announcement_heading = data.announcement_heading
    announcement = data.announcement
    today = date.today()
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    if user.user_type == 'public':
        try:
            announcement_info = [{"announcement_heading": f"{announcement_heading}", "announcement": f"{announcement}", "date": f"{today}", "inserted_by": f"{id_card_no}", "inserted_date": f"{today}"}]
            for i in announcement_info:
                db.session.add(PublicAnnouncement(**i))
                db.session.commit()
            logger.info("Announcement added successfully")
            response_object = {
                'status': 'success',
                'message': 'Announcement added successfully',
            }
            return response_object, 201
        except:
            logger.exception("Public Announcement could not be added")
            response_object = {
                'status': 'fail',
                'message': 'Announcement could not be not added.',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'Not eligible to add Announcement',
            }
        return response_object, 400
    
""" ===============================<< Create Announcement ends >>==============================="""
""" ===============================<< Update Announcement starts >>==============================="""
def updateAnnouncement(data, announcement_id):
    announcement_heading = data.announcement_heading
    announcement = data.announcement
    today = date.today()
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
        
    if user.user_type == 'public' and PublicAnnouncement.find_by_announcement_id(announcement_id):
        try:
            public_announcement_obj = PublicAnnouncement.query.filter_by(announcement_id=announcement_id, active=1).first()
            public_announcement_obj.announcement_heading = announcement_heading
            public_announcement_obj.announcement = announcement
            public_announcement_obj.date = today
            public_announcement_obj.updated_date = today
            public_announcement_obj.updated_by = id_card_no
            db.session.commit()
            response_object = {
                'status':'success',
                'message':'public announcement updated successfully.'
            }
            logger.info("public announcement updated.")
            return response_object, 201
        except:
            logger.exception("Public Announcement could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'Announcement could not be not be updated.',
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'announcement_id not found or user is not public.',
            }
        return response_object, 400
    
""" ===============================<< Update Announcement ends >>==============================="""
""" ===============================<< Delete Announcement starts >>===============================  """

def deleteAnnouncementList(data):
    user = get_logged_in_user()
    announcement_id_list = data.announcement_id_list.split(",")
    try:
        if user.user_type == 'public':
            for i in announcement_id_list:
                if PublicAnnouncement.query.filter_by(announcement_id=i).first():
                    PublicAnnouncement.query.filter_by(announcement_id=i).first().active = 0
                
            db.session.commit()

            logger.info("Announcement list Deleted successfully")

            response_object = {
                "status": "success",
                "message": "Announcement list Deleted successfully."
            }
            return response_object, 200

        else:
            response_object = {
                "status": "fail",
                "message": "User is not Public."
            } 

    except:
        logger.exception("Announcement list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Announcement list could not be Deleted."
        }
        return response_object, 400
            
""" ===============================<< Delete Announcement ends >>===============================  """
""" ===============================<< Get Manual starts >>==============================="""

def getManual():
    try:
        public_mannual_list = []
        for app in PublicManual.query.filter_by(active=1):
            public_mannual_list.append({
                'manual_heading': app.manual_heading,
                'manual_body': app.manual_body,
                'manual_path': app.manual_path,
            })
        logger.info("Public Manual Fetched")
        return jsonify(public_mannual_list)
    except:
        logger.exception("Public Manual could not be Fetched")
        response_object = {
            'status': 'fail',
            'message': 'Manual list could not be fetched.',
        }
        return response_object, 400
    
""" ===============================<< Get Manual ends >>==============================="""
""" ===============================<< Create Manual starts >>==============================="""

def createManual(data):
    manual_heading = data.manual_heading
    manual_body = data.manual_body
    manual_path = data.manual_path
    today = date.today()
    manual_path = re.sub('[^a-zA-Z0-9.]', '', manual_path)
    manual_path = '/jkas_resourses/public/images/'+manual_path
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    if user.user_type == 'public':
        try:
            manual_info = [{"manual_heading": f"{manual_heading}", "manual_body": f"{manual_body}", "manual_path": f"{manual_path}", "inserted_by": f"{id_card_no}", "inserted_date": f"{today}"}]
            for i in manual_info:
                db.session.add(PublicManual(**i))
            db.session.commit()
            logger.info("Manual added successfully")
            response_object = {
                'status': 'success',
                'message': 'Manual added successfully',
            }
            return response_object, 201
        except:
            logger.exception("Public Manual could not be added")
            response_object = {
                'status': 'fail',
                'message': 'Manual could not be added.'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'Not eligible to add Manual'
            }
        return response_object, 400
    
""" ===============================<< Create Manual ends >>==============================="""
""" ===============================<< Update Manual starts >>==============================="""
def updateManual(data, mannual_id):
    manual_path = data.manual_path
    today = date.today()
    manual_path = re.sub('[^a-zA-Z0-9.]', '', manual_path)
    manual_path = '/jkas_resourses/public/images/'+manual_path
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    if user.user_type == 'admin' and PublicManual.find_by_mannual_id(mannual_id):
        try:
            public_mannual_obj = PublicManual.query.filter_by(mannual_id=mannual_id, active=1).first()
            public_mannual_obj.manual_path = manual_path
            public_mannual_obj.date = today
            public_mannual_obj.updated_date = today
            public_mannual_obj.updated_by = id_card_no
            db.session.commit()
            response_object = {
                'status':'success',
                'message':'public mannual updated successfully.'
            }
            logger.info("public mannual updated.")
            return response_object, 201
        except:
            logger.exception("Public Manual could not be added")
            response_object = {
                'status': 'fail',
                'message': 'Manual could not be updated.'
            }
            return response_object, 400
    else:
        response_object = {
            'status': 'fail',
            'message': 'mannual_id not found or user is not Admin.'
            }
        return response_object, 400
    
""" ===============================<< Update Manual ends >>==============================="""
""" ===============================<< Delete Manual starts >>===============================  """

def deleteManualList(data):

    user = get_logged_in_user()
    manual_id_list = data.manual_id_list.split(",")

    try:
        if user.user_type == 'admin':
            for i in manual_id_list:
                if PublicManual.query.filter_by(mannual_id=i).first():
                    PublicManual.query.filter_by(mannual_id=i).first().active = 0
                
            db.session.commit()
            logger.info("Manual list Deleted successfully")

            response_object = {
                "status": "success",
                "message": "Manual list Deleted successfully."
            }
            return response_object, 200
        else:
            response_object = {
                "status": "fail",
                "message": "User is not Admin."
            }            

    except:
        logger.exception("Manual list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Announcement list could not be Deleted."
        }
        return response_object, 400
            
""" ===============================<< Delete Manual ends >>===============================  """
""" ===============================<< Get Gallery Photo starts >>==============================="""

def getGalleryPhoto():
    try:
        photo_gallery_list = []
        for app in PhotoGallery.filter_by(active=1):
            photo_gallery_list.append({
                'photo_path': app.photo_path,
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
""" ===============================<< Registration of new user starts >>==============================="""

def triggerRegistration(data):
    name = data.name
    id_card_no = data.id_card_no.upper()
    email = data.email
    password = data.password
    user_type = 'public'
    
    if MasterUser.find_by_email(email):
        abort(HTTPStatus.CONFLICT,f"Email {email} is already registered", status="fail")
    if MasterUser.find_by_id_card(id_card_no):
            abort(HTTPStatus.CONFLICT,
                  f"ID Card Number {id_card_no} is already registered", status="fail")
    if MasterUser.find_by_nama(name):
            abort(HTTPStatus.CONFLICT,
                  f"Username {name} is already registered", status="fail")
    return register(name, id_card_no, email, password, user_type)


def register(name, id_card_no, email, password, user_type):

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
    message = MIMEMultipart()
    message['From'] = FROM_EMAIL
    message['To'] = TO_EMAIL
    message['Subject'] = FROM_TITLE
    MAIL_CONTENT = f"Please note down the 6 digit code - {randotp} for registration of user of ID Card No. {id_card_no}"
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
    id_card_no = data.id_card_no
    user_type = 'public'
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
            updated_user = MasterUser(
                nama=name, no_kad_pengenalan=id_card_no, alamat_emel=email, password=password, user_type=user_type)
            db.session.add(updated_user)
            OtpStore.query.filter(OtpStore.no_kad_pengenalan == id_card_no).delete()
            db.session.commit()
            logger.info("User Registered")
            response = {
                'status': 'success',
                'message': f'User {id_card_no} registered'
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
    id_card_no = data.id_card_no.upper()
    password = data.password
    user = MasterUser.find_by_id_card(id_card_no)
    if not user or not user.check_password(password):
        logger.debug("Invalid Credential")
        abort(HTTPStatus.UNAUTHORIZED,"Invalid credentials! Please try again.", status="fail")
    elif user.user_type == 'admin' or user.user_type == 'public':
        access_token = user.encode_access_token()
        logger.info("Login Successfull")
        nama = user.nama
        return _create_auth_successful_response(
            token=access_token.decode(),
            status_code=HTTPStatus.OK,
            message="successfully logged in",
            user=nama,
        )       
    else:
        response_object = {
                'status': 'success',
                'message': f'User {id_card_no} cant sign in here',
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
    id_card_no = data.id_card_no.upper()
    email = data.email
    if MasterUser.find_by_email(email) and MasterUser.find_by_id_card(id_card_no):
        reset_password_token = secrets.token_hex(20)
        user = MasterUser.find_by_email(email)
        user.reset_password_token = reset_password_token
        db.session.commit()
        return make_forgot_mail(id_card_no, email, reset_password_token)
    else:
        logger.debug("Email or ID Card Not  Present")
        response_object = {
            'status': 'fail',
            'message': f'ID Card Number: {id_card_no} or Email: {email} is not registered'
        }
        return response_object, 400

def make_forgot_mail(id_card_no, email, reset_password_token):
    id_card_no = id_card_no
    TO_EMAIL = email
    message = MIMEMultipart()
    message['From'] = FROM_EMAIL
    message['To'] = TO_EMAIL
    message['Subject'] = 'JKAS Forgot Password'
    MAIL_CONTENT = f"Click Here to Change Your Password https://ppks.ml/public/resetpassword?token={reset_password_token}"
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
            'message': 'Reset password link sent successfully.'
            }
        return response_object, 200
    except:
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
        logger.exception('No user not found with the reset password token')
        response_object = {
            'status': 'fail',
            'message': 'No user not found with the reset password token !'
        }
        return response_object, 400
    if new_user:
        try:
            new_user.password = password
            db.session.commit()
            logger.info("Password reset Successfull")
            response_object = {
                'status': 'success',
                'message': 'Password updated successfully!'
            }
            logger.info("Password Updated")
            return response_object, 201
        except:
            logger.exception("Password Update Failed")
            response_object = {
                'status': 'fail',
                'message': 'Password updated failed!'
            }
            return response_object, 400
    
    
""" ===============================<< Reset password ends >>===============================  """
""" ===============================<< List Application starts >>===============================  """

@token_required
def viewApplicationList():
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan
    try:
        application_list = []
        for app in PublicApplicationList.query.filter_by(no_kad_pengenalan=id_card_no,active=1):
            application_list.append({
                'application_id': app.application_id,
                'no_siri_permohonan': app.no_siri_permohonan,
                'tarikh_permohonan': date.strftime(app.tarikh_permohonan,  "%Y-%m-%d"),
                'dokumen_senarai': app.dokumen_senarai,
                'status_semakan_dokumen': app.status_semakan_dokumen,
                'mesyuarat_permohanan_serahan_kawasan': app.mesyuarat_permohanan_serahan_kawasan,
                'maklumat_lawatan_tapak_id': app.maklumat_lawatan_tapak_id,
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

""" ===============================<< view Application List ends >>===============================  """
""" ===============================<< Delete Application List starts >>===============================  """

@token_required
def deleteApplicationList(data):
    app_id_list = data.app_id_list.split(",")
    try:
        for i in app_id_list:
            if PublicApplicationList.query.filter_by(application_id=i).first():
                PublicApplicationList.query.filter_by(application_id=i).first().active = 0
                
        db.session.commit()
        logger.info("Application list Deleted successfully")
        response_object = {
            "status": "success",
            "message": "Application list Deleted successfully"
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
""" ===============================<< submit Application starts >>===============================  """

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
    surat_permohonan_perkhidmatan_pembersihan_dokumen = data.surat_permohonan_perkhidmatan_pembersihan_dokumen
    if surat_permohonan_perkhidmatan_pembersihan_dokumen:
        surat_permohonan_perkhidmatan_pembersihan_dokumen = re.sub('[^a-zA-Z0-9.]', '', surat_permohonan_perkhidmatan_pembersihan_dokumen)
        surat_permohonan_perkhidmatan_pembersihan_dokumen = '/jkas_resourses/public/pdfs/'+surat_permohonan_perkhidmatan_pembersihan_dokumen
    surat_salinan_CF_dokumen = data.surat_salinan_CF_dokumen
    if surat_salinan_CF_dokumen:
        surat_salinan_CF_dokumen = re.sub('[^a-zA-Z0-9.]', '', surat_salinan_CF_dokumen)
        surat_salinan_CF_dokumen = '/jkas_resourses/public/pdfs/'+surat_salinan_CF_dokumen
    salinan_status_pembanginan_dokumen = data.salinan_status_pembanginan_dokumen
    if salinan_status_pembanginan_dokumen:
        salinan_status_pembanginan_dokumen = re.sub('[^a-zA-Z0-9.]', '', salinan_status_pembanginan_dokumen)
        salinan_status_pembanginan_dokumen = '/jkas_resourses/public/pdfs/'+salinan_status_pembanginan_dokumen
    bagi_status_pembangunan_dokumen = data.bagi_status_pembangunan_dokumen
    if bagi_status_pembangunan_dokumen:
        bagi_status_pembangunan_dokumen = re.sub('[^a-zA-Z0-9.]', '', bagi_status_pembangunan_dokumen)
        bagi_status_pembangunan_dokumen = '/jkas_resourses/public/pdfs/'+bagi_status_pembangunan_dokumen
    
    try:
        user = get_logged_in_user()
        id_card_no = user.no_kad_pengenalan
        today = date.today()
        app_srl_no = 'PSPPA'+''.join(random.choices(string.digits, k=4)) + \
                                     ''.join(random.choices(
                                         string.ascii_uppercase, k=2))
        if PublicApplicationDetails.find_by_app_srl_no(app_srl_no):
            return submitApplication()
        add_application_details = PublicApplicationDetails(kutipan_sampah=kutipan_sampah, sapuan_jalan=sapuan_jalan, cucian_longkang=cucian_longkang,
                                                pemotongan_rumput=pemotongan_rumput, dinyatakan_nama_bangunan=dinyatakan_nama_bangunan,
                                                strata_title=strata_title, hak_milik_kekal=hak_milik_kekal, nama_jalan=nama_jalan,
                                                panjang_jalan_mengikut_nama_jalan=panjang_jalan_mengikut_nama_jalan, panjang_longkang=panjang_longkang,
                                                luas_kawasan_berumput=luas_kawasan_berumput, luas_kawasan_TPKK=luas_kawasan_TPKK, parkir_area=parkir_area,
                                                surat_permohonan_perkhidmatan_pembersihan_dokumen=surat_permohonan_perkhidmatan_pembersihan_dokumen,
                                                surat_salinan_CF_dokumen=surat_salinan_CF_dokumen, salinan_status_pembanginan_dokumen=salinan_status_pembanginan_dokumen,
                                                bagi_status_pembangunan_dokumen=bagi_status_pembangunan_dokumen,
                                                no_siri_permohonan=app_srl_no, no_kad_pengenalan=id_card_no,
                                                inserted_by=id_card_no, inserted_date=today, active=1)

        db.session.add(add_application_details)
        db.session.commit()
        add_application_list = PublicApplicationList(no_kad_pengenalan=id_card_no,
                                                        no_siri_permohonan=app_srl_no,
                                                        dokumen_senarai=app_srl_no,
                                                        active=1)
        db.session.add(add_application_list)
        db.session.commit()
        logger.info("Application added successfully")
        response_object = {
            'status': 'success',
            'message': 'Application added successfully',
            'app_srl_no': f'{app_srl_no}'
            }
        return response_object, 201
    except:
        logger.exception("Application not added")
        response_object = {
            'status': 'fail',
            'message': 'Application not added!',
        }
        return response_object, 400


""" ===============================<< submit Application ends >>===============================  """
""" ===============================<< view Application Details starts >>===============================  """

@token_required
def viewApplicationDetails():
    user = get_logged_in_user()
    id_card_no = user.no_kad_pengenalan

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
            site_visit.tarikh = data.tarikh
            site_visit.lawatan_tapak = data.lawatan_tapak
            site_visit.keputusan_lawatan_tapak = data.keputusan_lawatan_tapak
            site_visit.makalumat_ketidakpatuhan = data.makalumat_ketidakpatuhan
            maklum_balas_ketidakpatuhan = data.maklum_balas_ketidakpatuhan
            if maklum_balas_ketidakpatuhan:
                maklum_balas_ketidakpatuhan = re.sub('[^a-zA-Z0-9.]', '', maklum_balas_ketidakpatuhan)
            site_visit.maklum_balas_ketidakpatuhan = maklum_balas_ketidakpatuhan
            site_visit.updated_by = id_card_no
            site_visit.updated_date = today
            db.session.commit()
            logger.info("Site Visit Info Updated")
            response_object = {
                'status': 'success',
                'message': 'Site Visit Info Updated.',
            }
            return response_object, 201
        except:
            logger.exception("Site Visit Info could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'Site Visit Info could not be updated',
            }
            return response_object, 404
    else:
        response_object = {
                'status': 'fail',
                'message': 'Site Visit Info not found with site_id',
            }
        return response_object, 404
   
""" ===============================<< Update Site Visit Information ends >>===============================  """
""" ===============================<< Delete Site Visit Information starts >>===============================  """

@token_required
def deleteSiteVisitInformation(data):
    user = get_logged_in_user()
    site_visit_id_list = data.site_visit_id_list.split(",")
    try:
        if user.user_type == 'public':
            for i in site_visit_id_list:
                if PublicSiteVisitInfo.query.filter_by(site_id=i).first():
                    PublicSiteVisitInfo.query.filter_by(site_id=i).first().active = 0
                    
            db.session.commit()
            logger.info("Site Visit Information list Deleted successfully")
            
            response_object = {
                "status": "success",
                "message": "Site Visit Information list Deleted successfully"
            }
            return response_object, 200
        else:
            response_object = {
                "status": "fail",
                "message": "User is not Public."
            } 
    except:
        logger.exception("Site Visit Information list could not be deleted")
        response_object = {
            "status": "fail",
            "message": "Site Visit Information list could not be Deleted"
        }
        return response_object, 400
            
""" ===============================<< Delete Site Visit Information ends >>===============================  """
""" ===============================<< Add Non Compliance Form starts >>===============================  """

@token_required
def addNonComplianceForm(data):
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
        newNonCompliance = NonComplianceForm(  
                                            pengesahan_peneriman=pengesahan_peneriman,
                                            nama=nama,
                                            alamat=alamat,
                                            tarikh=tarikh,
                                            lawatan_tapak_tarikh=lawatan_tapak_tarikh,
                                            bertempat_di=bertempat_di,
                                            wakil=wakil,
                                            kad_pengenalan=kad_pengenalan,
                                            peratusan_permis_adalah_kurang_daripada_50=peratusan_permis_adalah_kurang_daripada_50,
                                            kawasan_itu_kotor_dan_perlu_dibersihkan=kawasan_itu_kotor_dan_perlu_dibersihkan,
                                            tiada_kemudahan_stopper_untuk_tayar_trak=tiada_kemudahan_stopper_untuk_tayar_trak,
                                            tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah=tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah,
                                            tiada_garisan_kuning_di_hadapan_rumah_sampah=tiada_garisan_kuning_di_hadapan_rumah_sampah,
                                            tong_sampah_tidak_mencukupi_mengikut_spesifikasi=tong_sampah_tidak_mencukupi_mengikut_spesifikasi,
                                            turning_point_tidak_mengikut_spesifikasi=turning_point_tidak_mengikut_spesifikasi,
                                            mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai=mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai,
                                            inserted_by=id_card_no, inserted_date=today, active=1)
        db.session.add(newNonCompliance)
        db.session.commit()
        logger.info("Non Complianc Form added Successfully")
        response_object = {
            'status': 'success',
            'message': 'Non Compliance Form added. Database updated successfully',
        }
        return response_object, 201
    except:
        logger.exception("Non Compliance Form not added")
        response_object = {
            'status': 'fail',
            'message': 'Non Compliance Form not added',
        }
        return response_object, 400


""" ===============================<< Add Non Compliance Form ends >>===============================  """
""" ===============================<< Get Non Compliance Form Starts >>===============================  """

@token_required
def getNonComplianceForm(no_siri_permohonan):
    if no_siri_permohonan == None:
        abort(HTTPStatus.CONFLICT,f"Please Provide valid no_siri_permohonan", status="fail")
    try:
        non_compliance_form = NonComplianceForm.find_by_no_siri_permohonan(no_siri_permohonan)
    except:
        logger.exception('Non Compliance Form is not found')
        response_object = {
                'status': 'fail',
                'message': f'Non Compliance Form is not found for Application No. {no_siri_permohonan}',
            }
        return response_object, 404
    if non_compliance_form:
        try:
            user = get_logged_in_user()
            id_card_no = user.no_kad_pengenalan
            non_compliance_info_list = []
            for nonComplianceInfo in NonComplianceForm.query.filter_by(no_siri_permohonan=no_siri_permohonan, kad_pengenalan=id_card_no, active=1):
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
        except:
            logger.exception("Non Compliance could not be Fetched")
            response_object = {
                'status': 'fail',
                'message': 'Non Compliance Info could not be fetched.',
            }
            return response_object, 400
    else:
        response_object = {
                'status': 'fail',
                'message': f'Non Compliance Form is not found for Application No. {no_siri_permohonan}',
            }
        return response_object, 404
 
""" ===============================<< Get Non Compliance Form ends >>===============================  """
""" ===============================<< Update Non Compliance Form starts >>===============================  """

@token_required
def updateNonComplianceForm(non_compliance_id,data):
    if non_compliance_id == None or non_compliance_id == 'undefined':
        abort(HTTPStatus.CONFLICT,f"Please Provide valid non_compliance_id", status="fail")
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
            db.session.commit()
            logger.info("Non Compliance Form  Updated")
            response_object = {
                'status': 'success',
                'message': 'Non Compliance Form Updated.',
            }
            return response_object, 201
        except:
            logger.exception("Non Compliance Form could not be updated")
            response_object = {
                'status': 'fail',
                'message': 'Non Compliance Form could not be updated',
            }
            return response_object, 404
    else:
        response_object = {
                'status': 'fail',
                'message': 'Non Compliance Form not found with non_compliance_id',
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
        newRating = PublicRating(
            no_kad_pengenalan=id_card_no, star_rating=star, feedback_message=feedback, inserted_by=id_card_no, inserted_date=today, active=1)
        db.session.add(newRating)
        db.session.commit()
        logger.info("Rating Submitted")
        response_object = {
            'status': 'success',
            'message': 'Feedback Submitted Successfully.',
        }
        return response_object, 201
    except:
        logger.exception("Rating could not be be Submitted")
        response_object = {
            'status': 'fail',
            'message': 'Feedback did not Submitted.',
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
            files.save(os.path.join(os.environ.get('PHOTO_FOLDER'), filename))
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
            files.save(os.path.join(os.environ.get('DOC_FOLDER'), filename))
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
        logger.info("Coordinates fetched Successfully")
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
        logger.info("Coordinates fetched Successfully")
        return jsonify(result)
    except:
        logger.exception("Coordinates could not be fetched")
        response_object = {
            'status': 'fail',
            'message': 'Coordinates could not be fetched',
            }
        return response_object, 400
    
""" ===============================<< Map of Kawasan Perkhidmatan Ends >>===============================  """
