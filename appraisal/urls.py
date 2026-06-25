from django.urls import path
from . import views

app_name = 'appraisal'

urlpatterns = [
    # HR views
    path(
        'assign/',
        views.assign_appraisals,
        name='assign_appraisals'
    ),
    path(
        'all/',
        views.appraisal_list_hr,
        name='appraisal_list_hr'
    ),

    # Employee views
    path(
        'my/',
        views.my_appraisals,
        name='my_appraisals'
    ),
    path(
        'team/',
        views.team_appraisals,
        name='team_appraisals'
    ),
    path(
        'detail/<int:pk>/',
        views.appraisal_detail,
        name='detail'
    ),

    # Form parts (placeholders for now — built next)
    path('part1/<int:pk>/',
    views.part1_form,
    name='part1_form'
),
    path(
        'part2/<int:pk>/',
        views.my_appraisals,
        name='part2_form'
    ),
    path(
        'part3/<int:pk>/',
        views.my_appraisals,
        name='part3_form'
    ),
    path(
        'part4/<int:pk>/',
        views.my_appraisals,
        name='part4_form'
    ),
]