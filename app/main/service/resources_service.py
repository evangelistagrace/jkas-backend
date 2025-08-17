""" Business logic for /auth API endpoints."""
from http import HTTPStatus
import os, json, sys, string, requests, secrets, random, re
from random import randint
from datetime import date, datetime, timedelta
from flask import current_app, jsonify, session, request, redirect, send_file
from flask_restx import abort
import pytz
import itertools
import smtplib
from sqlalchemy import desc
from app.main import db
from .decorators import token_required
from app.main.util.datetime_util import remaining_fromtimestamp, format_timespan_digits
import setting
import logging
from applogger import logger


""" ===============================<< PDF Read starts >>=============================== """
#@token_required
def readPDF(pdfname):
    try:
        logger.info("pdf found")
        response = send_file(os.environ.get('PRIVATE_DOC_FOLDER')+pdfname)
        response.headers.set("Content-Type", "application/pdf")
        return response
    except:
        logger.exception("No pdf is stored with the filename")
        response_object = {
            "status": "fail",
            "message": "No pdf is stored with the filename"
        }
        return response_object

""" ===============================<< PDF Read ends >>=============================== """
""" ===============================<< PDF Read starts >>=============================== """

#@token_required
def readImage(imagename):
    try:
        logger.info("image found")
        response = send_file(os.environ.get('PRIVATE_PHOTO_FOLDER')+imagename)
        response.headers.set("Content-Type", "image/png")
        return response
    except:
        logger.exception("No image is stored with the filename")
        response_object = {
            "status": "fail",
            "message": "No image is stored with the filename"
        }
        return response_object
      
""" ===============================<< PDF Read ends >>=============================== """

""" ===============================<< PDF Read starts >>=============================== """
def getPDF(pdfname):
    try:
        logger.info("pdf found")
        response = send_file(os.path.join(os.environ.get('PUBLIC_DOC_FOLDER'), pdfname))
        response.headers.set("Content-Type", "application/pdf")
        return response
    except:
        logger.exception("No pdf is stored with the filename")
        response_object = {
            "status": "fail",
            "message": "No pdf is stored with the filename"
        }
        return response_object

""" ===============================<< PDF Read ends >>=============================== """
""" ===============================<< PDF Read starts >>=============================== """

def getImage(imagename):
    try:
        logger.info("image found")
        response = send_file(os.path.join(os.environ.get('PUBLIC_PHOTO_FOLDER'), imagename))
        response.headers.set("Content-Type", "image/png")
        return response
    except:
        logger.exception("No image is stored with the filename")
        response_object = {
            "status": "fail",
            "message": "No image is stored with the filename"
        }
        return response_object
      
""" ===============================<< PDF Read ends >>=============================== """

""" ===============================<< Video Read starts >>=============================== """

def getVideo(videoname):
    try:
        logger.info("Video found")
        response = send_file(os.environ.get('PUBLIC_VIDEO_FOLDER')+videoname)
        response.headers.set("Content-Type", "video/mp4")
        return response
    except:
        logger.exception("No Video is stored with the filename")
        response_object = {
            "status": "fail",
            "message": "No Video is stored with the filename"
        }
        return response_object
      
""" ===============================<< Video Read ends >>=============================== """