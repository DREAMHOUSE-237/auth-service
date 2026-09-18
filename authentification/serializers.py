# auth_app/serializers.py
"""
Serializers du service Auth — après refactorisation.

RegisterSerializer supprimé : l'inscription est gérée par le service User.
Seul LoginSerializer reste nécessaire.
"""
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
