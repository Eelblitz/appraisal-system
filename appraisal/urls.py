from django.urls import path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

app_name = 'appraisal'

# Temporary placeholder view — returns a simple "coming soon" page
# We use this so base.html doesn't crash while we build each section
@login_required
def coming_soon(request):
    return render(request, 'coming_soon.html', {'page': 'Appraisal'})

urlpatterns = [
    path('my/', coming_soon, name='my_appraisals'),
    path('team/', coming_soon, name='team_appraisals'),
    path('detail/<int:pk>/', coming_soon, name='detail'),
    path('part1/<int:pk>/', coming_soon, name='part1_form'),
    path('part2/<int:pk>/', coming_soon, name='part2_form'),
    path('part3/<int:pk>/', coming_soon, name='part3_form'),
    path('part4/<int:pk>/', coming_soon, name='part4_form'),
]