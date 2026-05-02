import requests
import os
import time
import socket

# URL du Eureka Registry
EUREKA_URL = os.getenv(
    "EUREKA_URL",
    "http://ec2-16-170-212-130.eu-north-1.compute.amazonaws.com:8761/eureka"
)
APP_NAME = "AUTHENTIFICATION"
PORT = int(os.getenv("APP_PORT", "8001"))


def get_hostname():
    """
    Récupère le hostname/IP dans cet ordre de priorité :
    1. Variable d'environnement INSTANCE_HOST (recommandé en Docker)
    2. Metadata AWS EC2 (si dispo)
    3. IP locale résolue
    4. Hostname système
    """
    # Priorité 1 : variable explicite injectée via docker-compose
    explicit = os.getenv("INSTANCE_HOST", "").strip()
    if explicit:
        print(f"🌐 Hostname depuis INSTANCE_HOST: {explicit}")
        return explicit

    # Priorité 2 : metadata AWS (fonctionne sur EC2 hôte, pas toujours en conteneur)
    try:
        ip = requests.get(
            "http://169.254.169.254/latest/meta-data/local-ipv4",
            timeout=2
        ).text.strip()
        if ip:
            print(f"🌐 Hostname depuis metadata AWS: {ip}")
            return ip
    except Exception:
        pass

    # Priorité 3 : IP locale résolue
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and ip != "127.0.0.1":
            print(f"🌐 Hostname depuis socket IP: {ip}")
            return ip
    except Exception:
        pass

    # Priorité 4 : hostname système
    hostname = socket.gethostname()
    if hostname:
        print(f"🌐 Hostname depuis socket gethostname: {hostname}")
        return hostname

    raise RuntimeError("❌ Impossible de déterminer le hostname. Définir INSTANCE_HOST dans l'environnement.")


def cleanup_old_instances():
    """Supprime les anciennes instances si besoin"""
    try:
        response = requests.get(f"{EUREKA_URL}/apps/{APP_NAME}", timeout=5)
        if response.status_code == 200:
            print("🧹 Nettoyage des anciennes instances...")
    except Exception as e:
        print(f"⚠️ Impossible de nettoyer: {e}")


def register_to_eureka():
    hostname = get_hostname()
    instance_id = f"{hostname}:{APP_NAME}:{PORT}"

    payload = {
        "instance": {
            "instanceId": instance_id,
            "hostName": hostname,
            "app": APP_NAME.upper(),
            "ipAddr": hostname,
            "status": "UP",
            "port": {"$": PORT, "@enabled": "true"},
            "securePort": {"$": 443, "@enabled": "false"},
            "healthCheckUrl": f"http://{hostname}:{PORT}/api/auth/health",
            "statusPageUrl": f"http://{hostname}:{PORT}/api/auth/info",
            "homePageUrl": f"http://{hostname}:{PORT}/api/auth/",
            "vipAddress": APP_NAME.lower(),
            "secureVipAddress": APP_NAME.lower(),
            "dataCenterInfo": {
                "@class": "com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo",
                "name": "MyOwn"
            },
            "metadata": {
                "management.port": str(PORT),
                "instanceId": instance_id
            },
            "leaseInfo": {
                "renewalIntervalInSecs": 30,
                "durationInSecs": 90
            }
        }
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    print(f"🔄 Enregistrement Eureka avec InstanceId: {instance_id}")

    try:
        cleanup_old_instances()
        r = requests.post(
            f"{EUREKA_URL}/apps/{APP_NAME}",
            json=payload,
            headers=headers,
            timeout=10
        )
        print(f"✅ Réponse Eureka : {r.status_code}")
        if r.status_code not in [200, 204]:
            print(f"⚠️ Body: {r.text}")
        else:
            print(f"🎯 Instance créée : {instance_id}")
    except Exception as e:
        print(f"❌ Erreur enregistrement Eureka : {e}")


def start_heartbeat():
    """Envoi d'un heartbeat toutes les 30s"""
    hostname = get_hostname()
    instance_id = f"{hostname}:{APP_NAME}:{PORT}"
    print(f"💓 Démarrage heartbeat pour: {instance_id}")

    while True:
        try:
            url = f"{EUREKA_URL}/apps/{APP_NAME}/{instance_id}"
            r = requests.put(url, timeout=5)
            if r.status_code == 200:
                print(f"💓 Heartbeat OK: {r.status_code}")
            else:
                print(f"⚠️ Heartbeat échoué ({r.status_code}), re-enregistrement...")
                register_to_eureka()
                # Recalcule l'instance_id après re-enregistrement
                hostname = get_hostname()
                instance_id = f"{hostname}:{APP_NAME}:{PORT}"
        except Exception as e:
            print(f"❌ Erreur heartbeat : {e}")
            time.sleep(5)
            continue

        time.sleep(30)


if __name__ == "__main__":
    print("🚀 Démarrage du service AUTHENTIFICATION")
    register_to_eureka()
    start_heartbeat()