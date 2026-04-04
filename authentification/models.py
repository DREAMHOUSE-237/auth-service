import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# ------------------------------------------------------------
# 🧩 1️⃣ AuthUser
# Représente l'utilisateur du point de vue du service Auth
# ------------------------------------------------------------
class AuthUser(models.Model):
    """
    AuthUser contient uniquement les données nécessaires à
    l'authentification et à la gestion des accès.
    Les informations personnelles sont gérées par le service User.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50) 
    cni_recto = models.ImageField(upload_to='images/', null=False)
    cni_verso = models.ImageField(upload_to='images/', null=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        """Hash le mot de passe avant de le sauvegarder."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Vérifie la validité d'un mot de passe."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.email


# ------------------------------------------------------------
# 🔑 2️⃣ Token
# Optionnel — pour gérer les tokens persistants (ex: refresh)
# ------------------------------------------------------------
class Token(models.Model):
    """
    Token JWT ou autre forme de jeton d'accès/rafraîchissement.
    Utile si tu veux gérer des sessions ou invalider des tokens.
    """
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="tokens")
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Token for {self.user.email}"


# ------------------------------------------------------------
# 🔄 3️⃣ PasswordReset
# Pour la gestion des réinitialisations de mot de passe
# ------------------------------------------------------------
class PasswordReset(models.Model):
    """
    Contient les tokens de réinitialisation de mot de passe
    et leur durée de validité.
    """
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="password_resets")
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Reset request for {self.user.email}"


#architecture_globale.png
#architecture_interne.png
#modele_donnees.png
#sequence.png