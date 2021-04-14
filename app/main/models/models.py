"""Class definition for User model."""
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import jwt
from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property
import datetime
from datetime import datetime
from app.main import db, bcrypt
from app.main.models.token_blacklist import BlacklistedToken
from app.main.util.datetime_util import (
    utc_now,
    get_local_utcoffset,
    make_tzaware,
    localized_dt_string,
)
from app.main.util.result import Result


class MasterUser(db.Model):
    """User model for storing logon credentials and other details."""

    __tablename__ = "master_user"

    id = db.Column(db.Integer, primary_key=True, unique= True, autoincrement=True)
    nama = db.Column(db.String(20), nullable=True)
    nama_pengguna = db.Column(db.String(20), nullable=True)
    no_kad_pengenalan = db.Column(db.String(20), unique=True)
    alamat_emel = db.Column(db.String(40), nullable=True)
    kata_laluan = db.Column(db.String(100), nullable=True)
    reset_password_token = db.Column(db.String(50), nullable= True)
    admin = db.Column(db.Boolean, nullable=True)
    role = db.Column(db.String(20), nullable=True)
    parlimen=db.Column(db.String(20), nullable= True)
    lokasi=db.Column(db.String(100), nullable= True)
    nama_pegawai_merinyu=db.Column(db.String(20), nullable= True)
    status_tindakan=db.Column(db.String(100), nullable= True)
    user_type=db.Column(db.String(20))
    active = db.Column(db.Boolean, default=1)
    
    
    def __repr__(self):
        return (
            f"<no_kad_pengenalan={self.no_kad_pengenalan}, nama={self.nama}, alamat_emel={self.alamat_emel} >"
        )

    @hybrid_property
    def registered_on_str(self):
        registered_on_utc = make_tzaware(
            self.registered_on, use_tz=timezone.utc, localize=False
        )
        return localized_dt_string(registered_on_utc, use_tz=get_local_utcoffset())

    @property
    def password(self):
        raise AttributeError("password: write-only field")

    @password.setter
    def password(self, password):
        log_rounds = current_app.config.get("BCRYPT_LOG_ROUNDS")
        hash_bytes = bcrypt.generate_password_hash(password, log_rounds)
        self.kata_laluan = hash_bytes.decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.kata_laluan, password)

    def encode_access_token(self):
        now = datetime.now(timezone.utc)
        token_age_h = current_app.config.get("TOKEN_EXPIRE_HOURS")
        token_age_m = current_app.config.get("TOKEN_EXPIRE_MINUTES")
        expire = now + timedelta(hours=token_age_h, minutes=token_age_m)
        if current_app.config["TESTING"]:
            expire = now + timedelta(seconds=5)
        payload = dict(exp=expire, iat=now, sub=self.id,)
        key = current_app.config.get("SECRET_KEY")
        return jwt.encode(payload, key, algorithm="HS256")

    @staticmethod
    def decode_access_token(access_token):
        if isinstance(access_token, bytes):
            access_token = access_token.decode("ascii")
        if access_token.startswith("Bearer "):
            split = access_token.split("Bearer")
            access_token = split[1].strip()
        try:
            key = current_app.config.get("SECRET_KEY")
            payload = jwt.decode(access_token, key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            error = "Access token expired. Please log in again."
            return Result.Fail(error)
        except jwt.InvalidTokenError:
            error = "Invalid token. Please log in again."
            return Result.Fail(error)

        if BlacklistedToken.check_blacklist(access_token):
            error = "Token blacklisted. Please log in again."
            return Result.Fail(error)
        user_dict = dict(
            id=payload["sub"],
            token=access_token,
            expires_at=payload["exp"],
        )
        return Result.Ok(user_dict)

    @classmethod
    def find_by_email(cls, alamat_emel):
        return cls.query.filter_by(alamat_emel=alamat_emel).first()
    
    @classmethod
    def find_by_id_card(cls, no_kad_pengenalan):
        return cls.query.filter_by(no_kad_pengenalan=no_kad_pengenalan).first()
    
    @classmethod
    def find_by_nama_pengguna(cls, nama_pengguna):
        return cls.query.filter_by(nama_pengguna=nama_pengguna).first()
    
    @classmethod
    def find_by_nama(cls, nama):
        return cls.query.filter_by(nama=nama).first()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()
    
class PublicAnnouncement(db.Model):
    __tablename__= "public_announcement" 
    announcement_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    announcement_heading=db.Column(db.String(300))
    announcement=db.Column(db.String(8000))
    date=db.Column(db.Date)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
    @classmethod
    def find_by_announcement_id(cls, announcement_id):
        return cls.query.filter_by(announcement_id=announcement_id).first()
    
class PublicManual(db.Model):
    __tablename__= "public_mannual"
    mannual_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    manual_heading=db.Column(db.String(300))
    manual_body=db.Column(db.String(5000))
    manual_path=db.Column(db.String(500))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
    @classmethod
    def find_by_mannual_id(cls, mannual_id):
        return cls.query.filter_by(mannual_id=mannual_id).first()
    

class PhotoGallery(db.Model):
    __tablename__= "photo_gallery"
    photo_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    photo_path=db.Column(db.String(500))
    active = db.Column(db.Boolean, default=1)
    
class PublicApplicationList(db.Model):
    __tablename__= "application_list"  
    application_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_kad_pengenalan=db.Column(db.String(20), db.ForeignKey('master_user.no_kad_pengenalan', ondelete="CASCADE"))
    no_siri_permohonan=db.Column(db.String(20), unique=True)
    tarikh_permohonan=db.Column(db.Date, default=utc_now) 
    dokumen_senarai=db.Column(db.String(100), nullable=True)
    status_semakan_dokumen=db.Column(db.Boolean, nullable=True)
    mesyuarat_permohanan_serahan_kawasan=db.Column(db.String(100), nullable=True)
    maklumat_lawatan_tapak_id=db.Column(db.String(20), nullable=True)
    surat_penyerahan_kawasan=db.Column(db.String(200), nullable=True)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
       
class PublicApplicationDetails(db.Model):
    __tablename__="application_details"
    application_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_kad_pengenalan=db.Column(db.String(20), db.ForeignKey('master_user.no_kad_pengenalan', ondelete="CASCADE"))
    kutipan_sampah = db.Column(db.Boolean)
    sapuan_jalan = db.Column(db.Boolean)
    cucian_longkang = db.Column(db.Boolean)
    pemotongan_rumput = db.Column(db.Boolean)
    dinyatakan_nama_bangunan = db.Column(db.String(20))
    strata_title = db.Column(db.Boolean)
    hak_milik_kekal = db.Column(db.Boolean)
    nama_jalan = db.Column(db.Boolean)
    panjang_jalan_mengikut_nama_jalan = db.Column(db.Boolean)
    panjang_longkang = db.Column(db.Boolean)
    luas_kawasan_berumput = db.Column(db.Boolean)
    luas_kawasan_TPKK = db.Column(db.Boolean)
    parkir_area = db.Column(db.Boolean)
    surat_permohonan_perkhidmatan_pembersihan_dokumen = db.Column(db.String(500))
    surat_salinan_CF_dokumen = db.Column(db.String(500))
    salinan_status_pembanginan_dokumen = db.Column(db.String(500))
    bagi_status_pembangunan_dokumen = db.Column(db.String(500))
    surat_permohonan_perkhidmatan_pembersihan_status = db.Column(db.Boolean)
    surat_salinan_CF_status = db.Column(db.Boolean)
    salinan_status_pembanginan_status = db.Column(db.Boolean)
    bagi_status_pembangunan_status = db.Column(db.Boolean)
    status_dokumen_keseluruhan = db.Column(db.Boolean)
    no_siri_permohonan = db.Column(db.String(20), unique=True)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
        
    @classmethod
    def find_by_app_srl_no(cls, no_siri_permohonan):
        return cls.query.filter_by(no_siri_permohonan=no_siri_permohonan).first()
    
class MeetingArea(db.Model):
    __tablename__= "meeting_area" 
    meeting_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_siri_permohonan=db.Column(db.String(20), db.ForeignKey('application_list.no_siri_permohonan', ondelete="CASCADE"))
    tarikh=db.Column(db.Date)
    masa=db.Column(db.String(20))
    tempat=db.Column(db.String(100))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
    

class MeetingPdfPath(db.Model):
    __tablename__= "meeting_pdf_path"
    pdf_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_siri_permohonan=db.Column(db.String(20), db.ForeignKey('application_list.no_siri_permohonan', ondelete="CASCADE"))
    pdfpath=db.Column(db.String(500))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
     
class PublicSiteVisitInfo(db.Model):
    __tablename__= "public_site_visit_info" 
    site_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_siri_permohonan=db.Column(db.String(20), db.ForeignKey('application_list.no_siri_permohonan', ondelete="CASCADE"))
    tarikh=db.Column(db.Date)    
    lawatan_tapak=db.Column(db.String(50))
    tarikh_lawatan_tapak=db.Column(db.Date)
    keputusan_lawatan_tapak=db.Column(db.String(50))
    makalumat_ketidakpatuhan=db.Column(db.String(100))    
    maklum_balas_ketidakpatuhan=db.Column(db.String(500))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
    
    @classmethod
    def find_by_app_srl_no(cls, no_siri_permohonan):
        return cls.query.filter_by(no_siri_permohonan=no_siri_permohonan).first()

class SiteVisitPdfPath(db.Model):
    __tablename__= "site_visit_pdf_path"
    pdf_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    site_id=db.Column(db.Integer, db.ForeignKey('public_site_visit_info.site_id', ondelete="CASCADE"))
    pdfpath=db.Column(db.String(500))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
        
class NonComplianceForm(db.Model):
    __tablename__="non_compliance_form"
    non_compliance_id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_siri_permohonan=db.Column(db.String(20), db.ForeignKey('application_list.no_siri_permohonan', ondelete="CASCADE"))
    pengesahan_peneriman = db.Column(db.String(30))
    nama = db.Column(db.String(30))
    alamat = db.Column(db.String(500))
    tarikh =  db.Column(db.Date, nullable=True) 
    lawatan_tapak_tarikh =  db.Column(db.Date, nullable=True)
    bertempat_di = db.Column(db.String(40))
    wakil = db.Column(db.String(40))
    kad_pengenalan = db.Column(db.String(20))
    peratusan_permis_adalah_kurang_daripada_50=db.Column(db.Boolean)
    kawasan_itu_kotor_dan_perlu_dibersihkan=db.Column(db.Boolean)
    tiada_kemudahan_stopper_untuk_tayar_trak=db.Column(db.Boolean)
    tiada_kemudahan_greating_di_hadapan_pintu_rumah_sampah=db.Column(db.Boolean)
    tiada_garisan_kuning_di_hadapan_rumah_sampah=db.Column(db.Boolean)
    tong_sampah_tidak_mencukupi_mengikut_spesifikasi=db.Column(db.Boolean)
    turning_point_tidak_mengikut_spesifikasi=db.Column(db.Boolean)
    mesin_swm_24m_perlu_ditinggikan_6_inci_dari_lantai=db.Column(db.Boolean)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
    @classmethod
    def find_by_no_siri_permohonan(cls, no_siri_permohonan):
        return cls.query.filter_by(no_siri_permohonan=no_siri_permohonan).first()
       

    
class PublicRating(db.Model):
    __tablename__= "public_rating" 
    rating_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_kad_pengenalan=db.Column(db.String(20), db.ForeignKey('master_user.no_kad_pengenalan', ondelete="CASCADE"))
    star_rating=db.Column(db.Float)     
    feedback_message=db.Column(db.String(500))  
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
        
class AgensiFeedback(db.Model):
    __tablename__= "agensi_feedback"  
    feedback_id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_siri_notis_pemberitahuan = db.Column(db.String(20), db.ForeignKey('master_user.no_kad_pengenalan', ondelete="CASCADE"))
    organisasi=db.Column(db.String(200)) 
    nama_pegawai_merinyu=db.Column(db.String(50))
    maklum_balas=db.Column(db.String(255))
    gambar_sebelum=db.Column(db.String(500), nullable=True)
    gambar_selepas=db.Column(db.String(500), nullable=True)
    sebelum_tarikh_masa=db.Column(db.String(60), nullable=True)
    selepas_tarikh_masa=db.Column(db.String(60), nullable=True)
    gambar_laporan=db.Column(db.String(500), nullable=True)
    laporan_tarikh_masa=db.Column(db.String(60), nullable=True)
    kerja_selesail=db.Column(db.Boolean, nullable=True)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    @classmethod
    def find_by_np(cls, no_siri_notis_pemberitahuan):
        return cls.query.filter_by(no_siri_notis_pemberitahuan=no_siri_notis_pemberitahuan).first()
    
class AgencyJobPaymentClaim(db.Model):
    __tablename__= "agency_job_payment_claim" 
    id=db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    no_inbois=db.Column(db.String(20), unique=True)
    kontraktor=db.Column(db.String(40))
    nama_pemohon=db.Column(db.String(20))
    e_mei=db.Column(db.String(30))
    jumlah_tuntutan=db.Column(db.String(20))
    inbois_dokumen=db.Column(db.String(500))
    ringkasan_dokumen=db.Column(db.String(500))
    lampiran=db.Column(db.String(500))
    tarikh=db.Column(db.Date)
    status=db.Column(db.String(50))
    ulasan_pegawai=db.Column(db.String(50))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
    
    @classmethod
    def find_by_invoice_no(cls, no_inbois):
        return cls.query.filter_by(no_inbois=no_inbois).first()
    
    @classmethod
    def find_by_feedback(cls, kontraktor):
        return cls.query.filter_by(kontraktor=kontraktor).first()

class OmpBaru(db.Model):
    __tablename__= "omp_baru"
    omp_id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    kodarea = db.Column(db.String(20), nullable=True)
    lokasi = db.Column(db.String(500), nullable=True)
    parlimen = db.Column(db.String(20), nullable=True)
    parlimen_subarea = db.Column(db.String(255), nullable=True)
    kordinat = db.Column(db.String(255), nullable=True)
    jumlah_unit_premis = db.Column(db.String(255), nullable=True)
    kekerapan_kutipan_sisa_domestik = db.Column(db.String(255), nullable=True)
    kekerapan_kutipan_sampah_pukal = db.Column(db.String(255), nullable=True)
    kekerapan_kutipan_sampah_haram = db.Column(db.String(255), nullable=True)
    ukuran_panjang_sapuan_jalan = db.Column(db.String(255), nullable=True)
    ukuran_panjang_sapuan_TPKK = db.Column(db.String(255), nullable=True)
    ukuran_panjang_sapuan_kewlapangparkir = db.Column(db.String(255), nullable=True)
    ukuran_panjang_jejantas_sapuan = db.Column(db.String(255), nullable=True)
    ukuran_panjang_jejantas_cucian = db.Column(db.String(255), nullable=True)
    ukuran_panjang_cucian_siarkaki = db.Column(db.String(255), nullable=True)
    ukuran_panjang_cucian_siarkaki_berbumbung = db.Column(db.String(255), nullable=True)
    ukuran_panjang_cucian_slesenbaslteksi = db.Column(db.String(255), nullable=True)

    ukuran_panjang_cucilongkan = db.Column(db.String(255), nullable=True)
    ukuran_panjang_potongrumput = db.Column(db.String(255), nullable=True)
    ukuran_panjang_sampahkebun = db.Column(db.String(255), nullable=True)
    catatan = db.Column(db.String(255), nullable=True)
    rujuken_tarikh_serahan = db.Column(db.String(500) , nullable=True)

    tarikh_semakandi_lapangant_keadeansemata_ada = db.Column(db.String(255) , nullable=True)
    tarikh_semakandi_lapangant_keadeansemata_tiada = db.Column(db.String(255) , nullable=True)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
class DetailedMeeting(db.Model):
    __tablename__= "detailed_meeting"
    detailed_meeting_id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    kategori_mesyuarat = db.Column(db.String(50))
    kekerapan_mesyuarat = db.Column(db.String(20))
    jenis_mesyuarat = db.Column(db.String(40))
    jabatan_terlibat = db.Column(db.String(50))
    tarikh_mesyuarat = db.Column(db.Date)
    masa_mesyuarat = db.Column(db.String(10))
    hingga = db.Column(db.String(50))
    pengerusi = db.Column(db.String(40))
    bill_mesyuarat = db.Column(db.String(50))
    tajuk_mesyuarat = db.Column(db.String(100))
    setiausaha = db.Column(db.String(30))
    tempat_mesyuarat = db.Column(db.String(100))
    agenda_dan_minit = db.Column(db.String(50))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
class InventoriPengguna(db.Model):
    __tablename__ = "inventori_pengguna"
    inventori_pengguna_id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    nama_pengguna = db.Column(db.String(50))
    id_pengguna = db.Column(db.String(50), unique=True)
    kata_laluan = db.Column(db.String(100))
    peranan = db.Column(db.String(10))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
class LogPengguna(db.Model):
    __tablename__ = 'log_pengguna'
    log_pengguna_id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    id_pengguna = db.Column(db.String(50), db.ForeignKey('inventori_pengguna.id_pengguna', ondelete="CASCADE") )
    tarikh = db.Column(db.Date)
    masa_masuk = db.Column(db.String(10))
    masa_keluar = db.Column(db.String(10))
    aktiviti = db.Column(db.String(50))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)

