# auth_app/services/dto.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserDataDTO:
    """
    DTO standardisé pour les échanges RabbitMQ liés à l'utilisateur.
    """

    user_auth_id: Optional[str] = None
    user_service_id: Optional[str] = None

    email: Optional[str] = None
    role: Optional[str] = None

    region: Optional[str] = None
    region_display: Optional[str] = None

    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None

    event: Optional[str] = None

    def to_dict(self):
        """
        Convertit le DTO en dictionnaire JSON sérialisable.
        Ignore automatiquement les valeurs None.
        """
        return {
            key: value
            for key, value in {
                "event": self.event,
                "user_auth_id": self.user_auth_id,
                "user_service_id": self.user_service_id,
                "email": self.email,
                "role": self.role,
                "region": self.region,
                "region_display": self.region_display,
                "is_verified": self.is_verified,
                "is_active": self.is_active,
            }.items()
            if value is not None
        }