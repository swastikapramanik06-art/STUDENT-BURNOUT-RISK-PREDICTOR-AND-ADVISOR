from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- Authentication & Main Pages ---
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'), # Added registration
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'), # Added logout

    # --- Password Reset Routes (Keep these!) ---
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="accounts/reset_password.html"), 
         name="reset_password"),
    
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="accounts/reset_password_done.html"), 
         name="password_reset_done"),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="accounts/reset_password_confirm.html"), 
         name="password_reset_confirm"),
    
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="accounts/reset_password_complete.html"), 
         name="password_reset_complete"),
]