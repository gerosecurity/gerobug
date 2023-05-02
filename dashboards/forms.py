from django import forms
from ckeditor.widgets import CKEditorWidget
from dashboards.models import StaticRules
from dashboards.rulestemplate import *
from dashboards.validators import *

class Requestform(forms.Form):
    reasons = forms.CharField(widget=forms.Textarea(attrs={"id":"reasons","name":"reasons","placeholder":"Write the reason here ..."}),required=True)

class CompleteRequestform(forms.Form):
    completereasons = forms.CharField(widget=forms.Textarea(attrs={"id":"completereasons","name":"completereasons","placeholder":"Write the reason here ..."}),required=True)

class AdminSettingForm(forms.Form):    
    try:
        RULES = StaticRules.objects.get(pk=1)
        RDP = RULES.RDP
        BT  = RULES.bountyterms
        IS  = RULES.inscope
        OOS = RULES.outofscope
        RG  = RULES.reportguidelines
        FAQ = RULES.faq

    except:
        RDP = RDP_template
        BT  = bountyterms_template
        IS  = inscope_templates
        OOS = outofscope_templates
        RG  = reportguidelines_templates
        FAQ = faq_templates

    RDP = forms.CharField(widget=CKEditorWidget(attrs={"id": "rdp"}),label="Responsible Disclosure Policy",initial=RDP)
    bountyterms = forms.CharField(widget=CKEditorWidget(attrs={"id": "bountyterms"}),label="Bounty Terms",initial=BT)
    inscope = forms.CharField(widget=CKEditorWidget(attrs={"id": "inscope"}),label="In Scope",initial=IS)
    outofscope = forms.CharField(widget=CKEditorWidget(attrs={"id": "outofscope"}),label="Out of Scope",initial=OOS)
    reportguidelines = forms.CharField(widget=CKEditorWidget(attrs={"id": "reportguidelines"}),label="Report Guidelines",initial=RG)
    faq = forms.CharField(widget=CKEditorWidget(attrs={"id": "faq"}),label="Frequenly Asked Questions",initial=FAQ)

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

class BlacklistForm(forms.Form):
    max_counter = forms.IntegerField(widget=forms.NumberInput(attrs={'id':'max_counter', 'placeholder': 'Max emails within buffer monitor', 'style': 'width: 100%;', 'class': 'form-control'}),label="Max Counter", initial=10)
    buffer_monitor = forms.IntegerField(widget=forms.NumberInput(attrs={'id':'buffer_monitor', 'placeholder': 'Timerange for monitor (Seconds)', 'style': 'width: 100%;', 'class': 'form-control'}),label="Monitor Buffer", initial=60)
    buffer_blacklist = forms.IntegerField(widget=forms.NumberInput(attrs={'id':'buffer_blacklist', 'placeholder': 'Blacklist duration before auto-release (Seconds)', 'style': 'width: 100%;', 'class': 'form-control'}),label="Blacklist Duration", initial=3600)

class TemplateReportForm(forms.Form):
    test = forms.HiddenInput()
    template_report = forms.FileField(widget=forms.FileInput(attrs={'id':'template_report', 'placeholder': 'Report Template (.pdf)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.pdf'}),label="Report Template",validators=(validate_is_pdf,))

class TemplateNDAForm(forms.Form):
    template_nda = forms.FileField(widget=forms.FileInput(attrs={'id':'template_nda', 'placeholder': 'NDA Template (.pdf)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.pdf'}),label="NDA Template",validators=(validate_is_pdf,))

class TemplateCertForm(forms.Form):
    template_cert = forms.FileField(widget=forms.FileInput(attrs={'id':'template_cert', 'placeholder': 'Certificate Template (.jpg)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.jpg'}),label="Certificate Template",validators=(validate_is_image,))
   
class CertDataForm(forms.Form):
    template_signature = forms.FileField(widget=forms.FileInput(attrs={'id':'template_signature', 'placeholder': 'Officer Signature (.jpg)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.jpg'}),label="Officer Signature",validators=(validate_is_image,))
    template_name = forms.CharField(widget=forms.TextInput(attrs={'id':'template_name', 'placeholder': 'e.g. Billy Sudarsono', 'style': 'width: 100%;', 'class': 'form-control'}),label="Officer Name")
    template_title = forms.CharField(widget=forms.TextInput(attrs={'id':'template_title', 'placeholder': 'e.g. Founder of Gerobug', 'style': 'width: 100%;', 'class': 'form-control'}),label="Officer Title")

class PersonalizationForm(forms.Form):
    company_logo = forms.FileField(widget=forms.FileInput(attrs={'id':'company_logo', 'placeholder': 'Company Logo (.png)', 'style': 'width: 100%;', 'class': 'form-control', 'accept': '.png'}),label="Company Logo",validators=(validate_is_image,))
    #company_name = forms.CharField(widget=forms.TextInput(attrs={'id':'company_name', 'placeholder': 'e.g. Gerobug Indonesia', 'style': 'width: 100%;', 'class': 'form-control'}),label="Company Name")