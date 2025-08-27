from django.urls import path
from .views import CdRegisterAPIView, CdGatherInfoAPIView, CdRequestTradeAPIView

urlpatterns = [
    path('cd/register/', CdRegisterAPIView.as_view(), name='cd_register'),
    path('cd/info/', CdGatherInfoAPIView.as_view(), name='cd_list'),
    path('cd/info/<slug:name>/', CdGatherInfoAPIView.as_view(), name='cd_detail'),
    path('cd/request/<str:product>/<int:quantity>/', CdRequestTradeAPIView.as_view(), name='cd_request'),
]