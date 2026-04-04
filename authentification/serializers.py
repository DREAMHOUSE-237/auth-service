# auth_app/serializers.py
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()
    tel = serializers.CharField(required=False, allow_blank=True)

    # Champs pour les PROPRIÉTAIRES
    nom = serializers.CharField(required=False, allow_blank=True)
    prenom = serializers.CharField(required=False, allow_blank=True)

    cni_recto = serializers.ImageField(required=False)
    cni_verso = serializers.ImageField(required=False)

    # Champs pour AGENCE
    localisation = serializers.CharField(required=False, allow_blank=True)
    numeroIdentification = serializers.CharField(required=False, allow_blank=True)
    nomPDG = serializers.CharField(required=False, allow_blank=True)
    contactPrincipal = serializers.CharField(required=False, allow_blank=True)
    nomAgence = serializers.CharField(required=False, allow_blank=True)

    nomUtilisateur = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        role = attrs.get('role')

        if role == 'proprietaire':
            #required_fields = ['nom', 'prenom', 'cni_recto', 'cni_verso']
            required_fields = ['nom', 'prenom']
        elif role == 'agence':
            required_fields = ['nomAgence', 'localisation', 'numeroIdentification', 'nomPDG', 'contactPrincipal']
        else:
            raise serializers.ValidationError("Rôle invalide. Choisir 'proprietaire' ou 'agence'.")

        for field in required_fields:
            if not attrs.get(field):
                raise serializers.ValidationError(f"Le champ '{field}' est obligatoire pour le rôle '{role}'.")

        return attrs




class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
