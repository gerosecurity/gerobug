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
from django.db import transaction
from django.db.models import Sum
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from django.middleware.csrf import get_token
from django.utils.html import format_html
from prerequisites.models import MailBox, Webhook
from .models import APPEAL_WINDOW_DAYS, BOUNTY_CALC_STATUS, COMPLETED_STATUS, BugHunter, BugReport, BugReportUpdate, BugReportAppeal, BugReportNDA, BugReportHunterComment, ReportStatus, StaticRules, BlacklistRule, CertificateData, Personalization, TroubleshootSettings
from .forms import Requestform, RulesGuidelineForm, CompleteRequestform, MailboxForm, AccountForm, ReviewerForm, WebhookForm, BlacklistForm, TemplateReportForm, TemplateNDAForm, TemplateCertForm, CertDataForm, PersonalizationForm, CompanyIdentityForm, Invalidform, TroubleshootForm
from geromail import geromailer, gerofilter, geroparser, gerocalculator
from gerobug.settings import MEDIA_ROOT, BASE_DIR

import threading, os, shutil, secrets, uuid, html, gerocert.gerocert
import logging


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
    ordering = ['-report_severity', 'report_datetime']

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

    
_SUBMISSION_KINDS = (
    ('updates',  'update',  BugReportUpdate,        'update_detail',  'Update'),
    ('appeals',  'appeal',  BugReportAppeal,        'appeal_detail',  'Appeal'),
    ('data',     'nda',     BugReportNDA,           'nda_detail',     'Submission'),
    ('comments', 'comment', BugReportHunterComment, 'comment_detail', 'Question'),
)


def build_hunter_submissions(report):
    out = {}
    for key, prefix, model, route, label in _SUBMISSION_KINDS:
        rows = []
        for row in model.objects.filter(report_id=report.report_id):
            ident = getattr(row, prefix + '_id')
            rows.append({
                'ident': ident,
                'tag': ident[len(report.report_id):],
                'label': label,
                'when': getattr(row, prefix + '_datetime'),
                'summary': getattr(row, prefix + '_summary'),
                'detail_url': reverse(route, kwargs={'pk': ident}),
                'has_file': bool(getattr(row, prefix + '_file', 0)) and os.path.isfile(
                    os.path.join(MEDIA_ROOT, report.report_id, ident + '.pdf')),
            })
        rows.sort(key=lambda r: r['when'], reverse=True)
        out[key] = rows
    return out


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

        report = BugReport.objects.get(report_id=self.kwargs.get('pk'))

        report_file = os.path.join(MEDIA_ROOT, report.report_id, report.report_id + '.pdf')
        context['report_file_exists'] = os.path.isfile(report_file)

        context['submissions'] = build_hunter_submissions(report)

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
    
    def form_valid(self, form):
        report_id = self.get_object().report_id
        for model in (BugReportUpdate, BugReportAppeal, BugReportNDA,
                      BugReportHunterComment):
            model.objects.filter(report_id=report_id).delete()
        return super().form_valid(form)

    def get_success_url(self):
        report_dir = os.path.join(MEDIA_ROOT, self.object.report_id)
        if os.path.exists(report_dir):
            shutil.rmtree(report_dir)
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
        parent = BugReport.objects.filter(report_id=self.kwargs.get('pk')[:12]).first()
        context['report_title'] = parent.report_title if parent else ''

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
        parent = BugReport.objects.filter(report_id=self.kwargs.get('pk')[:12]).first()
        context['report_title'] = parent.report_title if parent else ''

        # COMPANY NAME
        THEME = Personalization.objects.get(personalize_id=1)
        context['company_name'] = THEME.company_name
        return context
    

