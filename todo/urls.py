from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/', include('task.urls')),   # 👈 المسار الرئيسي للـ APIs الخاصة بالمهام
]
