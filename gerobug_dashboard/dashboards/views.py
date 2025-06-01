from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group
from django.db.models.query_utils import Q
from django.contrib import messages
from django.contrib.auth import logout
from django.views.generic import (
    ListView,
    UpdateView,
    DeleteView,
    DetailView,
    TemplateView
)
from django.urls import reverse, reverse_lazy
from django.db.models import Sum
from django.http import FileResponse
from django.middleware.csrf import get_token
from prerequisites.models import MailBox, Webhook
from .models import BugHunter, BugReport, BugReportUpdate, BugReportAppeal, BugReportNDA, ReportStatus, StaticRules, BlacklistRule, CertificateData, Personalization
from .forms import Requestform, RulesGuidelineForm, CompleteRequestform, MailboxForm, AccountForm, ReviewerForm, WebhookForm, BlacklistForm, TemplateReportForm, TemplateNDAForm, TemplateCertForm, CertDataForm, PersonalizationForm, CompanyIdentityForm, Invalidform, TroubleshootForm
from sys import platform
from geromail import geromailer, gerofilter, geroparser, gerocalculator
from gerobug.settings import MEDIA_ROOT, BASE_DIR

import threading, os, shutil, gerocert.gerocert
import logging
from logging.handlers import TimedRotatingFileHandler