class OmpLama(db.Model):
    __tablename__ = 'omp_lama'
    omp_lama_id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    parlimen_name = db.Column(db.String(100))
    kod_kekerapan_kutipan = db.Column(db.String(100))
    pembersihan = db.Column(db.String(100))
        
class OfficersList(db.Model):
    __tablename__= "officers" 
    officer_id=db.Column(db.Integer, primary_key=True)
    id_mtb=db.Column(db.String(20), nullable=True)
    parlimen=db.Column(db.String(30), nullable=True)
    tarikh=db.Column(db.Date, unique=True, nullable=False)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
    
    @classmethod
    def find_by_inspection_id(cls, inspection_id):
        return cls.query.filter_by(inspection_id=inspection_id).all()


class InquiryInformation(db.Model):
    __tablename__= "inquiry_information" 
    inquiry_information_id=db.Column(db.Integer, primary_key=True)
    tarikh=db.Column(db.Date, db.ForeignKey('officers.tarikh', ondelete="CASCADE"))
    id_mtb=db.Column(db.String(20), nullable=True)
    masa=db.Column(db.String(10), nullable=True)
    parlimen=db.Column(db.String(30), nullable=True)
    lokasi_aduan=db.Column(db.String(30), nullable=True)
    lokasi_siasatan=db.Column(db.String(50), nullable=True)
    borang_siasatan=db.Column(db.String(30), nullable=True)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
    @classmethod
    def find_by_tarikh(cls, tarikh):
        return cls.query.filter_by(tarikh=tarikh).all()
    
