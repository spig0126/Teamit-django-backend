from rest_framework import generics

from .models import *
from .serializers import *

class ArticleListAPIView(generics.ListCreateAPIView):
     serializer_class = ArticleCreateSerializer
     queryset = Article.objects.all().order_by('created_at')
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)

class EventArticleListAPIView(generics.ListCreateAPIView):
     serializer_class = EventArticleCreateSerializer
     queryset = EventArticle.objects.all().order_by('created_at')
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
        