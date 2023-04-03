from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User, Group
from django.views.generic.edit import FormMixin
from django.db.models.query_utils import Q
from django.contrib import messages
from django.contrib.auth import logout
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView
)
from django.urls import reverse, reverse_lazy
from django.db.models import Sum
from django.http import FileResponse
from .models import BugHunter, BugReport, BugReportUpdate, BugReportAppeal, BugReportNDA, ReportStatus, StaticRules
from prerequisites.models import MailBox
from .forms import Requestform, AdminSettingForm, CompleteRequestform, MailboxForm, AccountForm, ReviewerForm
from geromail import geromailer, gerofilter, geroparser
from sys import platform
from gerobug.settings import MEDIA_ROOT
import threading, os, shutil



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
        context['completeform'] = CompleteRequestform()
        return context


class ReportUpdate(LoginRequiredMixin,UpdateView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReport
    template_name = "dashboard_varieties/edit_report.html"
    fields = ["report_severity","report_severitystring","report_reviewer"] #Only status field is allowed to be edited
    
    def get_success_url(self):
        return reverse('dashboard')


class ReportDelete(LoginRequiredMixin,DeleteView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReport
    template_name = "dashboard_varieties/delete_report.html"
    
    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        super().delete(*args, **kwargs)

    def get_success_url(self):
        if platform == "win32":
            shutil.rmtree(os.path.join(MEDIA_ROOT)+"\\"+self.object.report_id)
        else:
            shutil.rmtree(os.path.join(MEDIA_ROOT)+"/"+self.object.report_id)
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
        return context
    

@login_required
def ReportStatusView(request, id):
    report = BugReport.objects.filter(report_status=id).values()
    status = ReportStatus.objects.get(status_id=id)
    status = status.status_name
    context = {'bugreportlists': report, 'reportstatus': status}
    return render(request, 'dashboard_varieties/report_status.html', context)


@login_required
def ReportUpdateStatus(request,id):
    if request.method == "POST" and gerofilter.validate_id(id):
        report = BugReport.objects.get(report_id=id)
        max = ReportStatus.objects.count() - 2 # LIMITED TO "BOUNTY PROCESS"

        if report.report_status < max:
           report.report_status += 1
           report.save()
        messages.success(request,"Report Status is updated!")

        def trigger_geromailer(report):
            payload = [report.report_id, report.report_title, report.report_status, "", report.report_severity]
            destination = report.hunter_email
            geromailer.notify(destination, payload) #TRIGGER GEROMAILER TO SEND UPDATE NOTIFICATION

        trigger = threading.Thread(target=trigger_geromailer, args=(report,))
        trigger.start()

    return redirect('dashboard')


@login_required
def FormHandler(request, id, complete):
    if gerofilter.validate_id(id):
        report = BugReport.objects.get(report_id=id)
        status = ReportStatus.objects.get(status_id=report.report_status)
        status = status.status_name
        if request.method == "POST":
            form = Requestform(request.POST)
            if form.is_valid():
                reasons = form.cleaned_data.get('reasons')
                code = 0
                if status == "Need to Review" and complete == "0":
                    # MARK AS INVALID
                    report.report_status = 0
                    report.save()

                    def trigger_geromailer(report):
                        payload = [report.report_id, report.report_title, report.report_status, reasons, report.report_severity]
                        destination = report.hunter_email
                        geromailer.notify(destination, payload) #TRIGGER GEROMAILER TO SEND UPDATE NOTIFICATION
                    
                    # SEND NOTIFICATION AND REASON WITH THREADING
                    trigger = threading.Thread(target=trigger_geromailer, args=(report,))
                    trigger.start()

                elif (status == "In Review" or status == "Fixing" or status == "Fixing (Retest)") and complete == "0":
                    code = 701 #REQUEST AMEND

                elif status == "Bounty Calculation" and complete == "0":
                    code = 702 #SEND CALCULATIONS

                elif status == "Bounty in Process" and complete == "0":
                    code = 703 #REQUEST NDA

                elif status == "Bounty in Process" and complete == "1":
                    code = 704 #COMPLETE

                messages.success(request,"Email is successfully being processed and sent to the bug hunter with your reason.")
                # TRIGGER COMPANY ACTION WITH THREADING
                def trigger_company_action(report):
                    geroparser.company_action(report.report_id, reasons, code)

                if code != 0:
                    trigger = threading.Thread(target=trigger_company_action, args=(report,))
                    trigger.start()
                
                return redirect('dashboard')

        return redirect('dashboard')

    else:
        messages.error(request,"Something's wrong. Please report to the Admin for checking the logs.")
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
                report_name = report.update_id + ".pdf"

            elif type == 'A':
                report = BugReportAppeal.objects.get(appeal_id=uan_id)
                report_name = report.appeal_id + ".pdf"

            elif type == 'N':
                report = BugReportNDA.objects.get(nda_id=uan_id)
                report_name = report.nda_id + ".pdf"
        
        else:
            report = BugReport.objects.get(report_id=id)
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
    mailbox_status = mailbox_account.mailbox_status
    mailbox_name = mailbox_account.email

    if request.method == "POST":
        reviewer = ReviewerForm(request.POST)
        if reviewer.is_valid():
            try:
                groupreviewer = Group.objects.get(name='Reviewer')
                reviewername = reviewer.cleaned_data.get('reviewername')
                revieweremail = reviewer.cleaned_data.get('reviewer_email')
                if User.objects.filter(Q(username__exact=reviewername)).count() > 0:
                    messages.error(request,"Username is already used. Please try another username!")
                    print("[LOG] Username is duplicated!")
                    return redirect("setting")
                elif User.objects.filter(Q(email__exact=revieweremail)).count() > 0:
                    messages.error(request,"Email is already used. Please try another email!")
                    print("[LOG] Email is duplicated!")
                    return redirect("setting")
                else:
                    reviewerpassword = "G3r0bUg_@dM!n_1337yipPie13579246810121337" #default pw, change since this is temp
                    revieweraccount = User.objects.create(username=reviewername,email=revieweremail)
                    revieweraccount.set_password(reviewerpassword)
                    revieweraccount.groups.add(groupreviewer)
                    revieweraccount.save()
                    print("[LOG] Reviewer is created successfully")
                    messages.success(request,"Reviewer is created successfully!")
                    return redirect('setting')
            except Exception as e:
                print("[LOG] "+ e)
                messages.error(request,"Something's wrong. Perhaps your username/email is already used. Please specify another one!")
                return redirect("setting")

        mailbox = MailboxForm(request.POST)
        if mailbox.is_valid():
            mailbox_account = MailBox.objects.get(mailbox_id=1)
            mailbox_account.email = mailbox.cleaned_data.get('mailbox_email')    
            mailbox_account.password = mailbox.cleaned_data.get('mailbox_password') 
            mailbox_account.mailbox_status = 0
            mailbox_account.save()
            print("[LOG] Mailbox updated successfully")
            messages.success(request,"Mailbox updated successfully!")
            return redirect('setting')

        account = AccountForm(request.POST)
        if account.is_valid():
            username = account.cleaned_data.get('username')
            user = User.objects.get(username=username)
            user.username = username
            user.email = account.cleaned_data.get('user_email')
            user.set_password(account.cleaned_data.get('user_password'))
            user.save()
            
            print("[LOG] Superuser updated successfully")
            messages.success(request,"Superuser is updated successfully!")
            return redirect('setting')

        form = AdminSettingForm(request.POST)
        if form.is_valid():
            staticrules = StaticRules.objects.get(pk=1)
            staticrules.RDP = form.cleaned_data.get('RDP')
            staticrules.bountyterms = form.cleaned_data.get('bountyterms')
            staticrules.inscope = form.cleaned_data.get('inscope')
            staticrules.outofscope = form.cleaned_data.get('outofscope')
            staticrules.reportguidelines = form.cleaned_data.get('reportguidelines')
            staticrules.faq = form.cleaned_data.get('faq')
            staticrules.save()
            print("[LOG] Rules are updated successfully")
            messages.success(request,"Rules are updated successfully!")
            return redirect('setting')
        
    return render(request,'setting.html',{'form': AdminSettingForm(), 'mailbox': MailboxForm(), 'account': AccountForm(),'reviewer': ReviewerForm(),'users':users,'mailbox_status': mailbox_status,'mailbox_name': mailbox_name})

@login_required
def ReviewerDelete(request,id):
    if request.method == "POST":
        try:
            if User.objects.filter(id=id).count() != 0:
                User.objects.filter(id=id).delete()
                messages.success(request,"User is deleted successfully!")
        except Exception as e:
            print("[LOG] ", e)
            messages.error(request,"Something wrong. The delete operation is unsuccessful. Please report to the Admin!")
            return redirect('setting')
        return redirect('setting')
    return render(request,'setting.html')

@login_required
def OWASPCalculator(request):
    return render(request,'owasp-calculator.html')

@login_required
def ManageRoles(request):
    return render(request,'manage.html')

def rulescontext(request,):
    staticrules = StaticRules.objects.get(pk=1)
    return render(request,'rules.html',{'RDP':staticrules.RDP,'bountyterms':staticrules.bountyterms,'inscope':staticrules.inscope,'outofscope':staticrules.outofscope,'reportguidelines':staticrules.reportguidelines,'faq':staticrules.faq})

def emailcontext(request,):
    if MailBox.objects.filter(mailbox_id=1)[0].email != "":
        email = MailBox.objects.filter(mailbox_id=1)[0].email
        template = "Submit your email to <strong>"+ email +"</strong> using the templates below..."
    else:
        template = "Currently the company hasn't set their email yet. Please contact the admin/wait for the mailbox setup."
    return render(request, 'submit.html',{'template':template})

def halloffame(request,):
    bughunters = BugHunter.objects.alias(
        points=Sum('hunter_scores')
    ).exclude(hunter_scores=0).order_by('-points') #descending use '-'

    return render(request, 'halloffame.html',{'bughunters':bughunters})
