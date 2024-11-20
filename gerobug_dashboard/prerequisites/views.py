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
from django.urls import reverse
from django.contrib import messages
from django.template.loader import render_to_string
from prerequisites.models import MailBox

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from geromail import mail_templates

def LoginForm(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # messages.success(request,"Login successful!")
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
                messages.success(request,"Login successful!")
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

            if MailBox.objects.filter(mailbox_id=1)[0].email == "":
                messages.error(request,"Admin has not set up the mailbox setting. Please contact them/wait for the setup is finished!")
                return redirect("password_reset")
            
            else:
                if check_email.exists():
                    for user in check_email:
                        url = request.build_absolute_uri(reverse('rules'))
                        domain = url[:len(url)-1]
                        uid = urlsafe_base64_encode(force_bytes(user.pk))
                        token = default_token_generator.make_token(user)

                        subject = mail_templates.subjectlist[9999]
                        body = mail_templates.messagelist[9999]
                        body = body.replace("~DOMAIN~", str(domain))
                        body = body.replace("~UID~", str(uid))
                        body = body.replace("~TOKEN~", str(token))
 
                        # SEND EMAIL
                        mailbox     = MailBox.objects.get(mailbox_id=1)
                        EMAIL       = mailbox.email
                        PWD         = mailbox.password
                        TYPE        = mailbox.mailbox_type
                        SMTP_SERVER = mailbox.mailbox_smtp
                        SMTP_PORT   = mailbox.mailbox_smtp_port

                        message = MIMEMultipart("alternative")
                        message["From"] = mailbox.email
                        message["To"] = user.email
                        message["Subject"] = subject
                        message_body = MIMEText(body, "html")
                        message.attach(message_body)

                        if EMAIL == "" or PWD == "":
                            pass

                        else:
                            try:
                                connection = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
                                connection.login(EMAIL, PWD)
                                connection.sendmail(EMAIL, user.email, message.as_string())
                                connection.close()
                                
                            except Exception as e:
                                with smtplib.SMTP(host=SMTP_SERVER, port=SMTP_PORT) as server:
                                    server.starttls()
                                    server.login(EMAIL, PWD)
                                    server.sendmail(EMAIL, user.email, message.as_string())
                                    server.close()
                    
                        logging.getLogger("Gerologger").info('Password Reset: Sent Link Successfully')
                        return redirect("/login/password_reset/sent")
                    
                else:
                    logging.getLogger("Gerologger").info('Password Reset: Email Not Found')
                    return redirect("/login/password_reset/sent")
                
    password_resets = PasswordResetForm()
    return render(request=request, template_name="password_reset_forms/password_reset.html", context={"password_reset_form":password_resets})

