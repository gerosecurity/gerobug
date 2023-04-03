from tabnanny import check
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.db.models.query_utils import Q
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib import messages
from django.template.loader import render_to_string
from gerobug.settings import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
from prerequisites.models import MailBox


def LoginForm(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            messages.success(request,"Login successful!")
            return redirect('dashboard')
        else:
            return redirect('rules')
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("dashboard")
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="login.html", context={"login_form":form})

def PasswordReset(request):
    if request.method == "POST":
        password_resets = PasswordResetForm(request.POST)
        if password_resets.is_valid():
            param = password_resets.cleaned_data['email']
            check_email = User.objects.filter(Q(email=param))
            if check_email.exists():
                for user in check_email:
                    subject = "Gerobug Password Reset"
                    body = "password_reset_forms/email_template.txt"
                    c = {
                        "email": user.email,
                        "domain": "127.0.0.1:7331", #temporary, needs to be updated
                        "site_name": "Gerobug",
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        "token": default_token_generator.make_token(user),
                        "protocol": "http" #next time, use HTTPS is a must!
                    }
                    email = render_to_string(body, c)
                    try:
                        mailbox = MailBox.objects.get(mailbox_id=1)
                        EMAIL_USE_TLS = True
                        EMAIL_HOST_USER = mailbox.email
                        EMAIL_HOST_PASSWORD = mailbox.password
                        
                        send_mail(subject, email, EMAIL_HOST_USER, [user.email], fail_silently=False, auth_user=EMAIL_HOST_USER, auth_password=EMAIL_HOST_PASSWORD)

                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')

                    return redirect("/login/password_reset/sent")
            else:
                messages.error(request,"Email does not exists!")
    password_resets = PasswordResetForm()
    return render(request=request, template_name="password_reset_forms/password_reset.html", context={"password_reset_form":password_resets})

