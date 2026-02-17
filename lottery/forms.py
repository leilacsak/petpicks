from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from PIL import Image

from .models import Comment, Entry


ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024


class EntryCreateForm(forms.ModelForm):
    pet_name = forms.CharField(max_length=50, label="Pet name", required=True)
    pet_breed = forms.CharField(max_length=50, required=True, label="Breed")
    pet_age = forms.IntegerField(min_value=0, label="Age", required=True)

    class Meta:
        model = Entry
        fields = ["photo"]

    def clean_pet_age(self):
        age = self.cleaned_data["pet_age"]
        if age < 0:
            raise forms.ValidationError("Age must be 0 or higher.")
        return age

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
