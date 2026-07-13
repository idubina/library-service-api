import stripe
from django.db import transaction
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from library.serializers import (
    BookSerializer,
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingBookReturnSerializer,
    BorrowingCreateSerializer,
)
from library.models import Book, Borrowing, Payment
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
        if self.action == "create":
            return BorrowingCreateSerializer
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                description="Filter by borrowing status [ex. ?is_active=True]",
                type=bool,
            ),
            OpenApiParameter(
                name="users",
                description="Filter by user ids (available only for staff) [ex. ?users=2,5]",
                type={"type": "list", "items": {"type": "number"}},
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get Borrowing List"""
        return super().list(request, *args, **kwargs)

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


class PaymentSuccessView(APIView):

    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"detail": "Session ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(session_id=session_id)
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            if payment.status != Payment.Status.PAID:
                payment.status = Payment.Status.PAID
                payment.save(update_fields=["status"])

            return Response(
                {"detail": "Payment was successful."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Payment has not been completed."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PaymentCancelView(APIView):

    def get(self, request):
        return Response(
            {
                "detail": (
                    "Payment was paused. "
                    "You can complete it later using the session URL."
                )
            },
            status=status.HTTP_200_OK,
        )