class CommentDetails(LoginRequiredMixin,DetailView):
    login_url = '/login/'
    redirect_field_name = 'login'
    model = BugReportHunterComment
    template_name = "dashboard_varieties/detail_comment.html"
    context_object_name = "bugposts"

    def get_context_data(self, **kwargs):
        context = super(CommentDetails, self).get_context_data(**kwargs)
        parent = BugReport.objects.filter(report_id=self.kwargs.get('pk')[:12]).first()
        context['report_title'] = parent.report_title if parent else ''

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
        parent = BugReport.objects.filter(report_id=self.kwargs.get('pk')[:12]).first()
        context['report_title'] = parent.report_title if parent else ''

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
        
    report = BugReport.objects.filter(report_status=id)
    status = ReportStatus.objects.get(status_id=id)
    status = status.status_name
    context = {'bugreportlists': report, 'reportstatus': status, 'status_id': int(id)}

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
            report.last_email_code = 300 if report.report_status == 0 else 301
            report.last_email_note = ''
            report.save()

            logging.getLogger("Gerologger").info("REPORT "+str(id)+" STATUS UPDATED ("+str(report.report_status)+") BY "+str(request.user.username))
            messages.success(request,"Report Status is updated!")

            def trigger_geromailer(report):
                from django.db import connection as db_connection
                try:
                    payload = [report.report_id, report.report_title, report.report_status, "", report.report_severity]
                    destination = report.hunter_email
                    geromailer.notify(destination, payload) #TRIGGER GEROMAILER TO SEND UPDATE NOTIFICATION
                except Exception as e:
                    logging.getLogger("Gerologger").error(f"Thread failed to send notification for {report.report_id}: {e}")
                finally:
                    db_connection.close()

            trigger = threading.Thread(target=trigger_geromailer, args=(report,))
            trigger.start()

        else:
            logging.getLogger("Gerologger").error("Mailbox is not ready.")
        
    return redirect('dashboard')


@login_required
def KanbanMove(request, id):
    # DRAG-AND-DROP COLUMN MOVE. UNLIKE ReportUpdateStatus (SINGLE-STEP FORWARD
    # BUTTON) THIS ACCEPTS AN ARBITRARY TARGET COLUMN, SO ONLY BOARD-VISIBLE
    # STATUSES ARE PERMITTED. THE HUNTER GETS THE SAME NOTIFICATION EITHER WAY.
    ALLOWED_TARGETS = {1, 2, 3, 4, 5}
    MOVABLE_SOURCES = {1, 2, 3, 4, 5, 6}

    if request.method != "POST":
        return JsonResponse({'error': 'POST required'}, status=405)
    if not gerofilter.validate_id(id):
        return JsonResponse({'error': 'unknown report'}, status=404)

    try:
        new_status = int(request.POST.get('new_status', ''))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'invalid status'}, status=400)
    if new_status not in ALLOWED_TARGETS:
        return JsonResponse({'error': 'status not movable on the board'}, status=400)

    if not geroparser.check_mailbox_status():
        logging.getLogger("Gerologger").error("Mailbox is not ready.")
        return JsonResponse({'error': 'Mailbox is not ready - status changes are disabled until the mailbox is configured.'}, status=409)

    report = BugReport.objects.get(report_id=id)
    if report.report_status not in MOVABLE_SOURCES:
        return JsonResponse({'error': 'report cannot be moved from its current status'}, status=400)
    if report.report_status == new_status:
        return JsonResponse({'status': 'unchanged'})

    report.report_status = new_status
    report.last_email_code = 301
    report.last_email_note = ''
    report.save()
    logging.getLogger("Gerologger").info("REPORT "+str(id)+" STATUS MOVED ("+str(new_status)+") BY "+str(request.user.username))

    def trigger_geromailer(report):
        from django.db import connection as db_connection
        try:
            payload = [report.report_id, report.report_title, report.report_status, "", report.report_severity]
            geromailer.notify(report.hunter_email, payload)
        except Exception as e:
            logging.getLogger("Gerologger").error(f"Thread failed to send notification for {report.report_id}: {e}")
        finally:
            db_connection.close()

    trigger = threading.Thread(target=trigger_geromailer, args=(report,))
    trigger.start()

    return JsonResponse({'status': 'ok', 'report': id, 'new_status': new_status})


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
                    nda_required = form.cleaned_data.get('nda_required', True)
                    if nda_required:
                        code = 703 #REQUEST NDA + PREREQUISITES
                        logging.getLogger("Gerologger").info("REPORT "+str(id)+" REQUESTED NDA BY "+str(request.user.username))
                    else:
                        code = 705 #REQUEST PREREQUISITES ONLY (NO NDA)
                        logging.getLogger("Gerologger").info("REPORT "+str(id)+" REQUESTED PREREQUISITES (NO NDA) BY "+str(request.user.username))

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
                        messages.error(request,"This action is not available for the report's current status.")

                else:
                    logging.getLogger("Gerologger").error("Mailbox is not ready.")
                    messages.error(request,"Mailbox is not ready. Please set up the mailbox in Settings before sending emails.")

            else:
                logging.getLogger("Gerologger").error("Form invalid: "+str(form.errors.as_json()))
                for _field, _errors in form.errors.items():
                    for _err in _errors:
                        messages.error(request, _err)

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

                    duplicate_of = form.cleaned_data.get('duplicate_of') or ''
                    if duplicate_of == report.report_id:
                        messages.error(request, "A report cannot be marked as a duplicate of itself.")
                        return redirect('dashboard')

                    # MARK AS INVALID
                    report.report_status = 0
                    if duplicate_of:
                        report.report_duplicate = 1
                        report.report_duplicate_of = duplicate_of
                    report.last_email_code = 300
                    report.last_email_note = reasons or ''
                    report.save()
                        
                    logging.getLogger("Gerologger").info("REPORT "+str(id)+" MARKED AS INVALID BY "+str(request.user.username)+(" (duplicate of "+duplicate_of+")" if duplicate_of else ""))
                        
                    def trigger_geromailer(report, reasons=reasons):
                        from django.db import connection as db_connection
                        try:
                            payload = [report.report_id, report.report_title, report.report_status, reasons, report.report_severity]
                            destination = report.hunter_email
                            geromailer.notify(destination, payload) # TRIGGER GEROMAILER TO SEND UPDATE NOTIFICATION
                        except Exception as e:
                            logging.getLogger("Gerologger").error(f"Thread failed to send notification for {report.report_id}: {e}")
                        finally:
                            db_connection.close()
                        
                    # SEND NOTIFICATION AND REASON WITH THREADING
                    trigger = threading.Thread(target=trigger_geromailer, args=(report,))
                    trigger.start()

                    messages.success(request,"Email is successfully being processed and sent to the bug hunter with your reason.")

                else:
                    logging.getLogger("Gerologger").error("Mailbox is not ready.")
                    messages.error(request,"Mailbox is not ready. Please set up the mailbox in Settings before sending emails.")

            else:
                logging.getLogger("Gerologger").error("Form invalid: "+str(form.errors.as_json()))
                for _field, _errors in form.errors.items():
                    for _err in _errors:
                        messages.error(request, _err)

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