class ComplaintInvestigation(db.Model):
    __tablename__= "complaint_investigation"
    form_id= db.Column(db.Integer, primary_key=True, autoincrement=True) 
    tarikh=db.Column(db.Date, db.ForeignKey('officers.tarikh', ondelete="CASCADE"))
    pengadu_nama=db.Column(db.String(100))
    pengadu_alamat=db.Column(db.String(500))
    no_telefon=db.Column(db.String(100))
    tarikh_terima_aduan=db.Column(db.Date)
    no_rujukan=db.Column(db.String(100))
    emel=db.Column(db.String(100))
    no_faksimili=db.Column(db.String(100))
    sumber_aduan=db.Column(db.String(100))
    tarikh_aduan=db.Column(db.Date)
    tarikh_terima=db.Column(db.Date)
    lokasi_aduan=db.Column(db.String(100))
    keterangan_aduan=db.Column(db.String(100))
    tarikh_siasatan=db.Column(db.Date)
    masa_siasatan=db.Column(db.String(100))
    nama_pegawai=db.Column(db.String(100))
    id_mtb=db.Column(db.String(20))
    lokasi_siasatan=db.Column(db.String(500))
    laporan_siasatan=db.Column(db.String(500))
    tindakan=db.Column(db.String(500))
    susulan=db.Column(db.String(500))
    ullasan_penyelia=db.Column(db.String(500))
    ullasan_ketua_seksyen=db.Column(db.String(500))
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
class CompoundInformation(db.Model):
    __tablename__= "compound_information" 
    compound_information_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_mtb=db.Column(db.String(20))
    parlimen=db.Column(db.String(30), nullable=True)
    tarikh=db.Column(db.Date, db.ForeignKey('officers.tarikh', ondelete="CASCADE"))
    masa=db.Column(db.String(30), nullable=True)
    lokasi_kompaun=db.Column(db.String(30), nullable=True)
    no_notis_bas=db.Column(db.Integer, unique=True)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
       
