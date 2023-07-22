from django.shortcuts import render
from django.db.models import Sum
from .models import DashboardsBughunter, DashboardsStaticrules, PrerequisitesMailbox

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
    ).exclude(hunter_scores=0).order_by('-points') #descending use '-'

    return render(request, 'halloffame.html',{'bughunters':bughunters})

def notfound_404(request, exception):
    return render(request, 'notfound.html', status=404)
