from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

app_name = 'payments'

@login_required
def coming_soon(request):
    return render(request, 'coming_soon.html', {'page': 'Payments'})

urlpatterns = [
    path('my/', coming_soon, name='my_payments'),
    path('all/', coming_soon, name='all_payments'),
    path('initiate/<int:pk>/', coming_soon, name='initiate'),
]