class CompoundForm(db.Model):
    __tablename__= "compound_form" 
    compound_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    no_notis_bas=db.Column(db.Integer, nullable=True)
    kepada=db.Column(db.String(30), nullable=True)
    company_no=db.Column(db.String(30), nullable=True)
    alamat=db.Column(db.String(100), nullable=True)
    id_mtb=db.Column(db.String(20), nullable=True)
    parlimen=db.Column(db.String(30), nullable=True)
    lokasi_kompaun=db.Column(db.String(50), nullable=True)
    akta_jalan=db.Column(db.Boolean, nullable=True)
    undang_kecil_permungutan=db.Column(db.Boolean, nullable=True)
    undang_kecil_pelesenan=db.Column(db.Boolean, nullable=True)
    undang_pelesenan_penjaja=db.Column(db.Boolean, nullable=True)
    undang_kecil_larangan_meludah=db.Column(db.Boolean, nullable=True)
    butir_butir_kesalahan=db.Column(db.String(100), nullable=True)
    tarikh=db.Column(db.Date, nullable=True)
    waktu=db.Column(db.String(50), nullable=True)
    tempat=db.Column(db.String(50), nullable=True)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
 
class Notice(db.Model):
    __tablename__= "notice" 
    notice_id=db.Column(db.Integer, primary_key=True)
    id_mtb=db.Column(db.String(30), nullable=True)
    nama_pegawai_merinyu=db.Column(db.String(30), nullable=True)      
    lokasi_merinyu=db.Column(db.String(30), nullable=True)      
    gambar_lokasi_kerja_photo1=db.Column(db.String(50), nullable=True)      
    gambar_lokasi_kerja_photo2=db.Column(db.String(50), nullable=True)      
    gambar_lokasi_kerja_photo3=db.Column(db.String(50), nullable=True)      
    status_tindakan=db.Column(db.String(30), nullable=True) 
    kontraktor_emel=db.Column(db.String(30), nullable=True) 
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)     
    
