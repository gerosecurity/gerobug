from django import forms
from ckeditor.widgets import CKEditorWidget



class Requestform(forms.Form):
    reasons = forms.CharField(widget=forms.Textarea(attrs={"id":"reasons","name":"reasons","placeholder":"Write the reason here ..."}),required=True)

class CompleteRequestform(forms.Form):
    completereasons = forms.CharField(widget=forms.Textarea(attrs={"id":"completereasons","name":"completereasons","placeholder":"Write the reason here ..."}),required=True)

class AdminSettingForm(forms.Form):
    RDP = forms.CharField(widget=CKEditorWidget(attrs={"id": "rdp"}))
    bountyterms = forms.CharField(widget=CKEditorWidget(attrs={"id": "bountyterms"}))
    inscope = forms.CharField(widget=CKEditorWidget(attrs={"id": "inscope"}))
    outofscope = forms.CharField(widget=CKEditorWidget(attrs={"id": "outofscope"}))
    reportguidelines = forms.CharField(widget=CKEditorWidget(attrs={"id": "reportguidelines"}))
    faq = forms.CharField(widget=CKEditorWidget(attrs={"id": "faq"}))

class MailboxForm(forms.Form):
    mailbox_email = forms.CharField(widget=forms.EmailInput(attrs={'id':'mailbox_email', 'placeholder': 'Email', 'style': 'width: 100%;', 'class': 'form-control'}))
    mailbox_password = forms.CharField(widget=forms.PasswordInput(attrs={'id':'mailbox_password', 'placeholder': 'Password', 'style': 'width: 100%;', 'class': 'form-control'}))

class AccountForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'id':'username', 'placeholder': 'Username', 'style': 'width: 100%;', 'class': 'form-control'}))
    user_email = forms.CharField(widget=forms.EmailInput(attrs={'id':'user_email', 'placeholder': 'Email', 'style': 'width: 100%;', 'class': 'form-control'}))
    user_password = forms.CharField(widget=forms.PasswordInput(attrs={'id':'user_password', 'placeholder': 'Password', 'style': 'width: 100%;', 'class': 'form-control'}))