def send_password_reset_link(request, user):
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.contrib.auth.tokens import default_token_generator
    from geromail import mail_templates

    url = request.build_absolute_uri(reverse('rules'))
    domain = url[:len(url) - 1]
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    subject = mail_templates.subjectlist[9999]
    body = mail_templates.messagelist[9999]
    body = body.replace("~USERNAME~", html.escape(user.username))
    body = body.replace("~DOMAIN~", str(domain))
    body = body.replace("~UID~", str(uid))
    body = body.replace("~TOKEN~", str(token))

    return geromailer.write_mail_raw(subject, body, user.email)


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
        if not request.user.is_superuser:
            logging.getLogger("Gerologger").warning("BLOCKED unauthorized admin-setting change by " + str(request.user.username))
            messages.error(request,"You are not authorized to perform this action.")
            return redirect('setting')

        reviewer = ReviewerForm(request.POST)
        if 'reviewername' in request.POST and not reviewer.is_valid():
            for _field, _errors in reviewer.errors.items():
                for _err in _errors:
                    messages.error(request, _err)
            return redirect("setting")
        if reviewer.is_valid():
            try:
                groupreviewer = Group.objects.get(name='Reviewer')
                reviewername = reviewer.cleaned_data.get('reviewername')
                revieweremail = reviewer.cleaned_data.get('reviewer_email')
                if User.objects.filter(Q(username__iexact=reviewername)).count() > 0:
                    messages.error(request,"Username already used. Please try another username!")
                    logging.getLogger("Gerologger").error("Username already used!")
                    return redirect("setting")
                elif User.objects.filter(Q(email__iexact=revieweremail)).count() > 0:
                    messages.error(request,"Email already used. Please try another email!")
                    logging.getLogger("Gerologger").error("Email already used!")
                    return redirect("setting")
                else:
                    reviewerpassword = secrets.token_urlsafe(16)
                    revieweraccount = User.objects.create(username=reviewername,email=revieweremail)
                    revieweraccount.set_password(reviewerpassword)
                    revieweraccount.groups.add(groupreviewer)
                    revieweraccount.save()
                    logging.getLogger("Gerologger").info("Reviewer is created successfully")

                    if geroparser.check_mailbox_status():
                        try:
                            if send_password_reset_link(request, revieweraccount):
                                logging.getLogger("Gerologger").info(f"Password reset link sent to reviewer: {revieweremail}")
                                messages.success(request, "Reviewer created! A password reset link has been sent to their email.")
                            else:
                                logging.getLogger("Gerologger").error("Reviewer created but the reset email failed to send.")
                                messages.warning(request, "Reviewer created, but failed to send the password reset email. Please use the 'Forgot Password' feature or resend the link.")
                        except Exception as mail_err:
                            logging.getLogger("Gerologger").error(f"Reviewer created but failed to send reset email: {mail_err}")
                            messages.warning(request, "Reviewer created, but failed to send the password reset email. Please use the 'Forgot Password' feature or resend the link.")
                    else:
                        messages.success(request, "Reviewer created! Mailbox is not ready — please ask the reviewer to use 'Forgot Password' to set their password.")

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
             
        if request.POST.get('personalize_reset'):
            theme = Personalization.objects.get(personalize_id=1)
            for field, value in Personalization.BRAND_DEFAULTS.items():
                setattr(theme, field, value)
            theme.save()
            logging.getLogger("Gerologger").info("Personalization reset to brand defaults")
            messages.success(request, "Colors reset to the default theme!")
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
                    'personalization': PersonalizationForm(instance=THEME), 'theme_presets': Personalization.THEME_PRESETS, 'troubleshoot': TroubleshootForm(), 'report_statuses': ReportStatus.objects.all().order_by('status_id'), 'users':users, 'mailbox_status': mailbox_status,'mailbox_name': mailbox_name,'notifications':notifications,'bl':bl, 'company_name':THEME.company_name})


