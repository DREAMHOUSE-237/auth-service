# auth_app/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer, RegisterSerializer
from .services.auth_service import AuthService
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny



class RegisterView(APIView):
    """
    Vue d'inscription — reçoit les données, valide, appelle AuthService.
    """
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        service = AuthService()

        try:
            user = service.register_user(**data)
            return Response({
                "message": "Utilisateur créé avec succès.",
                "email": user.email,
                "role": user.role
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("REGISTER ERROR => ", e)
            return Response({"error": "Erreur interne du serveur."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
    permission_classes = [IsAuthenticated]  # 🔒 Obligatoire

    def get(self, request):
        """
        Retourne les infos du user connecté (à partir du token JWT)
        """
        user = request.user  # récupéré automatiquement depuis le token JWT

        return Response({
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
        }, status=status.HTTP_200_OK)
