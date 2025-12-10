# core/utils.py
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import os


def generate_qr_code(data, filename):
    """
    Generate a QR code and save it as an image file
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to Django File
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return File(buffer, name=f'{filename}.png')


def generate_tutor_qr_code(tutor):
    """
    Generate QR code for tutor profile
    """
    data = f"""
    Tutor: {tutor.user.get_full_name()}
    Subject: {tutor.get_primary_subject_display()}
    Rate: KSH {tutor.hourly_rate}/hr
    Contact: {tutor.user.email}
    Platform: Campus Essentials Hub
    Profile: https://yourdomain.com/tutoring/{tutor.id}/
    """

    filename = f'tutor_{tutor.id}_qr'
    qr_file = generate_qr_code(data, filename)

    # Save to tutor model
    tutor.qr_code.save(f'{filename}.png', qr_file, save=True)
    return tutor.qr_code.url


def generate_service_qr_code(service):
    """
    Generate QR code for service
    """
    data = f"""
    Service: {service.name}
    Category: {service.get_category_display()}
    Location: {service.location}
    Contact: {service.contact_number}
    Hours: {service.opening_hours}
    Platform: Campus Essentials Hub
    Profile: https://yourdomain.com/services/{service.id}/
    """

    filename = f'service_{service.id}_qr'
    qr_file = generate_qr_code(data, filename)

    service.qr_code.save(f'{filename}.png', qr_file, save=True)
    return service.qr_code.url