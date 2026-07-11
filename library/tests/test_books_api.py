from decimal import Decimal

from django.contrib.auth import get_user_model
from library.models import Book
from library.serializers import BookSerializer
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

BOOK_URL = reverse("library:book-list")


def get_detail_url(book_id: int):
    return reverse("library:book-detail", args=[book_id])


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


class UnauthenticatedBookApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):

        sample_book()
        res = self.client.get(BOOK_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBookApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testuser@user.com", password="test-user123"
        )
        self.client.force_authenticate(self.user)

    def test_get_book_list(self):

        sample_book()

        res = self.client.get(BOOK_URL)

        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_book_detail(self):

        book = sample_book()

        res = self.client.get(get_detail_url(book.id))

        serializer = BookSerializer(book)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_book_create_forbidden(self):

        payload = {
            "title": "testTitle",
            "author": "testAuthor",
            "cover": "SOFT",
            "inventory": 20,
            "daily_fee": Decimal("15.23"),
        }

        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_book_delete_forbidden(self):

        book = sample_book()

        res = self.client.delete(get_detail_url(book.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_book_update_not_allowed(self):

        book = sample_book()

        payload = {
            "title": "testTitle2",
            "author": "testAuthor2",
            "cover": "HARD",
            "inventory": 20,
            "daily_fee": Decimal("15.23"),
        }

        res = self.client.put(get_detail_url(book.id), payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testadmin@admin.com",
            password="test-admin123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_book_create(self):
        payload = {
            "title": "testTitle",
            "author": "testAuthor",
            "cover": "SOFT",
            "inventory": 20,
            "daily_fee": Decimal("15.23"),
        }

        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        book = Book.objects.get(id=res.data["id"])

        for key in payload:
            self.assertEqual(payload[key], getattr(book, key))

    def test_book_delete(self):
        book = sample_book()

        res = self.client.delete(get_detail_url(book.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_book_update(self):
        book = sample_book()

        payload = {
            "title": "testTitle2",
            "author": "testAuthor2",
            "cover": "HARD",
            "inventory": 20,
            "daily_fee": Decimal("15.23"),
        }

        res = self.client.put(get_detail_url(book.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        book = Book.objects.get(id=res.data["id"])

        for key in payload:
            self.assertEqual(payload[key], getattr(book, key))
