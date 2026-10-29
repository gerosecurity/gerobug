from django.shortcuts import render
from django.db.models import Sum
from .models import DashboardsBughunter, DashboardsStaticrules, PrerequisitesMailbox, Personalization
from django.utils.html import format_html
from django.views.generic import TemplateView

def rulescontext(request,):
    staticrules = DashboardsStaticrules.objects.get(pk=1)

    # COMPANY NAME
    THEME = Personalization.objects.get(personalize_id=1)
    company_name = THEME.company_name

    return render(request,'rules.html',{'RDP':staticrules.rdp,'bountyterms':staticrules.bountyterms,'inscope':staticrules.inscope,'outofscope':staticrules.outofscope,'reportguidelines':staticrules.reportguidelines,'faq':staticrules.faq,'company_name':company_name})


COMMENT_LIMIT = 10
SELF_UPDATE_LIMIT = 3
APPEAL_LIMIT = 3
APPEAL_WINDOW_DAYS = 30
MAX_PDF_BYTES = 25_000_000
ENDPOINT_MAX = 255
TITLE_MAX = 150


def submit_page_context():
    return {
        'comment_limit': COMMENT_LIMIT,
        'self_update_limit': SELF_UPDATE_LIMIT,
        'appeal_limit': APPEAL_LIMIT,
        'appeal_window_days': APPEAL_WINDOW_DAYS,
        'max_pdf_mb': MAX_PDF_BYTES // 1000000,
        'endpoint_max': ENDPOINT_MAX,
        'title_max': TITLE_MAX,
    }


def emailcontext(request,):
    mailbox = PrerequisitesMailbox.objects.filter(mailbox_id=1).first()
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
    bughunters = DashboardsBughunter.objects.alias(
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