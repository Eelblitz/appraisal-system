from django.urls import path
from . import views

app_name = 'organisations'

urlpatterns = [
    # Platform level — only superusers
    path(
        'platform/organisations/',
        views.organisation_list,
        name='organisation_list'
    ),
    path(
        'platform/organisations/create/',
        views.organisation_create,
        name='organisation_create'
    ),
    path(
        'platform/organisations/<int:pk>/edit/',
        views.organisation_edit,
        name='organisation_edit'
    ),
    path(
        'platform/organisations/<int:pk>/toggle/',
        views.organisation_toggle,
        name='organisation_toggle'
    ),
    path(
        'platform/organisations/<int:pk>/create-admin/',
        views.create_org_admin,
        name='create_org_admin'
    ),

    # Organisation level — org super_admin sees their own details
    path(
        'org/settings/',
        views.organisation_settings,
        name='settings'
    ),
]