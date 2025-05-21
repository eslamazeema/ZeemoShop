from django.contrib import admin
from django.urls import path, include
from products.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='home'),
    path('products/', include('products.urls')),
]
