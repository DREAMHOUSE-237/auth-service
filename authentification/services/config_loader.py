import requests
import os

def load_config_from_server():
    CONFIG_SERVER_URL = os.getenv("CONFIG_SERVER_URL", "http://192.168.172.22:8080")
    APP_NAME = "AUTHENTIFICATION"

    url = f"{CONFIG_SERVER_URL}/{APP_NAME}/default"

    print(f"Téléchargement config depuis {url}...")

    response = requests.get(url)
    if response.status_code != 200:
        print("Échec récupération config :", response.status_code)
        return

    data = response.json()

    for source in data.get("propertySources", []):
        props = source.get("source", {})
        for key, value in props.items():
            # Injection dans les variables d'environnement
            os.environ[key.upper()] = str(value)

    print("Configuration Spring Cloud chargée avec succès.")
