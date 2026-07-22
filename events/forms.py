from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Comment, Event, UserProfile


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_class + " form-control").strip()


class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email address is already registered.")
        return email

class CustomPasswordResetForm(BootstrapFormMixin, PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter your registered email",
                "autocomplete": "email",
            }
        )
    )
    
class EventForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "category",
            "title",
            "organizer",
            "description",
            "location",
            "start_datetime",
            "end_datetime",
            "capacity",
            "poster",
            "is_published",
        ]
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["poster"].widget.attrs.update({"accept": ".jpg,.jpeg,.png,.webp"})

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get("start_datetime")
        end_datetime = cleaned_data.get("end_datetime")
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            self.add_error("end_datetime", "End time must be later than start time.")
        return cleaned_data

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity is not None and capacity <= 0:
            raise ValidationError("Capacity must be greater than zero.")
        return capacity

    def clean_poster(self):
        poster = self.cleaned_data.get("poster")
        if not poster:
            return poster
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        extension = poster.name.lower().rsplit(".", 1)[-1]
        if f".{extension}" not in allowed_extensions:
            raise ValidationError("Poster must be a JPG, JPEG, PNG, or WEBP image.")
        if poster.size > 5 * 1024 * 1024:
            raise ValidationError("Poster image must be 5 MB or smaller.")
        return poster


class CommentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4, "maxlength": 1000})}

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise ValidationError("Comment cannot be blank.")
        if len(body) > 1000:
            raise ValidationError("Comment must be 1,000 characters or fewer.")
        return body


class UserProfileForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = [
            "student_id",
            "program",
            "bio",
            "profile_picture",
            "preferred_category",
            "email_notifications",
        ]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
        self.fields["profile_picture"].widget.attrs.update({"accept": ".jpg,.jpeg,.png,.webp"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if self.user and User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")
        if not picture:
            return picture
        extension = picture.name.lower().rsplit(".", 1)[-1]
        if f".{extension}" not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValidationError("Profile picture must be a JPG, JPEG, PNG, or WEBP image.")
        if picture.size > 5 * 1024 * 1024:
            raise ValidationError("Profile picture must be 5 MB or smaller.")
        return picture

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get("first_name", "").strip()
            self.user.last_name = self.cleaned_data.get("last_name", "").strip()
            self.user.email = self.cleaned_data.get("email", "").strip().lower()
            if commit:
                self.user.save()
            profile.user = self.user
        if commit:
            profile.save()
        return profile


class ContactForm(BootstrapFormMixin, forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=150)
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}))
