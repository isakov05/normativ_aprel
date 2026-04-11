from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TaskViewSet, RegisterAPIView, LoginAPIView, LogoutAPIView

router = DefaultRouter()
router.register('tasks', TaskViewSet)

urlpatterns = router.urls

urlpatterns += [
    path('register/', RegisterAPIView.as_view()),
    path('login/', LoginAPIView.as_view()),
    path('logout/', LogoutAPIView.as_view()),
]