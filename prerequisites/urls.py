from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.LoginForm, name="login"),
    path("password_reset", views.PasswordReset, name="password_reset"),
    path("password_reset/sent", auth_views.PasswordResetDoneView.as_view(template_name='password_reset_forms/password_reset_done.html'),name='password_reset_done'),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_forms/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_forms/password_reset_complete.html'), name='password_reset_complete'),
]