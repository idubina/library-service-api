from django.urls import path, include
from rest_framework import routers
from library.views import BookApiView

app_name = "library"

router = routers.DefaultRouter()

router.register("books", BookApiView)

urlpatterns = [
    path("", include(router.urls)),
]
