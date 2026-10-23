from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import AvailabilitySlot, Booking
from datetime import date, time

User = get_user_model()


class BookingFlowTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(username='doc1', password='pass123', role='DOCTOR')
        self.patient = User.objects.create_user(username='pat1', password='pass123', role='PATIENT')

    def test_slot_creation_and_booking(self):
        slot = AvailabilitySlot.objects.create(
            doctor=self.doctor,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        self.assertFalse(slot.is_booked)

        booking = Booking.objects.create(patient=self.patient, slot=slot)
        slot.is_booked = True
        slot.save()

        self.assertTrue(Booking.objects.filter(patient=self.patient).exists())
        self.assertTrue(AvailabilitySlot.objects.get(id=slot.id).is_booked)

    def test_doctor_dashboard_shows_empty_appointments_state(self):
        self.client.force_login(self.doctor)

        response = self.client.get("/doctor/dashboard/")

        self.assertContains(response, "My Appointments")
        self.assertContains(response, "No appointments yet.")

    def test_doctor_dashboard_lists_booked_appointments(self):
        slot = AvailabilitySlot.objects.create(
            doctor=self.doctor,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_booked=True,
        )
        Booking.objects.create(patient=self.patient, slot=slot)
        self.client.force_login(self.doctor)

        response = self.client.get("/doctor/dashboard/")

        self.assertContains(response, self.patient.username)
        self.assertNotContains(response, "No appointments yet.")
from django.test import TestCase

# Create your tests here.
