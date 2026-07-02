from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('documentation/', views.download_documentation, name='documentation'),
    path('contact/', views.contact_submit, name='contact_submit'),
]