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

from django.db import close_old_connections, connection


def _bootstrap_django():
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, BASE)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'service_authentification.settings')
        django.setup()


def handle_user_created(ch, method, properties, body):

    # ✅ Ferme les connexions mortes et reconnecte si nécessaire
    close_old_connections()

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

        # ─────────────────────────────────────────────────────────────
        # Vérifier si utilisateur existe déjà
        # ─────────────────────────────────────────────────────────────

        auth_user = AuthUser.objects.filter(email=email).first()

        if auth_user:

            # ✅ Met à jour user_service_id s'il manque
            if not auth_user.user_service_id:
                auth_user.user_service_id = str(user_service_id)
                auth_user.save(update_fields=["user_service_id"])

            print(f"[⚠️] AuthUser {email} existe déjà — ACK envoyé quand même.")

        else:

            auth_user = AuthUser(
                email=email,
                role=role
            )

            cni_recto = data.get("cni_recto")
            cni_verso = data.get("cni_verso")

            if cni_recto:
                auth_user.cni_recto = cni_recto

            if cni_verso:
                auth_user.cni_verso = cni_verso

            # ✅ Stocker user_service_id dès la création
            auth_user.user_service_id = str(user_service_id)

            # ✅ Hash mot de passe
            auth_user.set_password(raw_password)

            # ✅ Sauvegarde DB
            auth_user.save()

            print(
                f"[✅] AuthUser créé : "
                f"{auth_user.email} "
                f"(id={auth_user.id}, user_service_id={user_service_id})"
            )

        # ─────────────────────────────────────────────────────────────
        # Publier ACK
        # ─────────────────────────────────────────────────────────────

        ack_payload = {
            "event": "user.auth_created",
            "user_service_id": str(user_service_id),
            "user_auth_id": str(auth_user.id),
        }

        try:

            publisher = RabbitMQPublisher(queue="user_auth_ack")

            publisher.publish_message(ack_payload)

            print(
                f"[✅] ACK publié dans user_auth_ack "
                f"pour user_service_id={user_service_id}"
            )

        except Exception as pub_err:

            print(
                f"[⚠️] AuthUser créé mais erreur publication ACK : "
                f"{pub_err}"
            )

        # ✅ ACK RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:

        print(f"[❌] Erreur traitement user_created : {e}")

        # ❌ NACK sans requeue
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )

    finally:

        # ✅ Très important pour éviter
        # "MySQL server has gone away"
        connection.close()


def start_consuming_user_created():

    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASSWORD", "guest")
    )

    host = os.getenv("RABBITMQ_HOST", "localhost")

    port = int(
        os.getenv("RABBITMQ_PORT", "5672")
    )

    while True:

        try:

            connection_rabbit = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host,
                    port=port,
                    credentials=credentials
                )
            )

            channel = connection_rabbit.channel()

            channel.queue_declare(
                queue='user_created',
                durable=True
            )

            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue='user_created',
                on_message_callback=handle_user_created
            )

            print(
                "[🐇] Consumer user_created démarré "
                "— en attente de messages..."
            )

            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as conn_err:

            print(
                f"[❌] Connexion RabbitMQ perdue "
                f"(user_created) : {conn_err} "
                f"— retry dans 5 s"
            )

            time.sleep(5)

        except Exception as e:

            print(
                f"[❌] Erreur consumer user_created : "
                f"{e} — retry dans 5 s"
            )

            time.sleep(5)


if __name__ == "__main__":

    _bootstrap_django()

    start_consuming_user_created()