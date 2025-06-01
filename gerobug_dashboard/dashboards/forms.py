from django import forms
from dashboards.models import StaticRules, Personalization
from dashboards.rulestemplate import *
from dashboards.validators import *
from django.core.validators import *
from colorfield.widgets import ColorWidget


class Requestform(forms.Form):
    reasons = forms.CharField(widget=forms.Textarea(attrs={"id":"reasons","name":"reasons","placeholder":"Explain what you need (Minimum 10 Characters)"}),validators=[MinLengthValidator(10)],required=True)

class CompleteRequestform(forms.Form):
    completereasons = forms.CharField(widget=forms.Textarea(attrs={"id":"completereasons","name":"completereasons","placeholder":"Write something inspiring (Minimum 10 Characters)"}),validators=[MinLengthValidator(10)],required=True)

class Invalidform(forms.Form):
    invalidreasons = forms.CharField(widget=forms.Textarea(attrs={"id":"invalidreasons","name":"invalidreasons","placeholder":"Please provide the reason (Minimum 10 Characters)"}),validators=[MinLengthValidator(10)],required=True)

class RulesGuidelineForm(forms.ModelForm):  
    class Meta:
        model = StaticRules
        fields = ['bountyterms', 'inscope', 'outofscope', 'RDP', 'reportguidelines', 'faq']
        labels = {
            "bountyterms": "Bounty Terms",
            "inscope": "In Scope",
            "outofscope": "Out of Scope",
            "RDP": "Responsible Disclosure Policy",
            "reportguidelines": "Report Guidelines",
            "faq": "Frequently Asked Questions"
        }

class MailboxForm(forms.Form):
    CHOICES = (('1', 'GMAIL'),('2', 'OUTLOOK'),('3', 'CUSTOM'),)
    mailbox_email = forms.CharField(widget=forms.EmailInput(attrs={'id':'mailbox_email', 'placeholder': 'Email', 'style': 'width: 100%;', 'class': 'form-control'}),label="Mailbox Email")
    mailbox_password = forms.CharField(widget=forms.PasswordInput(attrs={'id':'mailbox_password', 'placeholder': 'Password', 'style': 'width: 100%;', 'class': 'form-control'}),label="Mailbox Password")
    mailbox_type = forms.ChoiceField(choices=CHOICES,label="Email Type")
    mailbox_imap = forms.CharField(widget=forms.TextInput(attrs={'id':'mailbox_imap', 'placeholder': 'IMAP Server', 'style': 'width: 100%;', 'class': 'form-control hidden'}),label="IMAP Server")
    mailbox_imap_port = forms.CharField(widget=forms.NumberInput(attrs={'id':'mailbox_imap_port', 'placeholder': 'IMAP Port', 'style': 'width: 100%;', 'class': 'form-control hidden'}),label="IMAP Port")
    mailbox_smtp = forms.CharField(widget=forms.TextInput(attrs={'id':'mailbox_smtp', 'placeholder': 'SMTP Server', 'style': 'width: 100%;', 'class': 'form-control hidden'}),label="SMTP Server")
    mailbox_smtp_port = forms.CharField(widget=forms.NumberInput(attrs={'id':'mailbox_smtp_port', 'placeholder': 'SMTP Port', 'style': 'width: 100%;', 'class': 'form-control hidden'}),label="SMTP Port")
    
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

class BlacklistForm(forms.Form):
    max_counter = forms.IntegerField(widget=forms.NumberInput(attrs={'id':'max_counter', 'placeholder': 'Max emails within buffer monitor', 'style': 'width: 100%;', 'class': 'form-control'}),label="Max Counter", initial=10)
    buffer_monitor = forms.IntegerField(widget=forms.NumberInput(attrs={'id':'buffer_monitor', 'placeholder': 'Timerange for monitor (Seconds)', 'style': 'width: 100%;', 'class': 'form-control'}),label="Monitor Buffer", initial=60)
    buffer_blacklist = forms.IntegerField(widget=forms.NumberInput(attrs={'id':'buffer_blacklist', 'placeholder': 'Blacklist duration before auto-release (Seconds)', 'style': 'width: 100%;', 'class': 'form-control'}),label="Blacklist Duration", initial=3600)

class TemplateReportForm(forms.Form):
    template_report = forms.FileField(widget=forms.FileInput(attrs={'id':'template_report', 'placeholder': 'Report Template (.docx)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.docx'}),label="Report Template (.docx)",validators=(validate_is_docx,))

class TemplateNDAForm(forms.Form):
    template_nda = forms.FileField(widget=forms.FileInput(attrs={'id':'template_nda', 'placeholder': 'NDA Template (.pdf)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.pdf'}),label="NDA Template (.pdf)",validators=(validate_is_pdf,))

class TemplateCertForm(forms.Form):
    template_cert = forms.FileField(widget=forms.FileInput(attrs={'id':'template_cert', 'placeholder': 'Certificate Template (.jpg)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.jpg'}),label="Certificate Template (.jpg)",validators=(validate_is_image,))
   
class CertDataForm(forms.Form):
    template_signature = forms.FileField(widget=forms.FileInput(attrs={'id':'template_signature', 'placeholder': 'Officer Signature (.jpg)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.jpg, .png'}),label="Officer Signature (.jpg, .png)",validators=(validate_is_image,))
    template_name = forms.CharField(widget=forms.TextInput(attrs={'id':'template_name', 'placeholder': 'e.g. Billy Sudarsono', 'style': 'width: 100%;', 'class': 'form-control'}),label="Officer Name")
    template_title = forms.CharField(widget=forms.TextInput(attrs={'id':'template_title', 'placeholder': 'e.g. Founder of Gerobug', 'style': 'width: 100%;', 'class': 'form-control'}),label="Officer Title")

class CompanyIdentityForm(forms.Form):
    company_logo = forms.FileField(widget=forms.FileInput(attrs={'id':'company_logo', 'placeholder': 'Company Logo (.png)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.png'}),label="Company Logo (.png)",validators=(validate_is_image,))
    company_name = forms.CharField(widget=forms.TextInput(attrs={'id':'company_name', 'placeholder': 'e.g. GEROBUG', 'style': 'width: 100%;', 'class': 'form-control'}),label="Company Name")

class PersonalizationForm(forms.ModelForm):
    class Meta:
        model = Personalization
        fields = ['main_1', 'main_2', 'secondary_1', 'secondary_2', 'secondary_3', 'button_1']

class TroubleshootForm(forms.Form):
    troubleshoot_1 = forms.BooleanField(label="Recover Loss Report Files", required=False)
