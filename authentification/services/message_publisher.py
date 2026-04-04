# auth_app/services/message_publisher.py
import pika
import json

class RabbitMQPublisher:
    """
    Classe utilitaire responsable d'envoyer les messages vers RabbitMQ.
    """
    def __init__(self, queue,host='192.168.172.81'):
        self.host = host
        self.queue = queue

    def publish_message(self, message: dict):
        """
        Publie un message (dict) dans la file RabbitMQ spécifiée.
        """
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
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
