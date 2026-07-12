from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils.timezone import now

from library.models import Book, Borrowing
from library.serializers import (
    BookSerializer,
    BorrowingSerializer,
    BorrowingListSerializer,
)
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

BORROWING_URL = reverse("library:borrowing-list")


def get_detail_url(borrowing_id: int):
    return reverse("library:borrowing-detail", args=[borrowing_id])


def sample_book(**params):
    defaults = {
        "title": "testTitle",
        "author": "testAuthor",
        "cover": "SOFT",
        "inventory": 20,
        "daily_fee": 15.23,
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def sample_borrowing_1(user=None, **params):
    if user is None:
        user = get_user_model().objects.create_user(
            email="testuser@user.com", password="testuser123"
        )
    defaults = {
        "expected_return_date": now().date() + timedelta(days=1),
        "book": sample_book(),
        "user": user,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


def sample_borrowing_2(user=None, **params):
    if user is None:
        user = get_user_model().objects.create_user(
            email="testuser3@user.com", password="testuser1233"
        )
    defaults = {
        "expected_return_date": now().date() + timedelta(days=1),
        "book": sample_book(title="Test2"),
        "user": user,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


class UnauthenticatedBorrowingApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):

        res = self.client.get(BORROWING_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testuser2@user.com", password="test-user1234"
        )
        self.client.force_authenticate(self.user)

    def test_get_only_user_borrowing_list(self):

        user_borrowing = sample_borrowing_1(user=self.user)
        user_2_borrowing = sample_borrowing_2()

        res = self.client.get(BORROWING_URL)
        serializer_user_borrowing = BorrowingListSerializer(user_borrowing)
        serializer_user_2_borrowing = BorrowingListSerializer(user_2_borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_user_borrowing.data, res.data)
        self.assertNotIn(serializer_user_2_borrowing.data, res.data)

    def test_retrieve_only_user_borrowing_detail(self):
        user_borrowing = sample_borrowing_1(user=self.user)
        user_2_borrowing = sample_borrowing_2()

        res_user_borrowing = self.client.get(get_detail_url(user_borrowing.id))
        res_user_2_borrowing = self.client.get(get_detail_url(user_2_borrowing.id))

        self.assertEqual(res_user_borrowing.status_code, status.HTTP_200_OK)
        self.assertEqual(res_user_2_borrowing.status_code, status.HTTP_404_NOT_FOUND)

        serializer = BorrowingSerializer(user_borrowing)

        self.assertEqual(serializer.data, res_user_borrowing.data)

    def test_borrowing_create(self):

        payload = {
            "expected_return_date": now().date() + timedelta(days=1),
            "book": sample_book().id,
        }
        res = self.client.post(BORROWING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        borrowing = Borrowing.objects.get(id=res.data["id"])

        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(
            borrowing.expected_return_date, payload["expected_return_date"]
        )
        self.assertEqual(borrowing.book.id, payload["book"])

    def test_borrowing_with_date_in_the_past_not_allowed(self):
        payload = {
            "expected_return_date": now().date() - timedelta(days=1),
            "book": sample_book().id,
        }
        res = self.client.post(BORROWING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            res.data["non_field_errors"][0],
            "Expected return date cannot be in the past.",
        )
        self.assertFalse(Borrowing.objects.exists())

    def test_borrowing_with_book_that_not_in_stock_not_allowed(self):
        payload = {
            "expected_return_date": now().date() + timedelta(days=1),
            "book": sample_book(inventory=0).id,
        }

        res = self.client.post(BORROWING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            res.data["non_field_errors"][0],
            "The selected book is currently unavailable.",
        )
        self.assertFalse(Borrowing.objects.exists())

    def test_decreasing_selected_book_inventory_after_creating_borrowing(self):
        book = sample_book()
        book_inventory_before_borrowing = book.inventory
        payload = {
            "expected_return_date": now().date() + timedelta(days=1),
            "book": book.id,
        }
        res = self.client.post(BORROWING_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        book.refresh_from_db()

        self.assertEqual(book.inventory, book_inventory_before_borrowing - 1)


class AdminBorrowingApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testadmin@admin.com", password="test-admin1234", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_get_all_user_borrowing_list(self):

        user_1 = get_user_model().objects.create_user(
            email="testuser2@user.com", password="test-user1234"
        )
        sample_borrowing_1(user=user_1)
        sample_borrowing_2()

        res = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.all()
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_borrowing_delete_not_allowed(self):

        borrowing = sample_borrowing_1()

        res = self.client.delete(get_detail_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_borrowing_update_not_allowed(self):

        borrowing = sample_borrowing_1()

        payload = {
            "expected_return_date": now().date() + timedelta(days=3),
            "book": sample_book(title="Test5").id,
        }

        res = self.client.put(get_detail_url(borrowing.id), payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
