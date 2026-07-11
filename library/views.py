from rest_framework import viewsets, mixins
from library.serializers import (
    BookSerializer,
    BorrowingSerializer,
    BorrowingListSerializer,
)
from library.models import Book, Borrowing
from library.permissions import IsAdminOrAuthenticatedOrReadOnly


class BookApiView(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrAuthenticatedOrReadOnly,)


class BorrowingApiView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.select_related("user", "book")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
