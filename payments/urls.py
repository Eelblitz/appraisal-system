from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path(
        'initiate/<int:pk>/',
        views.initiate_payment,
        name='initiate'
    ),
    path(
        'callback/',
        views.payment_callback,
        name='callback'
    ),
    path(
        'my/',
        views.my_payments,
        name='my_payments'
    ),
    path(
        'all/',
        views.all_payments,
        name='all_payments'
    ),
    path(
        'download/<int:pk>/',
        views.download_pdf,
        name='download_pdf'
    ),
]