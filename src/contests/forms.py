from django import forms
from django.contrib.auth.models import User


class SubmitSolutionForm(forms.Form):
    file = forms.FileField()


class SubmitSabotageSolutionForm(forms.Form):
    answer = forms.CharField(required=True)


class CloseSubmissionForm(forms.Form):
    def __init__(self, user_ids, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["users"].queryset = User.objects.filter(id__in=user_ids)

    users = forms.ModelMultipleChoiceField(queryset=User.objects.all())


class CreateSabotageForm(forms.Form):
    def __init__(self, user_ids, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["users"].queryset = User.objects.filter(id__in=user_ids)

    users = forms.ModelMultipleChoiceField(queryset=User.objects.all())


class LoginForm(forms.Form):
    login = forms.CharField(max_length=100)

    password = forms.CharField(widget=forms.PasswordInput(), max_length=100)


class ProfileForm(forms.Form):
    team_name = forms.CharField(max_length=100, required=True)

    members = forms.CharField(max_length=200, required=True)
