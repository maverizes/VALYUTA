from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView
from user.serializers import UserSerializer
from .models import User


class UserList(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
