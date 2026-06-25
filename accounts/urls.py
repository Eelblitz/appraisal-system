from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Organisation user management (HR Admin)
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.create_user_view, name='create_user'),
    path('users/<int:pk>/edit/', views.edit_user_view, name='edit_user'),
    path('users/<int:pk>/detail/', views.user_detail_view, name='user_detail'),

    # Platform user management (Super Admin only)
    path(
        'platform/users/',
        views.platform_user_list,
        name='platform_user_list'
    ),
    path(
        'platform/users/<int:pk>/reset-password/',
        views.platform_reset_password,
        name='platform_reset_password'
    ),
]