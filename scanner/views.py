from django.shortcuts import render,redirect
import qrcode
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
from scanner.models import QRCode
from pyzbar.pyzbar import decode
from PIL import Image
def generate_qr(request):
    qr_image_url=None
    if request.method == "POST":
        mobile_number=request.POST.get('mobile_number')
        data=request.POST.get('qr-data')
        if not mobile_number or len(mobile_number) != 11 or not mobile_number.isdigit():
          return render(request,'scanner/generate.html',
                        {'error':'Invalid Mobile number'})
        qr_content=f"{data}|{mobile_number}"
        qr=qrcode.make(qr_content)
        qr_image_io=BytesIO()
        qr.save(qr_image_io,format='PNG')
        qr_image_io.seek(0)
        qr_storage_path=settings.MEDIA_ROOT/'qr_codes'
        fs=FileSystemStorage(location=qr_storage_path,
                             base_url='/media/qr_codes/')
        file_name=f"{data}_{mobile_number}.png"
        qr_image_content=ContentFile(qr_image_io.read(),
                                     name=file_name)
        file_path=fs.save(file_name,qr_image_content)
        qr_image_url=fs.url(file_name)
        QRCode.objects.create(data=data,mobile_number=mobile_number)
    return render(request,"scanner/generate.html",{'qr_image_url':qr_image_url})
def scan_qr(request):
    result = None
    if request.method == "POST" and request.FILES.get('qr_image'):
        mobile_number = request.POST.get('mobile_number')
        qr_image = request.FILES['qr_image']

        # Validate mobile number
        if not mobile_number or len(mobile_number) != 11 or not mobile_number.isdigit():
            return render(request, 'scanner/scanner.html', {'error': 'Invalid Mobile number'})

        # Save the uploaded file
        fs = FileSystemStorage()
        filename = fs.save(qr_image.name, qr_image)
        image_path = Path(fs.location) / filename

        try:
            # Open the image and decode QR code
            image = Image.open(image_path)
            decoded_objects = decode(image)
            if decoded_objects:
                # Extract QR content
                qr_content = decoded_objects[0].data.decode('utf-8').strip()
                qr_data, qr_mobile_number = qr_content.split('|')

                # Check against the database
                qr_entry = QRCode.objects.filter(data=qr_data, mobile_number=qr_mobile_number).first()
                if qr_entry and qr_mobile_number == mobile_number:
                    result = "Scan Success: Valid QR code for the provided mobile number"
                    qr_entry.delete()  # Optional: Delete entry after successful scan

                    # Delete the QR image from storage
                    qr_image_path = settings.MEDIA_ROOT / 'qr_codes' / f"{qr_data}_{qr_mobile_number}.png"
                    if qr_image_path.exists():
                        qr_image_path.unlink()
                    if image_path.exists():
                        image_path.unlink()

                else:
                    result = "Scan Failed: Invalid mobile number or QR code mismatch"
            else:
                result = "No QR code detected in the image"
        except Exception as e:
            result = f"Error processing the image: {str(e)}"
        finally:
            # Clean up: Remove the uploaded file
            if image_path.exists():
                image_path.unlink()

    return render(request, "scanner/scanner.html", {'result': result})
