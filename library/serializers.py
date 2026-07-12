from django.db import transaction
from django.utils.timezone import now
from rest_framework import serializers
from library.models import Book, Borrowing


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
