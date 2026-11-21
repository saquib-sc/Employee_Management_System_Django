from django import forms
from django.contrib.auth.models import User
from .models import EmployeeGroup, EmployeeProfile, Notification, Project


class EmployeeCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    job_title = forms.CharField(max_length=120, required=False)
    department = forms.CharField(max_length=120, required=False)
    phone = forms.CharField(max_length=30, required=False)
    group = forms.ModelChoiceField(
        queryset=EmployeeGroup.objects.all(), required=False
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username


class EmployeeEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    job_title = forms.CharField(max_length=120, required=False)
    department = forms.CharField(max_length=120, required=False)
    phone = forms.CharField(max_length=30, required=False)
    group = forms.ModelChoiceField(
        queryset=EmployeeGroup.objects.all(), required=False
    )


class EmployeeGroupForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_staff=False, is_superuser=False),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = EmployeeGroup
        fields = ["name", "description", "members"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["members"].initial = User.objects.filter(
                employee_profile__group=self.instance
            )

    def save(self, commit=True):
        group = super().save(commit=commit)
        if commit:
            selected_users = set(self.cleaned_data.get("members", []))
            for profile in EmployeeProfile.objects.filter(group=group):
                if profile.user not in selected_users:
                    profile.group = None
                    profile.save()
            for user in selected_users:
                profile, _ = EmployeeProfile.objects.get_or_create(user=user)
                profile.group = group
                profile.save()
        return group


class ProjectForm(forms.ModelForm):
    assigned_employees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_staff=False, is_superuser=False),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    assigned_groups = forms.ModelMultipleChoiceField(
        queryset=EmployeeGroup.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "status",
            "assigned_employees",
            "assigned_groups",
        ]


class NotificationForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False, is_superuser=False)
    )

    class Meta:
        model = Notification
        fields = ["recipient", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3}),
        }