RESEND_EMAIL_LABELS = {
    300: "Invalid Report Notification",
    301: "Status Update Notification",
    701: "Amend / Update Request",
    702: "Bounty Calculation",
    703: "NDA & Prerequisites Request",
    704: "Completion (Certificate)",
    705: "Prerequisites Request",
}


@login_required
def ResendEmail(request):
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('setting')

    if request.method == "POST":
        report_id = request.POST.get('report_id', '').strip().upper()

        if len(report_id) != 12 or not report_id.isalnum():
            messages.error(request, "Invalid Report ID format (expected 12 alphanumeric characters).")
            return redirect(reverse('setting') + '#troubleshoot')

        if not BugReport.objects.filter(report_id=report_id).exists():
            messages.error(request, f"Report {report_id} was not found.")
            return redirect(reverse('setting') + '#troubleshoot')

        if not geroparser.check_mailbox_status():
            logging.getLogger("Gerologger").error("Resend email aborted: mailbox is not ready.")
            messages.error(request, "Mailbox is not ready. Cannot resend the email right now.")
            return redirect(reverse('setting') + '#troubleshoot')

        report = BugReport.objects.get(report_id=report_id)
        username = request.user.username

        code, note = report.last_email_code, report.last_email_note
        if code not in RESEND_EMAIL_LABELS:
            messages.error(request, f"No operator-initiated email is recorded for {report_id}, so there is nothing to resend. Send the email from the report page instead.")
            return redirect(reverse('setting') + '#troubleshoot')

        if code == 704:
            hunter = BugHunter.objects.filter(hunter_email=report.hunter_email).first()
            if not hunter:
                messages.error(request, f"No hunter record for {report_id}; the certificate cannot be rebuilt.")
                return redirect(reverse('setting') + '#troubleshoot')
            try:
                gerocert.gerocert.generate(report_id, hunter.hunter_username, int(report.report_severity))
            except Exception as e:
                logging.getLogger("Gerologger").error(f"Certificate rebuild failed for {report_id}: {e}")
                messages.error(request, f"Could not rebuild the certificate for {report_id}: {e}")
                return redirect(reverse('setting') + '#troubleshoot')

        restarts_window = code == 702 and report.report_status == BOUNTY_CALC_STATUS
        if restarts_window:
            report.report_calc_sent_at = timezone.now()
            report.save(update_fields=['report_calc_sent_at'])

        def trigger_resend(report, code, note):
            from django.db import connection as db_connection
            try:
                payload = [report.report_id, report.report_title, report.report_status,
                           note, report.report_severity]
                geromailer.write_mail(code, payload, report.hunter_email)
                logging.getLogger("Gerologger").info(
                    f"RESEND email (code={code}) for {report.report_id} to {report.hunter_email} triggered by {username}")
            except Exception as e:
                logging.getLogger("Gerologger").error(f"Resend failed for {report.report_id}: {e}")
            finally:
                db_connection.close()

        threading.Thread(target=trigger_resend, args=(report, code, note)).start()

        what = RESEND_EMAIL_LABELS[code]
        if restarts_window:
            logging.getLogger("Gerologger").info(
                f"RESEND {report_id}: appeal window restarted by {username}")
            messages.success(request, f"Resending the {what} email for {report_id} to {report.hunter_email}. The hunter's 30-day appeal window restarts from now. Check the logs below to confirm delivery.")
        else:
            messages.success(request, f"Resending the {what} email for {report_id} to {report.hunter_email}. Check the logs below to confirm delivery.")

    return redirect(reverse('setting') + '#troubleshoot')


