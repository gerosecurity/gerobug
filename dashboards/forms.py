from django import forms
from ckeditor.widgets import CKEditorWidget



class Requestform(forms.Form):
    reasons = forms.CharField(widget=forms.Textarea(attrs={"id":"reasons","name":"reasons","placeholder":"Write the reason here ..."}),required=True)

class CompleteRequestform(forms.Form):
    completereasons = forms.CharField(widget=forms.Textarea(attrs={"id":"completereasons","name":"completereasons","placeholder":"Write the reason here ..."}),required=True)

class AdminSettingForm(forms.Form):
    RDP = forms.CharField(widget=CKEditorWidget(attrs={"id": "rdp"}),label="Responsible Disclosure Policy")
    bountyterms = forms.CharField(widget=CKEditorWidget(attrs={"id": "bountyterms"}),label="Bounty Terms")
    inscope = forms.CharField(widget=CKEditorWidget(attrs={"id": "inscope"}),label="In Scope")
    outofscope = forms.CharField(widget=CKEditorWidget(attrs={"id": "outofscope"}),label="Out of Scope")
    reportguidelines = forms.CharField(widget=CKEditorWidget(attrs={"id": "reportguidelines"}),label="Report Guidelines")
    faq = forms.CharField(widget=CKEditorWidget(attrs={"id": "faq"}),label="Frequenly Asked Questions")

class MailboxForm(forms.Form):
    mailbox_email = forms.CharField(widget=forms.EmailInput(attrs={'id':'mailbox_email', 'placeholder': 'Email', 'style': 'width: 100%;', 'class': 'form-control'}))
    mailbox_password = forms.CharField(widget=forms.PasswordInput(attrs={'id':'mailbox_password', 'placeholder': 'Password', 'style': 'width: 100%;', 'class': 'form-control'}))

class AccountForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'id':'username', 'placeholder': 'Username', 'style': 'width: 100%;', 'class': 'form-control'}))
    user_email = forms.CharField(widget=forms.EmailInput(attrs={'id':'user_email', 'placeholder': 'Email', 'style': 'width: 100%;', 'class': 'form-control'}))
    user_password = forms.CharField(widget=forms.PasswordInput(attrs={'id':'user_password', 'placeholder': 'Password', 'style': 'width: 100%;', 'class': 'form-control'}))

class ReviewerForm(forms.Form):
    reviewername = forms.CharField(widget=forms.TextInput(attrs={'id':'reviewername', 'placeholder': 'Reviewer\'s Username', 'style': 'width: 100%;', 'class': 'form-control'}),label="Reviewer's Name")
    reviewer_email = forms.CharField(widget=forms.EmailInput(attrs={'id':'reviewer_email', 'placeholder': 'Reviewer\'s Email', 'style': 'width: 100%;', 'class': 'form-control'}),label="Reviewer's Email")

class WebhookForm(forms.Form):
    CHOICES = (('SLACK', 'Slack'),('TELEGRAM', 'Telegram'),)
    webhook_service = forms.ChoiceField(choices=CHOICES,label="Notification Channel")
    webhook_handle = forms.CharField(widget=forms.URLInput(attrs={'id':'webhook_handle', 'placeholder': 'Webhook URL', 'style': 'width: 100%;', 'class': 'form-control'}),label="Webhook URL")