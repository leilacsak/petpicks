from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        label="Your Name",
        widget=forms.TextInput(attrs={"autocomplete": "name"})
    )
    email = forms.EmailField(
        required=True,
        label="Your Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "autocomplete": "message"}),
        required=True,
        label="Message"
    )