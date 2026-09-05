from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('dashboard/', include('apps.workflows.urls_ui')),
    path('api/v1/tenants/', include('apps.tenants.urls')),
    path('api/v1/workflows/', include('apps.workflows.urls')),
]
