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

    def _build_custom_claims(self, user):
        """Retourne le dict des claims personnalisés à injecter dans les deux tokens."""
        return {
            "user_service_id": str(user.user_service_id) if user.user_service_id else None,
            "email":           user.email,
            "role":            user.role,
            "is_verified":     user.is_verified,
        }

    def login_user(self, email, password):
        """
        Authentifie un utilisateur et retourne un JWT si succès.

        ✅ CORRECTION : les claims personnalisés sont injectés à la fois dans
        le refresh token ET dans l'access token.

        Avant, seul le refresh token recevait les claims. L'access token était
        généré via refresh.access_token avant l'injection → il ne contenait
        que le sub (UUID) sans aucun claim métier. Le frontend ne pouvait donc
        pas lire user_service_id / role / email depuis l'access token.
        """
        try:
            user = AuthUser.objects.get(email=email)
        except AuthUser.DoesNotExist:
            raise ValueError("Utilisateur inexistant.")

        if not user.check_password(password):
            raise ValueError("Email ou mot de passe incorrect.")

        if not user.is_active:
            raise ValueError("Compte désactivé.")

        claims = self._build_custom_claims(user)

        # ── Refresh token ────────────────────────────────────────────────────
        refresh = RefreshToken.for_user(user)
        for key, value in claims.items():
            refresh[key] = value

        # ── Access token — doit recevoir les claims indépendamment ───────────
        # refresh.access_token est une instance séparée ; on doit lui injecter
        # les claims explicitement après l'avoir récupérée.
        access = refresh.access_token
        for key, value in claims.items():
            access[key] = value

        # ── Publication event email ──────────────────────────────────────────
        user_dto = UserDataDTO(user_id=user.id, email=user.email)
        try:
            publisher = RabbitMQPublisher(queue='user-email-queue')
            publisher.publish_message(user_dto.to_dict())
            print(f"[✅] Événement email publié pour {user.email}")
        except Exception as e:
            print(f"[⚠️] Connexion réussie mais erreur RabbitMQ email : {e}")

        return {
            "refresh": str(refresh),
            "access":  str(access),
            "user": {
                "email":           user.email,
                "role":            user.role,
                "region":          user.region,
                "region_display":  user.region_display,
                "is_verified":     user.is_verified,
                "user_service_id": str(user.user_service_id) if user.user_service_id else None,
            },
        }