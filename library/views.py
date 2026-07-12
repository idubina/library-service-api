from django.db import transaction
from django.utils.timezone import now
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from library.serializers import (
    BookSerializer,
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingBookReturnSerializer,
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
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def _params_to_ints(qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        if self.action == "return_book":
            return BorrowingBookReturnSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        else:
            users = self.request.query_params.get("users")
            if users:
                users_ids = self._params_to_ints(users)
                queryset = queryset.filter(user__id__in=users_ids)

        is_active = self.request.query_params.get("is_active")
        if is_active:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            if is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        if self.action == "list":
            queryset = queryset.select_related("user", "book")
        return queryset

    @action(
        detail=True,
        methods=["post"],
        url_path="return",
        permission_classes=(IsAdminUser,),
    )
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        with transaction.atomic():
            if borrowing.is_active:

                borrowing.actual_return_date = now()
                borrowing.save(update_fields=["actual_return_date"])

                book = borrowing.book
                book.inventory += 1
                book.save(update_fields=["inventory"])

                serializer = self.get_serializer(borrowing)
                return Response(serializer.data, status.HTTP_200_OK)
        return Response(
            {"detail": "This book is not currently borrowed."},
            status.HTTP_400_BAD_REQUEST,
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
