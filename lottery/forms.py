from django import forms
from .models import Entry


class EntryCreateForm(forms.ModelForm):
    pet_name = forms.CharField(max_length=50, label="Pet name")
    pet_breed = forms.CharField(max_length=50, required=False, label="Breed")
    pet_age = forms.IntegerField(min_value=0, label="Age")

    class Meta:
        model = Entry
        fields = ["photo"]

    def clean_pet_age(self):
        age = self.cleaned_data["pet_age"]
        if age < 0:
            raise forms.ValidationError("Age must be 0 or higher.")
        return age
