from rest_framework import viewsets
from library.serializers import BookSerializer
from library.models import Book


class BookApiView(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
