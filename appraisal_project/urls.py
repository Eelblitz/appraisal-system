"""
URL configuration for appraisal_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('core/', include('core.urls', namespace='core')),
    path('hr/', include('hr.urls', namespace='hr')),
    path('appraisal/', include('appraisal.urls', namespace='appraisal')),
    path('payments/', include('payments.urls', namespace='payments')),

    # Root URL — redirects anyone visiting "/" to the login page
    path('', lambda request: redirect('accounts:login'), name='home'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)