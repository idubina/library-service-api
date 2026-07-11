from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from users.serializers import UserSerializer


class CreateUserApiView(generics.CreateAPIView):
    serializer_class = UserSerializer


class MangeUserApiView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