@login_required
def ToggleHunterEmailSinkhole(request):
    if not request.user.is_superuser:
        logging.getLogger("Gerologger").warning(
            "BLOCKED unauthorized hunter-email-sinkhole toggle by " + str(request.user.username))
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('setting')

    if request.method == "POST":
        row, _created = TroubleshootSettings.objects.get_or_create(settings_id=1)
        row.hunter_email_sinkhole = not row.hunter_email_sinkhole
        if row.hunter_email_sinkhole:
            row.sinkhole_enabled_by = request.user.username
            row.sinkhole_enabled_at = timezone.now()
        row.save()

        state = "ENABLED" if row.hunter_email_sinkhole else "disabled"
        logging.getLogger("Gerologger").warning(
            f"Hunter email sinkhole {state} by {request.user.username}")

        if row.hunter_email_sinkhole:
            messages.success(request, "Hunter email sinkhole ENABLED. No outgoing email will reach bug hunters until you disable it here.")
        else:
            messages.success(request, "Hunter email sinkhole disabled. Outgoing hunter email will resume normally.")

    return redirect(reverse('setting') + '#troubleshoot')


def _tail_file(path, n):
    with open(path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        pointer = f.tell()
        data = b''
        block = 4096
        while pointer > 0 and data.count(b'\n') <= n:
            read_size = min(block, pointer)
            pointer -= read_size
            f.seek(pointer)
            data = f.read(read_size) + data
    text = data.decode('utf-8', errors='replace')
    return text.splitlines()[-n:]


@login_required
def ViewLogs(request):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Forbidden'}, status=403)

    log_path = os.path.join(BASE_DIR, 'log', 'gerobug.log')

    try:
        lines = int(request.GET.get('lines', 200))
    except (TypeError, ValueError):
        lines = 200
    lines = max(10, min(lines, 2000))

    if not os.path.isfile(log_path):
        return JsonResponse({'ok': False, 'error': 'Log file not found.', 'lines': []})

    try:
        tail = _tail_file(log_path, lines)
        return JsonResponse({'ok': True, 'lines': tail, 'count': len(tail)})
    except Exception as e:
        logging.getLogger("Gerologger").error(f"ViewLogs failed: {e}")
        return JsonResponse({'ok': False, 'error': str(e), 'lines': []})


@login_required
def ReportOverride(request):
    if not request.user.is_superuser:
        if request.method == "GET":
            return JsonResponse({'ok': False, 'error': 'Forbidden'}, status=403)
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('setting')

    if request.method == "GET":
        report_id = request.GET.get('report_id', '').strip().upper()
        if len(report_id) != 12 or not report_id.isalnum():
            return JsonResponse({'ok': False, 'error': 'Invalid Report ID format (expected 12 alphanumeric characters).'})
        try:
            report = BugReport.objects.get(report_id=report_id)
        except BugReport.DoesNotExist:
            return JsonResponse({'ok': False, 'error': f'Report {report_id} was not found.'})
        hunter = BugHunter.objects.filter(hunter_email=report.hunter_email).first()
        return JsonResponse({
            'ok': True,
            'title': report.report_title,
            'status': report.report_status,
            'endpoint': report.report_endpoint,
            'attack': report.report_attack,
            'duplicate': report.report_duplicate,
            'hunter_name': hunter.hunter_username if hunter else '',
            'hunter_email': report.hunter_email,
        })

    if request.method == "POST":
        report_id = request.POST.get('report_id', '').strip().upper()
        if len(report_id) != 12 or not report_id.isalnum():
            messages.error(request, "Invalid Report ID format (expected 12 alphanumeric characters).")
            return redirect(reverse('setting') + '#troubleshoot')
        try:
            report = BugReport.objects.get(report_id=report_id)
        except BugReport.DoesNotExist:
            messages.error(request, f"Report {report_id} was not found.")
            return redirect(reverse('setting') + '#troubleshoot')

        title = request.POST.get('title', '').strip()
        endpoint = request.POST.get('endpoint', '').strip()
        attack = request.POST.get('attack', '').strip()
        status_raw = request.POST.get('status', '').strip()
        hunter_name = request.POST.get('hunter_name', '').strip()
        duplicate = 1 if request.POST.get('duplicate') == '1' else 0

        if not title:
            messages.error(request, "Title cannot be empty.")
            return redirect(reverse('setting') + '#troubleshoot')
        if len(title) > 255 or len(endpoint) > 255 or len(attack) > 255:
            messages.error(request, "Title, endpoint, and attack type must each be 255 characters or fewer.")
            return redirect(reverse('setting') + '#troubleshoot')
        if len(hunter_name) > 50:
            messages.error(request, "Hunter name must be 50 characters or fewer.")
            return redirect(reverse('setting') + '#troubleshoot')
        try:
            status = int(status_raw)
        except (TypeError, ValueError):
            messages.error(request, "Invalid status selection.")
            return redirect(reverse('setting') + '#troubleshoot')
        if not ReportStatus.objects.filter(status_id=status).exists():
            messages.error(request, "Selected status does not exist.")
            return redirect(reverse('setting') + '#troubleshoot')

        hunter = BugHunter.objects.filter(hunter_email=report.hunter_email).first()
        if hunter and not hunter_name:
            messages.error(request, "Hunter name cannot be empty.")
            return redirect(reverse('setting') + '#troubleshoot')

        old = (report.report_title, report.report_status, report.report_endpoint, report.report_attack, report.report_duplicate)
        report.report_title = title
        report.report_status = status
        report.report_endpoint = endpoint
        report.report_attack = attack
        report.report_duplicate = duplicate
        if not duplicate:
            report.report_duplicate_of = ''
        report.save(update_fields=['report_title', 'report_status', 'report_endpoint', 'report_attack', 'report_duplicate', 'report_duplicate_of'])

        hunter_change = ""
        if hunter and hunter_name != hunter.hunter_username:
            old_hunter_name = hunter.hunter_username
            hunter.hunter_username = hunter_name
            hunter.save(update_fields=['hunter_username'])
            hunter_change = f" | hunter_name: '{old_hunter_name}' -> '{hunter_name}' ({report.hunter_email})"

        logging.getLogger("Gerologger").info(
            f"REPORT OVERRIDE {report_id} by {request.user.username} | "
            f"title: '{old[0]}' -> '{title}' | status: {old[1]} -> {status} | "
            f"endpoint: '{old[2]}' -> '{endpoint}' | attack: '{old[3]}' -> '{attack}' | "
            f"duplicate: {old[4]} -> {duplicate}" + hunter_change)
        messages.success(request, f"Report {report_id} fields updated successfully.")
        return redirect(reverse('setting') + '#troubleshoot')

    return redirect(reverse('setting') + '#troubleshoot')


def _hunter_report_stats(hunter):
    reports = BugReport.objects.filter(hunter_email__iexact=hunter.hunter_email)
    completed = [r for r in reports if r.report_status == COMPLETED_STATUS]
    return len(completed), sum(max(0, int(r.report_severity)) for r in completed)


def _hall_of_fame_log(request, action, hunter, old_score, old_hidden):
    email = hunter.hunter_email if hunter else "-"
    new_score = hunter.hunter_scores if hunter else old_score
    new_hidden = hunter.hunter_hidden if hunter else old_hidden
    logging.getLogger("Gerologger").info(
        f"HALL OF FAME {action} by {request.user.username} | {email} | "
        f"score {old_score} -> {new_score} | hidden {old_hidden} -> {new_hidden}")


def _recompute_hunter(hunter):
    reports = list(BugReport.objects.select_for_update().filter(
        hunter_email__iexact=hunter.hunter_email))
    total = 0
    for report in reports:
        points = max(0, int(report.report_severity)) if report.report_status == COMPLETED_STATUS else 0
        total += points
        if report.report_score_awarded != points:
            BugReport.objects.filter(report_id=report.report_id).update(
                report_score_awarded=points)
    hunter.hunter_scores = total
    hunter.save(update_fields=['hunter_scores'])
    return total


@login_required
def HallOfFameAdmin(request):
    if not request.user.is_superuser:
        if request.method == "GET":
            return JsonResponse({'ok': False, 'error': 'Forbidden'}, status=403)
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('setting')

    if request.method == "GET":
        query = request.GET.get('q', '').strip()
        hunters = BugHunter.objects.all()
        if query:
            hunters = hunters.filter(Q(hunter_email__icontains=query) |
                                     Q(hunter_username__icontains=query))
        rows = []
        for hunter in hunters.order_by('-hunter_scores')[:20]:
            completed, recomputed = _hunter_report_stats(hunter)
            rows.append({
                'public_key': hunter.pk,
                'email': hunter.hunter_email,
                'name': hunter.hunter_username,
                'score': hunter.hunter_scores,
                'hidden': hunter.hunter_hidden,
                'completed_reports': completed,
                'recomputed_score': recomputed,
                'has_reports': BugReport.objects.filter(
                    hunter_email__iexact=hunter.hunter_email).exists(),
            })
        return JsonResponse({'ok': True, 'hunters': rows})

    if request.method == "POST":
        action = request.POST.get('action', '').strip()
        target = reverse('setting') + '#troubleshoot'

        if action == "recompute_all":
            if request.POST.get('confirm', '').strip() != "RECOMPUTE":
                messages.error(request, "Type RECOMPUTE to confirm recomputing every hunter.")
                return redirect(target)
            with transaction.atomic():
                count = 0
                for hunter in BugHunter.objects.select_for_update().all():
                    _recompute_hunter(hunter)
                    count += 1
            logging.getLogger("Gerologger").info(
                f"HALL OF FAME recompute_all by {request.user.username} | "
                f"{count} hunter(s) | score recomputed from completed reports")
            messages.success(request, f"Recomputed scores for {count} hunter(s) from their completed reports.")
            return redirect(target)

        try:
            hunter_id = int(request.POST.get('hunter_id', ''))
        except (TypeError, ValueError):
            messages.error(request, "Invalid hunter selection.")
            return redirect(target)

        hunter = BugHunter.objects.filter(pk=hunter_id).first()
        if hunter is None:
            messages.error(request, "That bug hunter was not found.")
            return redirect(target)

        old_score, old_hidden = hunter.hunter_scores, hunter.hunter_hidden

        if action == "set_score":
            raw = request.POST.get('score', '').strip()
            try:
                score = int(raw)
            except (TypeError, ValueError):
                messages.error(request, "Score must be a whole number.")
                return redirect(target)
            if score < 0 or score > 1000000:
                messages.error(request, "Score must be between 0 and 1000000.")
                return redirect(target)
            hunter.hunter_scores = score
            hunter.save(update_fields=['hunter_scores'])
            messages.success(request, f"Score for {hunter.hunter_email} set to {score}.")

        elif action in ("hide", "unhide"):
            hunter.hunter_hidden = (action == "hide")
            hunter.save(update_fields=['hunter_hidden'])
            if hunter.hunter_hidden:
                messages.success(request, f"{hunter.hunter_email} is now hidden from the Hall of Fame.")
            else:
                messages.success(request, f"{hunter.hunter_email} is shown in the Hall of Fame again.")

        elif action == "recompute":
            with transaction.atomic():
                locked = BugHunter.objects.select_for_update().get(pk=hunter.pk)
                total = _recompute_hunter(locked)
            hunter.refresh_from_db()
            messages.success(request, f"Score for {hunter.hunter_email} recomputed to {total} from completed reports.")

        elif action == "delete":
            if BugReport.objects.filter(hunter_email__iexact=hunter.hunter_email).exists():
                messages.error(request, "This hunter has reports. Hide them instead, so certificates can still be resent.")
                return redirect(target)
            email = hunter.hunter_email
            _hall_of_fame_log(request, "delete", hunter, old_score, old_hidden)
            hunter.delete()
            messages.success(request, f"Bug hunter {email} deleted.")
            return redirect(target)

        else:
            messages.error(request, "Unknown Hall of Fame action.")
            return redirect(target)

        _hall_of_fame_log(request, action, hunter, old_score, old_hidden)
        return redirect(target)

    return redirect(reverse('setting') + '#troubleshoot')


@login_required
def ReviewerDelete(request,public_id):
    if not request.user.is_superuser:
        logging.getLogger("Gerologger").warning("BLOCKED unauthorized reviewer-delete of " + str(public_id) + " by " + str(request.user.username))
        messages.error(request,"You are not authorized to perform this action.")
        return redirect('setting')

    if request.method == "POST":
        try:
            try:
                uid = uuid.UUID(str(public_id))
            except (ValueError, TypeError, AttributeError):
                logging.getLogger("Gerologger").warning("BLOCKED reviewer-delete of malformed identifier '" + str(public_id) + "' by " + str(request.user.username))
                messages.error(request,"User not found or cannot be deleted.")
                return redirect('setting')

            target = User.objects.filter(profile__public_id=uid, is_superuser=False).first()
            if target is None:
                logging.getLogger("Gerologger").warning("BLOCKED reviewer-delete of protected/unknown user " + str(public_id) + " by " + str(request.user.username))
                messages.error(request,"User not found or cannot be deleted.")
                return redirect('setting')

            username = target.username
            target.delete()
            messages.success(request,"User is deleted successfully!")
            logging.getLogger("Gerologger").info("USER " + username + " (public_id " + str(public_id) + ") SUCCESSFULLY DELETED BY " + str(request.user.username))
            return redirect('dashboard')

        except Exception as e:
            logging.getLogger("Gerologger").error(str(e))
            messages.error(request,"Something wrong. The delete operation is unsuccessful. Please report to the Admin!")
            return redirect('setting')

        return redirect('setting')

    return render(request,'setting.html')

@login_required
def NotificationDelete(request,service):
    if not request.user.is_superuser:
        logging.getLogger("Gerologger").warning("BLOCKED unauthorized notification-delete of '" + str(service) + "' by " + str(request.user.username))
        messages.error(request,"You are not authorized to perform this action.")
        return redirect('setting')

    if request.method == "POST":
        try:
            if Webhook.objects.filter(webhook_service=service).count() != 0:
                Webhook.objects.filter(webhook_service=service).delete()
                messages.success(request,"Notification Media is deleted successfully!")
                logging.getLogger("Gerologger").info("Notification '" + str(service) + "' deleted by " + str(request.user.username))
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

def rulescontext(request,):
    staticrules = StaticRules.objects.get(pk=1)

    # COMPANY NAME
    THEME = Personalization.objects.get(personalize_id=1)
    company_name = THEME.company_name

    return render(request,'rules.html',{'RDP':staticrules.RDP,'bountyterms':staticrules.bountyterms,'inscope':staticrules.inscope,'outofscope':staticrules.outofscope,'reportguidelines':staticrules.reportguidelines,'faq':staticrules.faq,'company_name':company_name})


def submit_page_context():
    return {
        'comment_limit': gerofilter.COMMENT_LIMIT,
        'self_update_limit': gerofilter.SELF_UPDATE_LIMIT,
        'appeal_limit': gerofilter.APPEAL_LIMIT,
        'appeal_window_days': APPEAL_WINDOW_DAYS,
        'max_pdf_mb': gerofilter.MAX_PDF_BYTES // 1000000,
        'endpoint_max': gerofilter.FIELD_LIMITS['endpoint'][1],
        'title_max': gerofilter.FIELD_LIMITS['title'][1],
    }


def emailcontext(request,):
    mailbox = MailBox.objects.filter(mailbox_id=1).first()
    mailbox_email = mailbox.email if mailbox and mailbox.email else ""
    if mailbox_email:
        template = format_html(
            "Send your email to {} using the formats below.", mailbox_email)
    else:
        template = "Currently the company hasn't set their email yet. Please contact the admin/wait for the mailbox setup."

    THEME = Personalization.objects.get(personalize_id=1)
    company_name = THEME.company_name

    context = {'template': template, 'mailbox_email': mailbox_email,
               'company_name': company_name}
    context.update(submit_page_context())

    return render(request, 'submit.html', context)

def halloffame(request,):
    bughunters = BugHunter.objects.alias(
        points=Sum('hunter_scores')
    ).exclude(hunter_scores=0).exclude(hunter_hidden=True).order_by('-points')

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