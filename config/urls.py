from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(
        title='Normativ API',
        default_version='v1',
    ),
    public=True,
    permission_classes=[AllowAny],
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tasks.urls')),
    path('api/token/', obtain_auth_token)
]
urlpatterns+=[
    path('api/token', TokenObtainPairView.as_view()),
    path('api/token/refresh', TokenRefreshView.as_view()),
]
urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
]