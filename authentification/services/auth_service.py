# auth_app/services/auth_service.py

"""
Service métier du microservice Auth.

Après refactorisation :
- L'inscription n'est PLUS gérée ici.
- Le service User est désormais le point d'entrée du register.
- Il publie dans 'user_created' → consume_user_events.py crée l'AuthUser.
- Ce service gère uniquement :
    - la connexion (login)
    - la génération JWT
    - les événements RabbitMQ liés à l'auth
"""

from rest_framework_simplejwt.tokens import RefreshToken

from ..models import AuthUser
from .dto import UserDataDTO
from .message_publisher import RabbitMQPublisher


class AuthService:
    """
    Service métier central du microservice Auth.
    """

    def _build_custom_claims(self, user):
        """
        Retourne les claims personnalisés injectés
        dans le refresh ET l'access token.
        """

        return {
            "user_auth_id": str(user.id),
            "user_service_id": (
                str(user.user_service_id)
                if user.user_service_id else None
            ),
            "email": user.email,
            "role": user.role,
            "region": user.region,
            "region_display": user.region_display,
            "is_verified": user.is_verified,
            "is_active": user.is_active,
        }

    def _publish_login_event(self, user):
        """
        Publie un événement RabbitMQ après connexion réussie.
        """

        user_dto = UserDataDTO(
            event="user.login",

            user_auth_id=str(user.id),

            user_service_id=(
                str(user.user_service_id)
                if user.user_service_id else None
            ),

            email=user.email,
            role=user.role,

            region=user.region,
            region_display=user.region_display,

            is_verified=user.is_verified,
            is_active=user.is_active,
        )

        try:
            publisher = RabbitMQPublisher(
                queue="user-email-queue"
            )

            publisher.publish_message(
                user_dto.to_dict()
            )

            print(
                f"[✅] Événement user.login publié "
                f"pour {user.email}"
            )

        except Exception as e:
            print(
                f"[⚠️] Connexion réussie mais "
                f"erreur RabbitMQ email : {e}"
            )

    def login_user(self, email, password):
        """
        Authentifie un utilisateur et retourne :

        - refresh token
        - access token
        - informations utilisateur

        IMPORTANT :
        Les claims personnalisés sont injectés
        dans les DEUX tokens.
        """

        try:
            user = AuthUser.objects.get(email=email)

        except AuthUser.DoesNotExist:
            raise ValueError("Utilisateur inexistant.")

        # ── Vérification mot de passe ────────────────────────────────

        if not user.check_password(password):
            raise ValueError("Email ou mot de passe incorrect.")

        # ── Vérification compte actif ────────────────────────────────

        if not user.is_active:
            raise ValueError("Compte désactivé.")

        # ── Construction des claims JWT ──────────────────────────────

        claims = self._build_custom_claims(user)

        # ── Refresh token ────────────────────────────────────────────

        refresh = RefreshToken.for_user(user)

        for key, value in claims.items():
            refresh[key] = value

        # ── Access token ─────────────────────────────────────────────
        # IMPORTANT :
        # access_token est une instance séparée.
        # Les claims doivent être réinjectés explicitement.

        access = refresh.access_token

        for key, value in claims.items():
            access[key] = value

        # ── Publication événement RabbitMQ ───────────────────────────

        self._publish_login_event(user)

        # ── Réponse API ──────────────────────────────────────────────

        return {
            "refresh": str(refresh),

            "access": str(access),

            "user": {
                "user_auth_id": str(user.id),

                "user_service_id": (
                    str(user.user_service_id)
                    if user.user_service_id else None
                ),

                "email": user.email,

                "role": user.role,

                "region": user.region,

                "region_display": user.region_display,

                "is_verified": user.is_verified,

                "is_active": user.is_active,
            },
        }