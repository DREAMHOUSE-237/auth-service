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

# ── Bootstrap Django si lancé en standalone ──────────────────────────────────
def _bootstrap_django():
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, BASE)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'service_authentification.settings')
        django.setup()

# ─────────────────────────────────────────────────────────────────────────────

def handle_user_created(ch, method, properties, body):
    """
    Callback déclenché à chaque message dans 'user_created'.
    """
    from ..models import AuthUser
    from .message_publisher import RabbitMQPublisher

    try:
        data = json.loads(body)
        print(f"[📨] user_created reçu : {data.get('email')}")

        email = data.get("email")
        raw_password = data.get("password")
        role = data.get("role", "client")
        user_service_id = data.get("user_service_id")

        if not email or not raw_password or not user_service_id:
            print("[⚠️] Payload incomplet, message ignoré.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # ── Éviter les doublons ───────────────────────────────────────────────
        if AuthUser.objects.filter(email=email).exists():
            auth_user = AuthUser.objects.get(email=email)
            print(f"[⚠️] AuthUser {email} existe déjà — ACK envoyé quand même.")
        else:
            auth_user = AuthUser(email=email, role=role)
            cni_recto = data.get("cni_recto")
            cni_verso = data.get("cni_verso")
            if cni_recto:
                auth_user.cni_recto = cni_recto
            if cni_verso:
                auth_user.cni_verso = cni_verso

            auth_user.set_password(raw_password)
            auth_user.save()
            print(f"[✅] AuthUser créé : {auth_user.email} (id={auth_user.id})")

        # ── Publier l'ACK vers le service User ────────────────────────────────
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
        print(f"[❌] Erreur traitement user_created : {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming_user_created():
    """
    Lance le consumer en boucle bloquante.
    """
    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASSWORD", "guest")
    )
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))

    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host, port=port, credentials=credentials)
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


# ── Lancement standalone ─────────────────────────────────────────────────────
if __name__ == "__main__":
    _bootstrap_django()
    start_consuming_user_created()
