from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('main-admin/', admin.site.urls),
    path('register/', user_views.RegisterView.as_view(), name='register'),
    path('profile/', user_views.ProfileView.as_view(), name='profile'),
    path('login/', user_views.LoginView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', user_views.AdminView.as_view(), name='admin'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('', include('blog.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),