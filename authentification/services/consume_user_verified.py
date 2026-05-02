"""
Consumer RabbitMQ — écoute la queue 'user_verified'.

Quand l'utilisateur clique sur le lien de vérification d'email,
le service User publie un événement 'user.verified'.
Ce consumer met à jour is_verified=True sur l'AuthUser correspondant.

Payload attendu :
{
    "event":  "user.verified",
    "email":  "utilisateur@example.com"
}
"""

import pika
import json
import django
import os
import sys


def _bootstrap_django():
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, BASE)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'service_authentification.settings')
        django.setup()


def handle_user_verified(ch, method, properties, body):
    """
    Callback déclenché à chaque message dans 'user_verified'.
    """
    from ..models import AuthUser

    try:
        data = json.loads(body)
        email = data.get("email")
        print(f"[📨] user_verified reçu pour : {email}")

        if not email:
            print("[⚠️] Payload sans email, message ignoré.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        updated = AuthUser.objects.filter(email=email).update(is_verified=True)

        if updated:
            print(f"[✅] AuthUser {email} marqué is_verified=True")
        else:
            print(f"[⚠️] Aucun AuthUser trouvé pour {email}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[❌] Erreur traitement user_verified : {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming_user_verified(host='ec2-16-170-212-130.eu-north-1.compute.amazonaws.com'):
    """
    Lance le consumer en boucle bloquante.
    Appelé dans un thread daemon depuis apps.py.
    """
    import time

    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.queue_declare(queue='user_verified', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='user_verified', on_message_callback=handle_user_verified)
            print("[🐇] Consumer user_verified démarré — en attente de messages...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as conn_err:
            print(f"[❌] Connexion RabbitMQ perdue (user_verified) : {conn_err} — retry dans 5 s")
            time.sleep(5)
        except Exception as e:
            print(f"[❌] Erreur consumer user_verified : {e} — retry dans 5 s")
            time.sleep(5)


if __name__ == "__main__":
    _bootstrap_django()
    start_consuming_user_verified()
