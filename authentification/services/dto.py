# auth_app/services/dto.py
class UserDataDTO:
    """
    Objet utilisé pour transférer les données d'un utilisateur nouvellement créé
    vers le service User.
    """
    def __init__(self, user_id, email, role=None, tel=None,nom=None, prenom=None, localisation=None,numeroIdentification=None,nomPDG=None,contactPrincipal=None,nomAgence=None, nomUtilisateur=None):
        self.user_id = str(user_id)
        self.email = email
        self.role = role
        self.tel = tel
        self.nom = nom
        self.prenom = prenom
        self.localisation = localisation
        self.numeroIdentification = numeroIdentification
        self.nomPDG = nomPDG
        self.contactPrincipal = contactPrincipal
        self.nomAgence = nomAgence
        self.nomUtilisateur = nomUtilisateur


    def to_dict(self):
        """Convertit l'objet DTO en dictionnaire JSON."""
    
        if self.role == "proprietaire":
            return {
                "user_id": self.user_id,
                "email": self.email,
                "role": self.role,
                "tel": self.tel,
                "nom": self.nom,
                "prenom": self.prenom,
                "nomUtilisateur": self.nomUtilisateur
            }
        else:
            return {
                "user_id": self.user_id,
                "email": self.email,
                "role": self.role,
                "tel": self.tel,
                "nomAgence": self.nomAgence,
                "localisation": self.localisation,
                "numeroIdentification": self.numeroIdentification,
                "nomPDG": self.nomPDG,
                "contactPrincipal": self.contactPrincipal
            }
