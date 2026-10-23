from rest_framework import serializers
from .models import AvailabilitySlot, Booking


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = ["id", "doctor", "date", "start_time", "end_time", "is_booked"]
        read_only_fields = ["id", "doctor", "is_booked"]


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "patient", "slot", "created_at"]
        read_only_fields = ["id", "patient", "created_at"]
