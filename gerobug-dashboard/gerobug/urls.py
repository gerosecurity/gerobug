"""gerobug URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from dashboards.views import halloffame,rulescontext,emailcontext

urlpatterns = [
    path('', rulescontext,name="rules"),
    path("submit/",emailcontext,name="submit"),
    path("halloffame/",halloffame,name="halloffame"),
    path('login/', include("prerequisites.urls"),name="login"),
    path('dashboard/', include("dashboards.urls"),name="dashboard"),
    
    #path('accounts/', include('django.contrib.auth.urls')),
    #path('admin/', admin.site.urls),
]
