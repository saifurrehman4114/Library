from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api.views import UserViewSet, AuthorViewSet, BookViewSet, FavoriteBookViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'books', BookViewSet)
router.register(r'favorites', FavoriteBookViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]