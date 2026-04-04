# auth_app/services/auth_service.py
from django.db import transaction
from ..models import AuthUser
from .dto import UserDataDTO
from .message_publisher import RabbitMQPublisher
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:
    """
    Service métier central du microservice Auth.
    Gère la création des utilisateurs et la communication inter-service.
    """

    @transaction.atomic
    def register_user(
        self, email, password, role, cni_recto, cni_verso,
        tel=None, nom=None, prenom=None,
        localisation=None, numeroIdentification=None,
        nomPDG=None, contactPrincipal=None,
        nomAgence=None, nomUtilisateur=None
    ):
        # 1️⃣ Vérifier l'existence
        if AuthUser.objects.filter(email=email).exists():
            raise ValueError("Un utilisateur avec cet email existe déjà.")

        # 2️⃣ Création du compte Auth
        user = AuthUser(
            email=email,
            role=role,
            cni_recto=cni_recto,
            cni_verso=cni_verso
        )
        user.set_password(password)
        user.save()

        # 3️⃣ DTO à destination du service User
        user_dto = UserDataDTO(
            user_id=user.id,
            email=user.email,
            role=role,
            tel=tel,
            nom=nom,
            prenom=prenom,
            nomUtilisateur=nomUtilisateur,
            localisation=localisation,
            numeroIdentification=numeroIdentification,
            nomPDG=nomPDG,
            contactPrincipal=contactPrincipal,
            nomAgence=nomAgence
        )

        # 4️⃣ Publication event : création utilisateur
        try:
            publisher = RabbitMQPublisher(queue='user_created')
            publisher.publish_message(user_dto.to_dict())
            print(f"[✅] Utilisateur {user.email} créé et message envoyé au service User.")
        except Exception as e:
            print(f"[⚠️] Utilisateur {user.email} créé mais erreur RabbitMQ: {e}")

        return user


    def login_user(self, email, password):
        """
        Authentifie un utilisateur et renvoie un JWT si succès,
        puis publie un événement d'email vers RabbitMQ.
        """

        try:
            user = AuthUser.objects.get(email=email)
        except AuthUser.DoesNotExist:
            raise ValueError("Utilisateur inexistant.")

        if not user.check_password(password):
            raise ValueError("Email ou Mot de passe incorrect.")

        if not user.is_active:
            raise ValueError("Compte désactivé.")

        # ✅ Génération du JWT
        refresh = RefreshToken.for_user(user)

        # ✅ DTO minimal pour événement email
        user_dto = UserDataDTO(
            user_id=user.id,
            email=user.email
        )

        # ✅ Publication event : envoi d'email
        try:
            publisher = RabbitMQPublisher(queue='user-email-queue')
            publisher.publish_message(user_dto.to_dict())
            print(f"[✅] Email envoyé au service publication via RabbitMQ")
        except Exception as e:
            print(f"[⚠️] Connexion réussie mais erreur lors de l'envoi email RabbitMQ: {e}")

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "email": user.email,
                "role": user.role,
                "is_verified": user.is_verified
            }
        }
