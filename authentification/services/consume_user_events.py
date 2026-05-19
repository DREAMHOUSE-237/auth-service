"""
Consumer RabbitMQ — écoute la queue 'user_created'.

Flux :
  User Service ──► user_created ──► [ce consumer] ──► crée AuthUser ──► user_auth_ack ──► User Service
"""

import pika
import json
import django
import os
import sys
import time


def _bootstrap_django():
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, BASE)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'service_authentification.settings')
        django.setup()


def _close_db_connections():
    """
    Ferme toutes les connexions DB Django avant chaque message.
    RDS MySQL coupe les connexions idle — cette fonction force Django
    à rouvrir une connexion fraîche au prochain appel ORM.
    """
    from django.db import connections
    for conn in connections.all():
        try:
            conn.close()
        except Exception:
            pass


def handle_user_created(ch, method, properties, body):
    # Toujours fermer les connexions périmées avant toute opération ORM
    _close_db_connections()

    from ..models import AuthUser
    from .message_publisher import RabbitMQPublisher

    try:
        data = json.loads(body)
        print(f"[📨] user_created reçu : {data.get('email')} | keys: {list(data.keys())}")

        email           = data.get("email")
        raw_password    = data.get("password")
        role            = data.get("role", "client")
        user_service_id = data.get("user_service_id")

        if not email or not raw_password or not user_service_id:
            print(f"[⚠️] Payload incomplet — email={email}, password={'ok' if raw_password else 'MISSING'}, user_service_id={user_service_id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # ── Éviter les doublons ───────────────────────────────────────────
        if AuthUser.objects.filter(email=email).exists():
            auth_user = AuthUser.objects.get(email=email)
            if not auth_user.user_service_id:
                auth_user.user_service_id = str(user_service_id)
                auth_user.save(update_fields=["user_service_id"])
            print(f"[⚠️] AuthUser {email} existe déjà — ACK envoyé quand même.")
        else:
            auth_user = AuthUser(email=email, role=role)
            auth_user.user_service_id = str(user_service_id)
            auth_user.set_password(raw_password)

            cni_recto = data.get("cni_recto")
            cni_verso = data.get("cni_verso")
            if cni_recto:
                auth_user.cni_recto = cni_recto
            if cni_verso:
                auth_user.cni_verso = cni_verso

            try:
                auth_user.save()
                print(f"[✅] AuthUser créé : {auth_user.email} (id={auth_user.id}, user_service_id={user_service_id})")
            except Exception as save_err:
                import traceback
                print(f"[❌] Erreur save AuthUser pour {email} : {save_err}")
                traceback.print_exc()
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

        # ── ACK vers User Service ─────────────────────────────────────────
        ack_payload = {
            "event": "user.auth_created",
            "user_service_id": str(user_service_id),
            "user_auth_id": str(auth_user.id),
        }
        try:
            publisher = RabbitMQPublisher(queue="user_auth_ack")
            publisher.publish_message(ack_payload)
            print(f"[✅] ACK publié dans user_auth_ack pour user_service_id={user_service_id}")
        except Exception as pub_err:
            print(f"[⚠️] AuthUser créé mais erreur publication ACK : {pub_err}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        import traceback
        print(f"[❌] Erreur traitement user_created : {e}")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming_user_created():
    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASSWORD", "guest")
    )
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))

    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host,
                    port=port,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue='user_created', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='user_created', on_message_callback=handle_user_created)
            print("[🐇] Consumer user_created démarré — en attente de messages...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as conn_err:
            print(f"[❌] Connexion RabbitMQ perdue (user_created) : {conn_err} — retry dans 5 s")
            time.sleep(5)
        except Exception as e:
            print(f"[❌] Erreur consumer user_created : {e} — retry dans 5 s")
            time.sleep(5)


if __name__ == "__main__":
    _bootstrap_django()
    start_consuming_user_created()