from django.urls import path
from .views import LoginView, MeView, HealthView, InfoView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # /register/ supprimé — géré par le service User via RabbitMQ
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),

     # Endpoints pour Eureka / Gateway
    path('health/', HealthView.as_view(), name='health'),
    path('info/', InfoView.as_view(), name='info'),
]