def LogoutForm(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('login')


class RenderDashboardAdmin(LoginRequiredMixin,ListView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReport
    template_name = "dashboard.html"
    context_object_name = "bugposts"

    def get_context_data(self, **kwargs):
        context = super(RenderDashboardAdmin, self).get_context_data(**kwargs)
        context['total_notvalid'] = BugReport.objects.filter(report_status=0).count()
        context['total_unreviewed'] = BugReport.objects.filter(report_status=1).count()
        context['total_inreview'] = BugReport.objects.filter(report_status=2).count()
        context['total_fixing'] = BugReport.objects.filter(report_status=3).count()
        context['total_retest'] = BugReport.objects.filter(report_status=4).count()
        context['total_calcbount'] = BugReport.objects.filter(report_status=5).count()
        context['total_procbount'] = BugReport.objects.filter(report_status=6).count()
        context['total_completed'] = BugReport.objects.filter(report_status=7).count()
        context['total_bounty'] = BugReport.objects.filter(report_status=5).count() + BugReport.objects.filter(report_status=6).count()
        
        # COMPANY NAME
        THEME = Personalization.objects.get(personalize_id=1)
        context['company_name'] = THEME.company_name

        return context

    
class ReportDetails(LoginRequiredMixin,DetailView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReport
    template_name = "dashboard_varieties/detail_report.html"
    context_object_name = "bugposts"

    def get_context_data(self, **kwargs):
        context = super(ReportDetails, self).get_context_data(**kwargs)
        context['reportstatus'] = ReportStatus.objects.filter(status_id=BugReport.objects.get(report_id=self.kwargs.get('pk')).report_status)[0].status_name
        context['requestform'] = Requestform()
        context['invalidform'] = Invalidform()
        context['completeform'] = CompleteRequestform()

        # COMPANY NAME
        THEME = Personalization.objects.get(personalize_id=1)
        context['company_name'] = THEME.company_name
        return context


class ReportUpdate(LoginRequiredMixin,UpdateView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReport
    template_name = "dashboard_varieties/edit_report.html"
    fields = ["report_severitystring"] # Only status field is allowed to be edited
    
    def get_success_url(self):
        report = BugReport.objects.get(report_id=self.object.report_id)
        report.report_severitytype = gerocalculator.classify(self.object.report_severitystring)
        report.report_severity = gerocalculator.calculate(self.object.report_severitystring, report.report_severitytype)
        report.report_reviewer = str(self.request.user.username)
        report.save()

        logging.getLogger("Gerologger").info("REPORT " + str(self.object.report_id) + " SEVERITY UPDATED USING " + report.report_severitytype + " BY " + str(self.request.user.username))
        return reverse('dashboard')


class ReportDelete(LoginRequiredMixin,DeleteView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReport
    template_name = "dashboard_varieties/delete_report.html"
    
    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        super().delete(*args, **kwargs)
        #self.object.delete()

        # DELETE ALL CHILD UAN OBJECT
        if BugReportUpdate.objects.filter(report_id=self.object.report_id).exists():
            BugReportUpdate.objects.filter(report_id=self.object.report_id).delete()

        if BugReportAppeal.objects.filter(report_id=self.object.report_id).exists():
            BugReportAppeal.objects.filter(report_id=self.object.report_id).delete()
        
        if BugReportNDA.objects.filter(report_id=self.object.report_id).exists():
            BugReportNDA.objects.filter(report_id=self.object.report_id).delete() 

    def get_success_url(self):
        if platform == "win32":
            shutil.rmtree(os.path.join(MEDIA_ROOT)+"\\"+self.object.report_id)
        else:
            shutil.rmtree(os.path.join(MEDIA_ROOT)+"/"+self.object.report_id)
        logging.getLogger("Gerologger").info("REPORT " + str(self.object.report_id) + " DELETED BY " + str(self.request.user.username))
        return reverse_lazy('dashboard')


class UpdateDetails(LoginRequiredMixin,DetailView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReportUpdate
    template_name = "dashboard_varieties/detail_uan.html"
    context_object_name = "bugposts"

    def get_context_data(self, **kwargs):
        context = super(UpdateDetails, self).get_context_data(**kwargs)
        context['uan_type'] = self.kwargs.get('pk')[12:13]
        context['report_title'] = BugReport.objects.get(report_id=self.kwargs.get('pk')[:12]).report_title

        # COMPANY NAME
        THEME = Personalization.objects.get(personalize_id=1)
        context['company_name'] = THEME.company_name
        return context
    

class AppealDetails(LoginRequiredMixin,DetailView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReportAppeal
    template_name = "dashboard_varieties/detail_uan.html"
    context_object_name = "bugposts"

    def get_context_data(self, **kwargs):
        context = super(AppealDetails, self).get_context_data(**kwargs)
        context['uan_type'] = self.kwargs.get('pk')[12:13]
        context['report_title'] = BugReport.objects.get(report_id=self.kwargs.get('pk')[:12]).report_title

        # COMPANY NAME
        THEME = Personalization.objects.get(personalize_id=1)
        context['company_name'] = THEME.company_name
        return context
    

class NDADetails(LoginRequiredMixin,DetailView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReportNDA
    template_name = "dashboard_varieties/detail_uan.html"
    context_object_name = "bugposts"

    def get_context_data(self, **kwargs):
        context = super(NDADetails, self).get_context_data(**kwargs)
        context['uan_type'] = self.kwargs.get('pk')[12:13]
        context['report_title'] = BugReport.objects.get(report_id=self.kwargs.get('pk')[:12]).report_title

        # COMPANY NAME
        THEME = Personalization.objects.get(personalize_id=1)
        context['company_name'] = THEME.company_name
        return context
    

@login_required
def ReportStatusView(request, id):
    count = int(ReportStatus.objects.count()) - 1
    if int(id) > count:
        return notfound_404(request, id)
    elif int(id) < 0:
        return notfound_404(request, id)
        
    report = BugReport.objects.filter(report_status=id).values()
    status = ReportStatus.objects.get(status_id=id)
    status = status.status_name
    context = {'bugreportlists': report, 'reportstatus': status}

    # COMPANY NAME
    THEME = Personalization.objects.get(personalize_id=1)
    context['company_name'] = THEME.company_name
    return render(request, 'dashboard_varieties/report_status.html', context)


@login_required
def ReportUpdateStatus(request,id):
    if request.method == "POST" and gerofilter.validate_id(id):
        if geroparser.check_mailbox_status():
            report = BugReport.objects.get(report_id=id)
            max = ReportStatus.objects.count() - 2 # LIMITED TO "BOUNTY PROCESS"

            if report.report_status < max:
                report.report_status += 1
                report.save()

            logging.getLogger("Gerologger").info("REPORT "+str(id)+" STATUS UPDATED ("+str(report.report_status)+") BY "+str(request.user.username))
            messages.success(request,"Report Status is updated!")

            def trigger_geromailer(report):
                payload = [report.report_id, report.report_title, report.report_status, "", report.report_severity]
                destination = report.hunter_email
                geromailer.notify(destination, payload) #TRIGGER GEROMAILER TO SEND UPDATE NOTIFICATION

            trigger = threading.Thread(target=trigger_geromailer, args=(report,))
            trigger.start()

        else:
            logging.getLogger("Gerologger").error("Mailbox is not ready.")
        
    return redirect('dashboard')


@login_required
def FormHandler(request, id, complete):
    if gerofilter.validate_id(id):
        report = BugReport.objects.get(report_id=id)
        # report = get_object_or_404(BugReport,report_id=id)
        status = ReportStatus.objects.get(status_id=report.report_status)
        # status = get_object_or_404(ReportStatus,status_id=report.report_status)
        status = status.status_name
        if request.method == "POST":
            form = Requestform(request.POST)
            if form.is_valid():
                reasons = form.cleaned_data.get('reasons')
                code = 0
                if (status == "In Review" or status == "Fixing" or status == "Fixing (Retest)") and complete == "0":
                    code = 701 #REQUEST AMEND
                    logging.getLogger("Gerologger").info("REPORT "+str(id)+" REQUESTED AMEND BY "+str(request.user.username))

                elif status == "Bounty Calculation" and complete == "0":
                    code = 702 #SEND CALCULATIONS
                    logging.getLogger("Gerologger").info("REPORT "+str(id)+" SEND CALCULATIONS BY "+str(request.user.username))

                elif status == "Bounty in Process" and complete == "0":
                    code = 703 #REQUEST NDA
                    logging.getLogger("Gerologger").info("REPORT "+str(id)+" REQUESTED NDA BY "+str(request.user.username))

                elif status == "Bounty in Process" and complete == "1":
                    code = 704 #COMPLETE
                    logging.getLogger("Gerologger").info("REPORT "+str(id)+" STATUS UPDATED (COMPLETE) BY "+str(request.user.username))
                
                if geroparser.check_mailbox_status():
                    # TRIGGER COMPANY ACTION WITH THREADING
                    def trigger_company_action(report):
                        geroparser.company_action(report.report_id, reasons, code)

                    if code != 0:
                        trigger = threading.Thread(target=trigger_company_action, args=(report,))
                        trigger.start()
                        messages.success(request,"Email is successfully being processed and sent to the bug hunter with your reason.")

                    else:
                        logging.getLogger("Gerologger").error("CODE = 0")
                
                else:
                    logging.getLogger("Gerologger").error("Mailbox is not ready.")
            
            else:
                logging.getLogger("Gerologger").error("Form invalid: "+str(request))
                messages.error(request,"Form invalid. Please report to the Admin for checking the logs.")

        return redirect('dashboard')

    else:
        messages.error(request,"Something's wrong with form handler. Please report to the Admin for checking the logs.")
        logging.getLogger("Gerologger").error("Something's wrong with form handler: "+str(request))
        return redirect('dashboard')


@login_required
def InvalidHandler(request, id):
    if gerofilter.validate_id(id):
        report = BugReport.objects.get(report_id=id)
        status = ReportStatus.objects.get(status_id=report.report_status)
        status = status.status_name

        if request.method == "POST":
            form = Invalidform(request.POST)
            if form.is_valid():
                if geroparser.check_mailbox_status():
                    reasons = form.cleaned_data.get('invalidreasons')

                    # MARK AS INVALID
                    report.report_status = 0
                    report.save()
                        
                    logging.getLogger("Gerologger").info("REPORT "+str(id)+" MARKED AS INVALID BY "+str(request.user.username))
                        
                    def trigger_geromailer(report):
                        payload = [report.report_id, report.report_title, report.report_status, reasons, report.report_severity]
                        destination = report.hunter_email
                        geromailer.notify(destination, payload) # TRIGGER GEROMAILER TO SEND UPDATE NOTIFICATION
                        
                    # SEND NOTIFICATION AND REASON WITH THREADING
                    trigger = threading.Thread(target=trigger_geromailer, args=(report,))
                    trigger.start()

                    messages.success(request,"Email is successfully being processed and sent to the bug hunter with your reason.")

                else:
                    logging.getLogger("Gerologger").error("Mailbox is not ready.")

            else:
                messages.error(request,"Form invalid. Please report to the Admin for checking the logs.")
                logging.getLogger("Gerologger").error("Form invalid: "+str(request))

        return redirect('dashboard')

    else:
        messages.error(request,"Something's wrong with invalid handler. Please report to the Admin for checking the logs.")
        logging.getLogger("Gerologger").error("Something's wrong with invalid handler: "+str(request))
        return redirect('dashboard')


@login_required
def ReportFiles(request, id):
    if gerofilter.validate_id(id):
        # IF UPDATE OR NDA
        if len(id) > 12:
            uan_id = id
            id = id[:12]
            type = uan_id[12:13]

            if type == 'U':
                report = BugReportUpdate.objects.get(update_id=uan_id)
                # report = get_object_or_404(BugReportNDA,update_id=uan_id)
                report_name = report.update_id + ".pdf"

            elif type == 'A':
                report = BugReportAppeal.objects.get(appeal_id=uan_id)
                # report = get_object_or_404(BugReportNDA,appeal_id=uan_id)
                report_name = report.appeal_id + ".pdf"

            elif type == 'N':
                report = BugReportNDA.objects.get(nda_id=uan_id)
                # report = get_object_or_404(BugReportNDA,nda_id=uan_id)
                report_name = report.nda_id + ".pdf"
        
        else:
            report = BugReport.objects.get(report_id=id)
            # report = get_object_or_404(BugReport,report_id=id)
            report_name = report.report_id + ".pdf"
        
        try:
            report_file = os.path.join(MEDIA_ROOT,id,report_name)
            return FileResponse(open(report_file, 'rb'), content_type='application/pdf')
        
        except FileNotFoundError:
            return redirect('dashboard')

    else:
        return redirect('dashboard')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def AdminSetting(request):
    users = User.objects.filter(is_superuser=False)
    mailbox_account = MailBox.objects.get(mailbox_id=1)
    mailbox_initial_data = {
        'mailbox_email': mailbox_account.email,
        'mailbox_password': "",
        'mailbox_type': mailbox_account.mailbox_type,
        'mailbox_imap': mailbox_account.mailbox_imap,
        'mailbox_imap_port': mailbox_account.mailbox_imap_port,
        'mailbox_smtp': mailbox_account.mailbox_smtp,
        'mailbox_smtp_port': mailbox_account.mailbox_smtp_port,
    }
    bl = BlacklistRule.objects.get(rule_id=1)
    mailbox_status = mailbox_account.mailbox_status
    mailbox_name = mailbox_account.email
    notifications = Webhook.objects.all()

    if request.method == "POST":
        reviewer = ReviewerForm(request.POST)
        if reviewer.is_valid():
            try:
                groupreviewer = Group.objects.get(name='Reviewer')
                reviewername = reviewer.cleaned_data.get('reviewername')
                revieweremail = reviewer.cleaned_data.get('reviewer_email')
                if User.objects.filter(Q(username__exact=reviewername)).count() > 0:
                    messages.error(request,"Username already used. Please try another username!")
                    logging.getLogger("Gerologger").error("Username already used!")
                    return redirect("setting")
                elif User.objects.filter(Q(email__exact=revieweremail)).count() > 0:
                    messages.error(request,"Email already used. Please try another email!")
                    logging.getLogger("Gerologger").error("Email already used!")
                    return redirect("setting")
                else:
                    reviewerpassword = "G3r0bUg_@dM!n_1337yipPie13579246810121337" #default pw, change since this is temp
                    revieweraccount = User.objects.create(username=reviewername,email=revieweremail)
                    revieweraccount.set_password(reviewerpassword)
                    revieweraccount.groups.add(groupreviewer)
                    revieweraccount.save()
                    logging.getLogger("Gerologger").info("Reviewer is created successfully")
                    messages.success(request,"Reviewer is created successfully!")
                    return redirect('setting')
            except Exception as e:
                logging.getLogger("Gerologger").error(str(e))
                messages.error(request,"Something's wrong. Perhaps your username/email is already used. Please specify another one!")
                return redirect("setting")

        mailbox = MailboxForm(request.POST)
        if mailbox.is_valid():
            mailbox_account = MailBox.objects.get(mailbox_id=1)
            mailbox_account.email = mailbox.cleaned_data.get('mailbox_email')    
            mailbox_account.password = mailbox.cleaned_data.get('mailbox_password') 
            mailbox_account.mailbox_status = 0
            mailbox_account.mailbox_type = mailbox.cleaned_data.get('mailbox_type')

            if mailbox_account.mailbox_type == '1':
                mailbox_account.mailbox_imap = "imap.gmail.com"
                mailbox_account.mailbox_imap_port = 993
                mailbox_account.mailbox_smtp = "smtp.gmail.com"
                mailbox_account.mailbox_smtp_port = 465

            elif mailbox_account.mailbox_type == '2':
                mailbox_account.mailbox_imap = "outlook.office365.com"
                mailbox_account.mailbox_imap_port = 993
                mailbox_account.mailbox_smtp = "smtp.office365.com"
                mailbox_account.mailbox_smtp_port = 587

            else:
                mailbox_account.mailbox_imap = mailbox.cleaned_data.get('mailbox_imap')
                mailbox_account.mailbox_imap_port = mailbox.cleaned_data.get('mailbox_imap_port')
                mailbox_account.mailbox_smtp = mailbox.cleaned_data.get('mailbox_smtp')
                mailbox_account.mailbox_smtp_port = mailbox.cleaned_data.get('mailbox_smtp_port')

            mailbox_account.save()
            logging.getLogger("Gerologger").info("Mailbox updated successfully.")
            messages.success(request,"Mailbox updated successfully.")
            return redirect('setting')

        account = AccountForm(request.POST)
        if account.is_valid():
            username = account.cleaned_data.get('username')
            user = User.objects.get(username=username)
            user.username = username
            user.email = account.cleaned_data.get('user_email')
            user.set_password(account.cleaned_data.get('user_password'))
            user.save()
            
            logging.getLogger("Gerologger").info("User "+str(username)+" Updated successfully")
            messages.success(request,"User "+username+" updated successfully!")
            return redirect('setting')

        form = RulesGuidelineForm(request.POST)
        if form.is_valid():
            staticrules = StaticRules.objects.get(pk=1)
            staticrules.RDP = form.cleaned_data.get('RDP')
            staticrules.bountyterms = form.cleaned_data.get('bountyterms')
            staticrules.inscope = form.cleaned_data.get('inscope')
            staticrules.outofscope = form.cleaned_data.get('outofscope')
            staticrules.reportguidelines = form.cleaned_data.get('reportguidelines')
            staticrules.faq = form.cleaned_data.get('faq')
            staticrules.save()
            logging.getLogger("Gerologger").info("Rules are updated successfully")
            messages.success(request,"Rules are updated successfully!")
            return redirect('setting')
        
        webhook = WebhookForm(request.POST)
        if webhook.is_valid():
            try:
                service = webhook.cleaned_data.get('webhook_service')
                handle = webhook.cleaned_data.get('webhook_handle')
                if Webhook.objects.filter(Q(webhook_service=service)).count() > 0:
                    messages.error(request,"Notification Channel already exists.")
                    logging.getLogger("Gerologger").warning("Duplicate Notification Channel")
                    return redirect("setting")
                else:
                    new_webhook = Webhook.objects.create(webhook_service=service,webhook_handle=handle)
                    new_webhook.save()
                    logging.getLogger("Gerologger").info("Notification Channel Saved Successfully")
                    messages.success(request,"Notification Channel Saved Successfully")
                    return redirect('setting')
            except Exception as e:
                logging.getLogger("Gerologger").error(str(e))
                messages.error(request,"Something's wrong...")
                return redirect("setting")

        blacklistform = BlacklistForm(request.POST)
        if blacklistform.is_valid():
            blacklistrule = BlacklistRule.objects.get(rule_id=1)
            blacklistrule.max_counter = blacklistform.cleaned_data.get('max_counter')    
            blacklistrule.buffer_monitor = blacklistform.cleaned_data.get('buffer_monitor') 
            blacklistrule.buffer_blacklist = blacklistform.cleaned_data.get('buffer_blacklist') 
            blacklistrule.save()

            logging.getLogger("Gerologger").info("Blacklist rule updated successfully")
            messages.success(request,"Blacklist rule updated successfully!")
            return redirect("setting")
        
        templatereport = TemplateReportForm(request.POST, request.FILES)
        if templatereport.is_valid():
            template_file = request.FILES['template_report']
            path = os.path.join(BASE_DIR, "static/templates", "Template_Report.docx")

            with open(path, 'wb+') as destination:
                for chunk in template_file.chunks():
                    destination.write(chunk)

            logging.getLogger("Gerologger").info("Report Template updated successfully")
            messages.success(request,"Report Template updated successfully!")
            return redirect('setting')
        
        templatenda = TemplateNDAForm(request.POST, request.FILES)
        if templatenda.is_valid():
            template_file = request.FILES['template_nda']
            path = os.path.join(BASE_DIR, "static/templates", "Template_NDA.pdf")

            with open(path, 'wb+') as destination:
                for chunk in template_file.chunks():
                    destination.write(chunk)

            logging.getLogger("Gerologger").info("NDA Template updated successfully")
            messages.success(request,"NDA Template updated successfully!")
            return redirect('setting')
        
        templatecert = TemplateCertForm(request.POST, request.FILES)
        if templatecert.is_valid():
            template_file = request.FILES['template_cert']
            path = os.path.join(BASE_DIR, "static/templates", "Template_Cert.jpg")

            with open(path, 'wb+') as destination:
                for chunk in template_file.chunks():
                    destination.write(chunk)

            gerocert.gerocert.generate_sample()
            logging.getLogger("Gerologger").info("Certificate Template updated successfully")
            messages.success(request,"Certificate Template updated successfully!")
            return redirect('setting')
        
        certificatedata = CertDataForm(request.POST, request.FILES)
        if certificatedata.is_valid():
            certdata = CertificateData.objects.get(cert_id=1)
            certdata.officer_name = certificatedata.cleaned_data.get('template_name')    
            certdata.officer_title = certificatedata.cleaned_data.get('template_title') 
            certdata.save()

            template_file = request.FILES['template_signature']
            path = os.path.join(BASE_DIR, "gerocert", "cert_signature")

            with open(path, 'wb+') as destination:
                for chunk in template_file.chunks():
                    destination.write(chunk)

            gerocert.gerocert.generate_sample()
            logging.getLogger("Gerologger").info("Certificate Data updated successfully")
            messages.success(request,"Certificate Data updated successfully!")
            return redirect('setting')
        
        companyidentity = CompanyIdentityForm(request.POST, request.FILES)
        if companyidentity.is_valid():
            # COMPANY NAME
            theme               = Personalization.objects.get(personalize_id=1)
            theme.company_name  = companyidentity.cleaned_data.get('company_name')
            theme.save()

            # COMPANY LOGO
            if companyidentity.cleaned_data['company_logo'] != None:
                file = request.FILES['company_logo']
                path = os.path.join(BASE_DIR, "static", "logo.png")

                with open(path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                gerocert.gerocert.generate_sample()

            logging.getLogger("Gerologger").info("Company Identity updated successfully")
            messages.success(request,"Company Identity updated successfully!")
            return redirect('setting')
             
        personalization = PersonalizationForm(request.POST)
        if personalization.is_valid():
            theme               = Personalization.objects.get(personalize_id=1)
            theme.main_1        = personalization.cleaned_data.get('main_1')    
            theme.main_2        = personalization.cleaned_data.get('main_2') 
            theme.secondary_1   = personalization.cleaned_data.get('secondary_1')  
            theme.secondary_2   = personalization.cleaned_data.get('secondary_2')
            theme.secondary_3   = personalization.cleaned_data.get('secondary_3')
            theme.button_1      = personalization.cleaned_data.get('button_1')
            theme.save()

            logging.getLogger("Gerologger").info("Personalization updated successfully")
            messages.success(request,"Personalization updated successfully!")
            return redirect('setting')
    
        troubleshoot = TroubleshootForm(request.POST)
        if troubleshoot.is_valid():
            if troubleshoot.cleaned_data.get('troubleshoot_1')  == True:
                if geroparser.check_mailbox_status():
                    # FILE RECOVERY THREAD
                    def trigger_recovery(BUGREPORTS):
                        geroparser.recover_loss_file_handler(BUGREPORTS) 
                    
                    trigger = threading.Thread(target=trigger_recovery, args=(BugReport.objects.all(),))
                    trigger.start()
                    
                else:
                    logging.getLogger("Gerologger").error("Mailbox is not ready.")
            
            return redirect("setting")

    THEME = Personalization.objects.get(personalize_id=1)
    RULES = StaticRules.objects.get(pk=1)
    return render(request,'setting.html',
                  {'form': RulesGuidelineForm(instance=RULES), 'mailbox': MailboxForm(initial=mailbox_initial_data), 'account': AccountForm(),'reviewer': ReviewerForm(),'webhooks': WebhookForm(),'blacklistrule': BlacklistForm(),
                    'templatereport': TemplateReportForm(), 'templatenda': TemplateNDAForm(), 'templatecert': TemplateCertForm(), 'certdata': CertDataForm(), 'companyidentity': CompanyIdentityForm(),
                    'personalization': PersonalizationForm(instance=THEME), 'troubleshoot': TroubleshootForm(), 'users':users, 'mailbox_status': mailbox_status,'mailbox_name': mailbox_name,'notifications':notifications,'bl':bl, 'company_name':THEME.company_name})

@login_required
def ReviewerDelete(request,id):
    if request.method == "POST":
        try:
            if User.objects.filter(id=id).count() != 0:
                User.objects.filter(id=id).delete()
                messages.success(request,"User is deleted successfully!")
                logging.getLogger("Gerologger").info("USER ID " + str(id) + " SUCCESSFULLY DELETED BY " + str(request.user.username))
                return redirect('dashboard')
            
        except Exception as e:
            logging.getLogger("Gerologger").error(str(e))
            messages.error(request,"Something wrong. The delete operation is unsuccessful. Please report to the Admin!")
            return redirect('setting')
        
        return redirect('setting')
    
    return render(request,'setting.html')

@login_required
def NotificationDelete(request,service):
    if request.method == "POST":
        try:
            if Webhook.objects.filter(webhook_service=service).count() != 0:
                Webhook.objects.filter(webhook_service=service).delete()
                messages.success(request,"Notification Media is deleted successfully!")
                return redirect('setting')
        except Exception as e:
            logging.getLogger("Gerologger").error(str(e))
            messages.error(request,"Something wrong. The delete operation is unsuccessful. Please report to the Admin!")
            return redirect('setting')
        return redirect('setting')
    return render(request,'setting.html')

@login_required
def OWASPCalculator(request):
    # COMPANY NAME
    THEME = Personalization.objects.get(personalize_id=1)
    company_name = THEME.company_name

    return render(request,'owasp-calculator.html',{'company_name':company_name})

@login_required
def CVSSCalculator(request):
    # COMPANY NAME
    THEME = Personalization.objects.get(personalize_id=1)
    company_name = THEME.company_name
    
    return render(request,'cvss-calculator.html',{'company_name':company_name})

@login_required
def ManageRoles(request):
    return render(request,'manage.html')

def rulescontext(request,):
    staticrules = StaticRules.objects.get(pk=1)

    # COMPANY NAME
    THEME = Personalization.objects.get(personalize_id=1)
    company_name = THEME.company_name

    return render(request,'rules.html',{'RDP':staticrules.RDP,'bountyterms':staticrules.bountyterms,'inscope':staticrules.inscope,'outofscope':staticrules.outofscope,'reportguidelines':staticrules.reportguidelines,'faq':staticrules.faq,'company_name':company_name})

def emailcontext(request,):
    if MailBox.objects.filter(mailbox_id=1)[0].email != "":
        email = MailBox.objects.filter(mailbox_id=1)[0].email
        template = "Submit your email to <strong>"+ email +"</strong> using the templates below..."
    else:
        template = "Currently the company hasn't set their email yet. Please contact the admin/wait for the mailbox setup."

    # COMPANY NAME
    THEME = Personalization.objects.get(personalize_id=1)
    company_name = THEME.company_name

    return render(request, 'submit.html',{'template':template, 'company_name':company_name})

def halloffame(request,):
    bughunters = BugHunter.objects.alias(
        points=Sum('hunter_scores')
    ).exclude(hunter_scores=0).order_by('-points')

    # COMPANY NAME
    THEME = Personalization.objects.get(personalize_id=1)
    company_name = THEME.company_name

    return render(request, 'halloffame.html',{'bughunters':bughunters, 'company_name':company_name})

def notfound_404(request, exception):
    return render(request, '404.html', status=404)

# def error_500(request, exception):
#     return render(request, '500.html', status=500)

class Themes(TemplateView):
    template_name = 'theme.css'
    content_type = 'text/css'
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        THEME = Personalization.objects.get(personalize_id=1)
        context['main_1']       = THEME.main_1
        context['main_2']       = THEME.main_2
        context['secondary_1']  = THEME.secondary_1
        context['secondary_2']  = THEME.secondary_2
        context['secondary_3']  = THEME.secondary_3
        context['button_1']     = THEME.button_1
        context['text_1']       = "Black"
        context['text_2']       = "White"

        return self.render_to_response(context)