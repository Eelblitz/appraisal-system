from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/toggle/', views.category_toggle, name='category_toggle'),

    # Cycles
    path('cycles/', views.cycle_list, name='cycle_list'),
    path('cycles/create/', views.cycle_create, name='cycle_create'),
    path('cycles/<int:pk>/edit/', views.cycle_edit, name='cycle_edit'),
    path('cycles/<int:pk>/status/', views.cycle_status_change, name='cycle_status'),

    # Aspects
    path('aspects/', views.aspect_list, name='aspect_list'),
    path('aspects/<int:pk>/edit/', views.aspect_edit, name='aspect_edit'),

    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
]