from django.urls import path

from apps.portfolio.views import MainDashboardView, MainDashboardUserBalanceView, UserDashboardView

urlpatterns = [
    path('MainDashboard/', MainDashboardView.as_view(), name='main_dashboard'),
    path('MainDashboardOfUsers/', MainDashboardUserBalanceView.as_view(), name='main_dashboard_users'),
    path('UserDashboard/<int:pk>/', UserDashboardView.as_view(), name='user_dashboard'),
]
