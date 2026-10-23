from django import forms
from .models import AvailabilitySlot
from django.core.exceptions import ValidationError
from datetime import datetime


class SlotForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = ["date", "start_time", "end_time"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
        }

    def clean(self):
        cleaned = super().clean()

        # Accept common date formats from user input (e.g. 27/01/2026 or 2026-01-27)
        if cleaned.get("date") in (None, ""):
            # try to parse raw input if automatic parsing failed
            raw_key = self.add_prefix("date")
            raw_date = self.data.get(raw_key) or self.data.get("date")
            if raw_date:
                for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                    try:
                        parsed = datetime.strptime(raw_date, fmt).date()
                        cleaned["date"] = parsed
                        break
                    except Exception:
                        continue
                else:
                    raise ValidationError({"date": "Enter a valid date."})
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and start >= end:
            raise forms.ValidationError("End time must be after start time")
        return cleaned
