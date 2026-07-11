from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

USER_CREATE_URL = reverse("users:register")
USER_MANAGE_URL = reverse("users:manage")
USER_GET_TOKEN_URL = reverse("users:token_obtain_pair")


class UnauthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_register(self):

        payload = {"email": "test@test.com", "password": "test1234"}

        res = self.client.post(USER_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["email"], payload["email"])
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

    def test_user_get_token(self):
        payload = {"email": "test@test.com", "password": "test1234"}

        get_user_model().objects.create_user(**payload)

        res = self.client.post(USER_GET_TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for token in ["access", "refresh"]:
            self.assertIn(token, res.data)

    def test_user_manage_forbidden(self):

        res = self.client.get(USER_MANAGE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_with_existing_email_fails(self):
        payload = {
            "email": "test@test.com",
            "password": "test1234",
        }
        get_user_model().objects.create_user(**payload)

        res = self.client.post(USER_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_short_password_fails(self):
        payload = {
            "email": "test@test.com",
            "password": "123",
        }

        res = self.client.post(USER_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test1234",
        )
        self.client.force_authenticate(self.user)

    def test_user_manage(self):
        res = self.client.get(USER_MANAGE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.email, res.data["email"])

    def test_user_update(self):
        payload = {"email": "testupdate@test.com", "password": "update1234"}
        res = self.client.put(USER_MANAGE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.email, payload["email"])
        self.assertTrue(self.user.check_password(payload["password"]))
