from django.apps import AppConfig
import threading

class AuthentificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentification'

    def ready(self):
        """
        Cette méthode est exécutée automatiquement lorsque l'app Django démarre.
        On y place :
        - Chargement config depuis Spring Cloud Config
        - Enregistrement Eureka
        - Heartbeat
        """
        from .services.config_loader import load_config_from_server
        from .services.eureka import register_to_eureka, start_heartbeat

        # 1) Charger configuration depuis Spring Cloud Config
        try:
            load_config_from_server()
        except Exception as e:
            print("Erreur lors du chargement de la config :", e)

        # 2) Enregistrer dans Eureka
        try:
            register_to_eureka()
        except Exception as e:
            print("Erreur enregistrement Eureka :", e)

        # 3) Lancer le heartbeat Eureka dans un thread
        try:
            thread = threading.Thread(target=start_heartbeat, daemon=True)
            thread.start()
        except Exception as e:
            print("Erreur lancement heartbeat :", e)
