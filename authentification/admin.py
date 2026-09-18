from django.contrib import admin
from .models import AuthUser, Token, PasswordReset

# ------------------------------------------------------------
# 🧩 Customisation de l'affichage du modèle AuthUser
# ------------------------------------------------------------
@admin.register(AuthUser)
class AuthUserAdmin(admin.ModelAdmin):
    list_display = ("email", "role", "is_active", "is_verified", "created_at")
    list_filter = ("role", "is_active", "is_verified")
    search_fields = ("email",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Informations de compte", {
            "fields": ("email", "password", "role")
        }),
        ("Vérifications", {
            "fields": ("is_active", "is_verified")
        }),
        ("CNI", {
            "fields": ("cni_recto", "cni_verso")
        }),
        ("Dates", {
            "fields": ("created_at", "updated_at")
        }),
    )

# ------------------------------------------------------------
# 🔑 Admin Token
# ------------------------------------------------------------
@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at")
    search_fields = ("user__email",)
    readonly_fields = ("created_at",)

# ------------------------------------------------------------
# 🔄 Admin PasswordReset
# ------------------------------------------------------------
@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "expires_at")
    search_fields = ("user__email", "token")
    readonly_fields = ("created_at",)
