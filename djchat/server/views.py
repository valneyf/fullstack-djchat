from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from .serializer import ServerSerializer
from .models import Server


class ServerListViewSet(viewsets.ViewSet):

    queryset = Server.objects.all()

    def list(self, request):
        category = request.query_params.get('category')

        if category:
            self.queryset = self.queryset.filter(category=category)

        serializer = ServerSerializer(self.queryset, many=True)
        return Response(serializer.data)