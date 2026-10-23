from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            role=validated_data.get("role", "PATIENT"),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user
