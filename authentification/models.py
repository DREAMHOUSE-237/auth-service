import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


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
    region = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Code région du Cameroun (ex: CE, LT, OU...)"
    )
    region_display = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Display des région du Cameroun (ex: Centre, Littorale..)"
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    user_service_id = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="ID de l'utilisateur dans le service User"
    )
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


class Token(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="tokens")
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Token for {self.user.email}"


class PasswordReset(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="password_resets")
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Reset request for {self.user.email}"