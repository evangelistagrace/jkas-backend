"""Flask CLI/Application entry point."""
from datetime import date
import os
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_cors import CORS
from flask import send_file
from app.main import create_app, db
from app.main.models.token_blacklist import BlacklistedToken
from app.main.models.models import (
    MasterUser, PublicAnnouncement, PublicManual, PhotoGallery, PublicApplicationList, PublicApplicationDetails, MeetingArea, MeetingPdfPath, 
    PublicSiteVisitInfo, NonComplianceForm, SiteVisitPdfPath, PublicRating, AgensiFeedback, AgencyJobPaymentClaim, CompoundInformation, InventoriPengguna, LogPengguna, OmpLama,
    InquiryInformation, OfficersList)
from app import api_bp

from applogger import logger


app = create_app('dev')
CORS(app)

app.register_blueprint(api_bp)
app.app_context().push()

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

""" View Image """
@app.route("/jkas_resourses/public/pdfs/<pdfname>")    
def pdfRead(pdfname):
    try:
        return send_file(os.environ.get('DOC_FOLDER')+pdfname)
    except:
        logger.exception("No pdf is stored with the filename")
        response_object = {
            "status": "fail",
            "message": "No pdf is stored with the filename"
        }
        return response_object

@app.route("/jkas_resourses/public/images/<imgname>")    
def imgRead(imgname):
    try:
        logger.info("image found")
        return send_file(os.environ.get('PHOTO_FOLDER')+imgname)
    except:
        logger.exception("No image is stored with the filename")
        response_object = {
            "status": "fail",
            "message": "No image is stored with the filename"
        }
        return response_object

        
@manager.command
def run():
    logger.debug("Starting")
    app.run(debug=True)


if __name__=="__main__":
    manager.run()
    