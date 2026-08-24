from django.db import transaction
from django.utils.timezone import now
from rest_framework import serializers
from library.models import Book, Borrowing, Payment
from library.services import create_stripe_session


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")


class BorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
            "is_active",
        )
        read_only_fields = ("id", "actual_return_date", "is_active", "user")

    def validate(self, attrs):

        if attrs["expected_return_date"] < now().date():
            raise serializers.ValidationError(
                "Expected return date cannot be in the past."
            )
        if not attrs["book"].inventory > 0:
            raise serializers.ValidationError(
                "The selected book is currently unavailable."
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        book = validated_data["book"]
        book.inventory -= 1
        book.save(update_fields=["inventory"])
        return super().create(validated_data)


class BorrowingListSerializer(BorrowingSerializer):
    book = serializers.StringRelatedField(read_only=True)
    user = serializers.SlugRelatedField(read_only=True, slug_field="email")


class BorrowingBookReturnSerializer(serializers.Serializer):
    pass


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
        )
        read_only_fields = fields


class BorrowingCreateSerializer(BorrowingSerializer):
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta(BorrowingSerializer.Meta):
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
            "is_active",
            "payments",
        )

    @transaction.atomic
    def create(self, validated_data):
        borrowing = super().create(validated_data)

        days = (borrowing.expected_return_date - borrowing.borrow_date.date()).days
        days = max(days, 1)

        money_to_pay = borrowing.book.daily_fee * days

        session = create_stripe_session(borrowing, money_to_pay)

        Payment.objects.create(
            borrowing=borrowing,
            type=Payment.Type.PAYMENT,
            status=Payment.Status.PENDING,
            money_to_pay=money_to_pay,
            session_id=session.id,
            session_url=session.url,
        )

        return borrowing
