from django.apps import AppConfig
import threading


class AuthentificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentification'

    def ready(self):
        """
        Exécuté au démarrage de l'app Django.
        - Charge la config Spring Cloud
        - Enregistre dans Eureka + heartbeat
        - Démarre les consumers RabbitMQ (user_created, user_verified)
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

        # 4) Consumer RabbitMQ — user_created (User Service → Auth Service)
        #    Crée l'AuthUser à partir des données envoyées par le service User
        try:
            from .services.consume_user_events import start_consuming_user_created
            t1 = threading.Thread(target=start_consuming_user_created, daemon=True)
            t1.start()
            print("[🐇] Thread consumer user_created démarré.")
        except Exception as e:
            print(f"Erreur démarrage consumer user_created : {e}")

        # 5) Consumer RabbitMQ — user_verified (User Service → Auth Service)
        #    Synchronise is_verified=True sur l'AuthUser quand l'email est confirmé
        try:
            from .services.consume_user_verified import start_consuming_user_verified
            t2 = threading.Thread(target=start_consuming_user_verified, daemon=True)
            t2.start()
            print("[🐇] Thread consumer user_verified démarré.")
        except Exception as e:
            print(f"Erreur démarrage consumer user_verified : {e}")
