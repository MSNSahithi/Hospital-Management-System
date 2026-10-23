from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from .models import AvailabilitySlot, Booking
from accounts_app.models import User
from .forms import SlotForm
from notifications.email_client import send_email


# ---------------- DOCTOR DASHBOARD ----------------
@login_required(login_url="/doctor/login/")
def doctor_dashboard(request):
    if getattr(request.user, "role", "").upper() != "DOCTOR":
        messages.error(request, "Only doctors can access doctor dashboard")
        return redirect("/")

    slots = AvailabilitySlot.objects.filter(doctor=request.user).order_by("-date")
    appointments = (
        Booking.objects.filter(slot__doctor=request.user)
        .select_related("patient", "slot")
        .order_by("slot__date", "slot__start_time")
    )
    return render(
        request,
        "doctor_dashboard.html",
        {"slots": slots, "appointments": appointments},
    )


# ---------------- CREATE SLOT PAGE ----------------
@login_required(login_url="/doctor/login/")
def create_slot_page(request):
    if getattr(request.user, "role", "").upper() != "DOCTOR":
        messages.error(request, "Only doctors can create slots")
        return redirect("/")
    if request.method == "POST":
        form = SlotForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data["date"]
            start_time = form.cleaned_data["start_time"]
            end_time = form.cleaned_data["end_time"]

            overlap = AvailabilitySlot.objects.filter(
                doctor=request.user,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time,
            ).exists()

            if overlap:
                messages.error(request, "This slot overlaps an existing slot")
            else:
                AvailabilitySlot.objects.create(
                    doctor=request.user,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                )
                messages.success(request, "Slot created successfully ✅")
                return redirect("/doctor/dashboard/")
    else:
        form = SlotForm()

    return render(request, "create_slot.html", {"form": form})


# ---------------- PATIENT DASHBOARD ----------------
@login_required(login_url="/patient/login/")
def patient_dashboard(request):
    if getattr(request.user, "role", "").upper() != "PATIENT":
        messages.error(request, "Only patients can access patient dashboard")
        return redirect("/")

    bookings = Booking.objects.filter(patient=request.user).select_related("slot").order_by("-created_at")
    return render(request, "patient_dashboard.html", {"bookings": bookings})


# ---------------- PATIENT VIEW AVAILABLE SLOTS ----------------
@login_required(login_url="/patient/login/")
def patient_slots_page(request):
    if getattr(request.user, "role", "").upper() != "PATIENT":
        messages.error(request, "Only patients can view slots")
        return redirect("/")

    slots = AvailabilitySlot.objects.filter(is_booked=False).order_by("date", "start_time")
    return render(request, "patient_slots.html", {"slots": slots})


@login_required(login_url="/patient/login/")
def doctors_list(request):
    if getattr(request.user, "role", "").upper() != "PATIENT":
        messages.error(request, "Only patients can search for doctors")
        return redirect('/')
    doctors = User.objects.filter(role__iexact="DOCTOR")
    return render(request, "doctors_list.html", {"doctors": doctors})


@login_required(login_url="/patient/login/")
def doctor_slots(request, doctor_id):
    if getattr(request.user, "role", "").upper() != "PATIENT":
        messages.error(request, "Only patients can view doctor slots")
        return redirect('/')
    doctor = get_object_or_404(User, id=doctor_id, role__iexact="DOCTOR")
    slots = AvailabilitySlot.objects.filter(doctor=doctor, is_booked=False).order_by("date", "start_time")
    return render(request, "doctor_slots.html", {"doctor": doctor, "slots": slots})


