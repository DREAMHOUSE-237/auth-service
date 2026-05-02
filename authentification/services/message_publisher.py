# auth_app/services/message_publisher.py
import pika
import json
import os

class RabbitMQPublisher:
    """
    Classe utilitaire responsable d'envoyer les messages vers RabbitMQ.
    """

    def __init__(self, queue: str):
        self.queue = queue
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.user = os.getenv("RABBITMQ_USER", "guest")
        self.password = os.getenv("RABBITMQ_PASSWORD", "guest")

    def publish_message(self, message: dict):
        """
        Publie un message (dict) dans la file RabbitMQ spécifiée.
        """
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials)
            )
            channel = connection.channel()
            channel.queue_declare(queue=self.queue, durable=True)

            channel.basic_publish(
                exchange='',
                routing_key=self.queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # message persistant
            )

            print(f"[✔] Message envoyé à RabbitMQ ({self.queue}): {message}")
            connection.close()

        except Exception as e:
            print(f"[❌] Erreur RabbitMQ: {e}")
