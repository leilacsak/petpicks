from pathlib import Path

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Div
from django import forms
from django.core.exceptions import ValidationError
from PIL import Image

from .models import Comment, Entry, LotteryRound


ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


class EntryCreateForm(forms.ModelForm):
    AGE_NUMBER_CHOICES = [(i, str(i)) for i in range(1, 101)]
    AGE_UNIT_CHOICES = [
        ('year(s)', 'year(s)'),
        ('month(s)', 'month(s)'),
        ('week(s)', 'week(s)'),
    ]
    
    pet_name = forms.CharField(max_length=50, label="Pet name", required=True)
    pet_breed = forms.CharField(max_length=50, required=True, label="Breed")
    pet_age_number = forms.ChoiceField(
        choices=AGE_NUMBER_CHOICES,
        label="Age",
        required=True
    )
    pet_age_unit = forms.ChoiceField(
        choices=AGE_UNIT_CHOICES,
        label="",
        required=True
    )

    class Meta:
        model = Entry
        fields = ["photo"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['pet_age_number'].widget.attrs.update({
            'class': 'form-select',
            'style': 'width: auto; display: inline-block;'
        })
        self.fields['pet_age_unit'].widget.attrs.update({
            'class': 'form-select',
            'style': 'width: auto; display: inline-block;'
        })

    def clean(self):
        cleaned_data = super().clean()
        age_number = cleaned_data.get("pet_age_number")
        age_unit = cleaned_data.get("pet_age_unit")
        
        if age_number and age_unit:
            # Combine into a single age string like "2 year(s)"
            cleaned_data["pet_age"] = f"{age_number} {age_unit}"
        
        return cleaned_data

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo:
            raise forms.ValidationError(
                "A photo is required to enter the draw."
            )

        extension = Path(photo.name).suffix.lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError("Only JPG, PNG, and WEBP files are allowed.")

        if photo.size > MAX_UPLOAD_SIZE:
            raise ValidationError("Image file too large (max 5 MB).")

        try:
            image = Image.open(photo)
            image.verify()
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError(
                    "Only JPG, PNG, and WEBP files are allowed."
                )
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(
                "Upload a valid image file (JPG, PNG, or WEBP)."
            ) from exc
        finally:
            photo.seek(0)

        return photo


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        labels = {
            "text": "Comment:",
        }
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Write a congratulatory comment...",
                }
            )
        }

    def clean_text(self):
        text = self.cleaned_data.get("text", "").strip()
        if not text:
            raise ValidationError("Comment cannot be empty.")
        return text


class LotteryRoundForm(forms.ModelForm):
    class Meta:
        model = LotteryRound
        fields = ["title", "start_date", "end_date"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "e.g., February 2026 Draw"}
            ),
            "start_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "end_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date.")
        
        return cleaned_data
