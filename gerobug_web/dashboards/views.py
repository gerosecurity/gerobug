from django.shortcuts import render
from django.db.models import Sum
from .models import DashboardsBughunter, DashboardsStaticrules, PrerequisitesMailbox, Personalization
from django.views.generic import TemplateView

def rulescontext(request,):
    staticrules = DashboardsStaticrules.objects.get(pk=1)
    return render(request,'rules.html',{'RDP':staticrules.rdp,'bountyterms':staticrules.bountyterms,'inscope':staticrules.inscope,'outofscope':staticrules.outofscope,'reportguidelines':staticrules.reportguidelines,'faq':staticrules.faq})

def emailcontext(request,):
    if PrerequisitesMailbox.objects.filter(mailbox_id=1)[0].email != "":
        email = PrerequisitesMailbox.objects.filter(mailbox_id=1)[0].email
        template = "Submit your email to <strong>"+ email +"</strong> using the templates below..."
    else:
        template = "Currently the company hasn't set their email yet. Please contact the admin/wait for the mailbox setup."
    return render(request, 'submit.html',{'template':template})

def halloffame(request,):
    bughunters = DashboardsBughunter.objects.alias(
        points=Sum('hunter_scores')
    ).exclude(hunter_scores=0).order_by('-points')

    return render(request, 'halloffame.html',{'bughunters':bughunters})

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