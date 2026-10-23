from django.urls import path
from . import views

urlpatterns = [
    # Doctor
    path("doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("doctor/create-slot/", views.create_slot_page, name="create_slot"),

    # Patient
    path("patient/dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path("patient/slots/", views.patient_slots_page, name="patient_slots"),
    path("patient/book/<int:slot_id>/", views.book_slot, name="book_slot"),
    path("patient/cancel/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
    path("doctors/", views.doctors_list, name="doctors_list"),
    path("doctors/<int:doctor_id>/slots/", views.doctor_slots, name="doctor_slots"),
]
