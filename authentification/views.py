# auth_app/views.py
"""
Vues du service Auth — après refactorisation.

L'inscription (/register/) est supprimée de ce service :
le service User est désormais le point d'entrée du register.
Il publie dans RabbitMQ → consume_user_events.py crée l'AuthUser ici.

Ce service expose uniquement :
  POST /login/           — authentification + JWT
  POST /token/refresh/   — rafraîchissement du token (SimpleJWT)
  GET  /me/              — infos du user connecté
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer
from .services.auth_service import AuthService
from rest_framework.permissions import IsAuthenticated, AllowAny


class LoginView(APIView):
    """
    Vue de connexion — vérifie les identifiants et retourne le JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        service = AuthService()

        try:
            tokens = service.login_user(**data)
            return Response(tokens, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(e)
            return Response({"error": "Erreur interne du serveur."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retourne les infos du user connecté (à partir du token JWT).
        """
        user = request.user

        return Response({
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
        }, status=status.HTTP_200_OK)


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "UP"})

class InfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "service": "AUTHENTIFICATION",
            "version": "1.0.0",
            "description": "Service d'authentification DreamHouse237"
        })