from rest_framework import serializers

from user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'phone_number')
        model = User
