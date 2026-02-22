from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True, label="Your Name")
    email = forms.EmailField(required=True, label="Your Email")
    message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=True,
        label="Message"
    )