class GrafPrestasiBulanan(db.Model):
    __tablename__ = "graf_prestasi_bulanan"
    graf_prestasi_bulanan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pegawai_merinyu = db.Column(db.String(30), unique=True)
    parlimen = db.Column(db.String(30))
    nama_pegawai = db.Column(db.String(30))
    sub_area = db.Column(db.String(30))
    year = db.Column(db.Integer)
    jan_count = db.Column(db.Integer)
    feb_count = db.Column(db.Integer)
    mac_count = db.Column(db.Integer)
    april_count = db.Column(db.Integer)
    mei_count = db.Column(db.Integer)
    jun_count = db.Column(db.Integer)
    julai_count = db.Column(db.Integer)
    ogos_count = db.Column(db.Integer)
    sept_count = db.Column(db.Integer)
    okt_count = db.Column(db.Integer)
    nos_count = db.Column(db.Integer)
    dis_count = db.Column(db.Integer)
    inserted_date = db.Column(db.Date , nullable=True)
    updated_date = db.Column(db.Date , nullable=True)
    inserted_by = db.Column(db.String(30), nullable=True)
    updated_by = db.Column(db.String(30), nullable=True)
    active = db.Column(db.Boolean, default=1)
    
class Coordinates(db.Model):
    __tablename__ = "coordinates"
    coordinate_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lokasi = db.Column(db.String(800), nullable=True)
    parlimen = db.Column(db.String(255), nullable=True)
    taman = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.String(60), nullable=True)
    longitude = db.Column(db.String(60), nullable=True)
    parlimen_subarea = db.Column(db.String(500), nullable=True)
    jumlah_unit_premis = db.Column(db.String(500), nullable=True)
    kekerapan_kutipan_sisa_domestik = db.Column(db.String(500), nullable=True)
    kekerapan_kutipan_sampah_pukal = db.Column(db.String(500), nullable=True)
    kekerapan_kutipan_sampah_haram = db.Column(db.String(500), nullable=True)
    ukuran_panjang_sapuan_jalan = db.Column(db.String(500), nullable=True)
    ukuran_panjang_sapuan_TPKK = db.Column(db.String(500), nullable=True)
    ukuran_panjang_sapuan_kewlapangparkir = db.Column(db.String(500), nullable=True)
    ukuran_panjang_jejantas_sapuan = db.Column(db.String(500), nullable=True)
    ukuran_panjang_jejantas_cucian = db.Column(db.String(500), nullable=True)
    ukuran_panjang_cucian_siarkaki = db.Column(db.String(500), nullable=True)
    ukuran_panjang_cucian_siarkaki_berbumbung = db.Column(db.String(500), nullable=True)
    ukuran_panjang_cucian_slesenbaslteksi = db.Column(db.String(500), nullable=True)
    ukuran_panjang_cucilongkan = db.Column(db.String(500), nullable=True)
    ukuran_panjang_potongrumput = db.Column(db.String(500), nullable=True)
    ukuran_panjang_sampahkebun = db.Column(db.String(500), nullable=True)
    catatan = db.Column(db.String(500), nullable=True)
    rujuken_tarikh_serahan = db.Column(db.String(500), nullable=True)
    tarikh_semakandi_lapangant_keadeansemata_ada = db.Column(db.String(500), nullable=True)
    tarikh_semakandi_lapangant_keadeansemata_tiada = db.Column(db.String(500), nullable=True)
    active = db.Column(db.Boolean, default=1)
      
class OtpStore(db.Model):
    __tablename__= "otp" 
    id=db.Column(db.Integer, primary_key=True)
    no_kad_pengenalan=db.Column(db.String(30), nullable=True)
    nama_pengguna=db.Column(db.String(30), nullable=True)
    otp=db.Column(db.String(20), nullable=True)
    name=db.Column(db.String(30), nullable=True)
    email=db.Column(db.String(30), nullable=True)
    psswd=db.Column(db.String(50), nullable=True)
    
    @classmethod
    def find_by_id_card_no(cls, no_kad_pengenalan):
        return cls.query.filter_by(no_kad_pengenalan=no_kad_pengenalan).first()
    
    @classmethod
    def find_by_nama_pengguna(cls, nama_pengguna):
        return cls.query.filter_by(nama_pengguna=nama_pengguna).first()
    
class Log(db.Model):
    __tablename__= "log"
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    statement = db.Column(db.String(500), nullable=True)
    date = db.Column(db.Date , nullable=True)
    user_name = db.Column(db.String(50), nullable=True)