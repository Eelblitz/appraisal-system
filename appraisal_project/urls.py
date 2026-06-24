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
    path('', include('organisations.urls', namespace='organisations')),
    path('', lambda request: redirect('accounts:login'), name='home'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)