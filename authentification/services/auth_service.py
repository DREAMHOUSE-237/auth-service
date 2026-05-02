# auth_app/services/auth_service.py
"""
Service métier du microservice Auth.

Après refactorisation :
- L'inscription n'est PLUS gérée ici. Le service User est désormais le point d'entrée
  du register. Il publie dans 'user_created' → consume_user_events.py crée l'AuthUser.
- Ce service gère uniquement la connexion (login) et la génération de JWT.
"""
from ..models import AuthUser
from .dto import UserDataDTO
from .message_publisher import RabbitMQPublisher
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:
    """
    Service métier central du microservice Auth.
    Gère l'authentification (login) et la communication inter-service.
    """

    def login_user(self, email, password):
        """
        Authentifie un utilisateur et retourne un JWT si succès.
        Publie ensuite un événement d'email vers RabbitMQ (publication service).
        """
        try:
            user = AuthUser.objects.get(email=email)
        except AuthUser.DoesNotExist:
            raise ValueError("Utilisateur inexistant.")

        if not user.check_password(password):
            raise ValueError("Email ou mot de passe incorrect.")

        if not user.is_active:
            raise ValueError("Compte désactivé.")

        # ✅ Génération du JWT
        refresh = RefreshToken.for_user(user)

        # ✅ DTO minimal pour événement email
        user_dto = UserDataDTO(
            user_id=user.id,
            email=user.email
        )

        # ✅ Publication event : envoi d'email (service publication)
        try:
            publisher = RabbitMQPublisher(queue='user-email-queue')
            publisher.publish_message(user_dto.to_dict())
            print(f"[✅] Événement email publié pour {user.email}")
        except Exception as e:
            print(f"[⚠️] Connexion réussie mais erreur RabbitMQ email : {e}")

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "email": user.email,
                "role": user.role,
                "is_verified": user.is_verified
            }
        }
