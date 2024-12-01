from django.urls import path
from scanner.views import generate_qr,scan_qr
urlpatterns = [
    path('genrate/',generate_qr,name="genrate"),
     path('scan/',scan_qr,name="scan")
 ]