# ---------------- BOOK SLOT ----------------
def book_slot(request, slot_id):
    # Handle unauthenticated AJAX requests with JSON 401, otherwise redirect to login
    if not request.user.is_authenticated:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "login_required"}, status=401)
        return redirect("/patient/login/")

    if getattr(request.user, "role", "").upper() != "PATIENT":
        messages.error(request, "Only patients can book slots")
        return redirect("/")

    # Only accept POST for booking
    if request.method != "POST":
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
        return redirect("/patient/slots/")

    slot = get_object_or_404(AvailabilitySlot, id=slot_id)

    # Log request context for debugging
    try:
        logger.debug("book_slot called: user=%s authenticated=%s slot_id=%s method=%s headers=%s",
                     getattr(request.user, 'username', None), request.user.is_authenticated, slot_id, request.method,
                     {k: v for k, v in request.headers.items() if k.lower() in ['x-requested-with', 'x-csrftoken']})

        # Perform booking in a transaction to avoid race conditions
        with transaction.atomic():
            slot_for_update = AvailabilitySlot.objects.select_for_update().get(id=slot.id)
            if slot_for_update.is_booked:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"status": "error", "message": "Already booked"}, status=400)
                messages.error(request, "This slot is already booked ❌")
                return redirect("/patient/slots/")

            booking = Booking.objects.create(patient=request.user, slot=slot_for_update)
            slot_for_update.is_booked = True
            slot_for_update.save()

    except AvailabilitySlot.DoesNotExist:
        logger.exception("Slot does not exist during booking: %s", slot_id)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "Selected slot no longer exists"}, status=404)
        messages.error(request, "Selected slot no longer exists")
        return redirect("/patient/slots/")
    except Exception as e:
        logger.exception("Unexpected error in book_slot for slot %s", slot_id)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        messages.error(request, "An error occurred while booking")
        return redirect("/patient/slots/")

    # Notify via serverless email (best-effort)
    try:
        send_email("BOOKING_CONFIRMATION", {
            "to_email": request.user.email,
            "doctor_email": slot.doctor.email,
            "doctor": slot.doctor.username,
            "patient": request.user.username,
            "date": str(slot.date),
            "start_time": str(slot.start_time),
            "end_time": str(slot.end_time),
        })
    except Exception:
        pass

    # Create Google Calendar events for doctor and patient if connected
    calendar_update_failed = False
    try:
        from notifications.google_client import create_calendar_event
        start_iso = timezone.make_aware(
            datetime.combine(slot.date, slot.start_time),
            timezone.get_current_timezone(),
        ).isoformat()
        end_iso = timezone.make_aware(
            datetime.combine(slot.date, slot.end_time),
            timezone.get_current_timezone(),
        ).isoformat()

        if slot.doctor.google_refresh_token:
            calendar_update_failed |= create_calendar_event(
                slot.doctor.google_refresh_token,
                summary=f"Appointment with {request.user.username}",
                start_iso=start_iso,
                end_iso=end_iso,
                attendees=[request.user.email] if request.user.email else None,
                description=f"Patient: {request.user.username}",
            ) is None

        if request.user.google_refresh_token:
            calendar_update_failed |= create_calendar_event(
                request.user.google_refresh_token,
                summary=f"Appointment with Dr. {slot.doctor.username}",
                start_iso=start_iso,
                end_iso=end_iso,
                attendees=[slot.doctor.email] if slot.doctor.email else None,
                description=f"Doctor: {slot.doctor.username}",
            ) is None
    except Exception:
        logger.exception("Google Calendar update failed for booking %s", booking.pk)
        calendar_update_failed = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "status": "ok",
                "message": "Booking confirmed",
                "calendar_warning": calendar_update_failed,
            }
        )

    messages.success(request, "Booking confirmed ✅")
    if calendar_update_failed:
        messages.warning(request, "The appointment was booked, but Google Calendar could not be updated.")
    return redirect("/patient/dashboard/")


@login_required(login_url="/patient/login/")
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, patient=request.user)
    slot = booking.slot
    booking.delete()
    slot.is_booked = False
    slot.save()

    # Notify via serverless email (best-effort)
    try:
        send_email("BOOKING_CANCELLATION", {
            "to_email": request.user.email,
            "doctor_email": slot.doctor.email,
            "doctor": slot.doctor.username,
            "patient": request.user.username,
            "date": str(slot.date),
            "start_time": str(slot.start_time),
            "end_time": str(slot.end_time),
        })
    except Exception:
        pass

    messages.success(request, "Booking cancelled and slot freed")
    return redirect("/patient/dashboard/")
