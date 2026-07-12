from django.urls import path, include
from rest_framework import routers
from library.views import BookApiView, BorrowingApiView

app_name = "library"

router = routers.DefaultRouter()

router.register("books", BookApiView),
router.register("borrowings", BorrowingApiView)

urlpatterns = [
    path("", include(router.urls)),
]
