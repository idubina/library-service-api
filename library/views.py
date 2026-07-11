from rest_framework import viewsets
from library.serializers import BookSerializer
from library.models import Book
from library.permissions import IsAdminOrAuthenticatedOrReadOnly


class BookApiView(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrAuthenticatedOrReadOnly,)
