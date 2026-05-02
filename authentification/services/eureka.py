import requests
import os
import time
import socket

# URL du Eureka Registry (remplace par le DNS public de ton EC2 où tourne registry-service)
EUREKA_URL = os.getenv(
    "EUREKA_URL",
    "http://ec2-16-170-212-130.eu-north-1.compute.amazonaws.com:8761/eureka"
)
APP_NAME = "AUTHENTIFICATION"
PORT = int(os.getenv("APP_PORT", "8001"))

def get_hostname():
    """
    Récupère automatiquement l'IP privée de l'instance EC2
    """
    try:
        return requests.get("http://169.254.169.254/latest/meta-data/local-ipv4", timeout=2).text
    except Exception:
        return socket.gethostname()

def cleanup_old_instances():
    """Supprime les anciennes instances de AUTHENTIFICATION si besoin"""
    try:
        response = requests.get(f"{EUREKA_URL}/apps/{APP_NAME}", timeout=5)
        if response.status_code == 200:
            print("🧹 Nettoyage des anciennes instances...")
            # Ici tu pourrais supprimer d’anciennes instances si besoin
    except Exception as e:
        print(f"⚠️ Impossible de nettoyer: {e}")

def register_to_eureka():
    hostname = get_hostname()
    INSTANCE_ID = f"{hostname}:{APP_NAME}:{PORT}"

    payload = {
        "instance": {
            "instanceId": INSTANCE_ID,
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
                "instanceId": INSTANCE_ID
            },
            "leaseInfo": {
                "renewalIntervalInSecs": 30,
                "durationInSecs": 90
            }
        }
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    print(f"🔄 Enregistrement Eureka avec InstanceId: {INSTANCE_ID}")

    try:
        cleanup_old_instances()
        r = requests.post(f"{EUREKA_URL}/apps/{APP_NAME}", json=payload, headers=headers, timeout=10)
        print(f"✅ Réponse Eureka : {r.status_code}")
        if r.status_code not in [200, 204]:
            print(f"⚠️ Body: {r.text}")
        else:
            print(f"🎯 Instance créée : {INSTANCE_ID}")
    except Exception as e:
        print(f"❌ Erreur enregistrement Eureka : {e}")

def start_heartbeat():
    """Envoi d'un heartbeat toutes les 30s avec l’IP privée"""
    hostname = get_hostname()
    INSTANCE_ID = f"{hostname}:{APP_NAME}:{PORT}"

    print(f"💓 Démarrage heartbeat pour: {INSTANCE_ID}")

    while True:
        try:
            url = f"{EUREKA_URL}/apps/{APP_NAME}/{INSTANCE_ID}"
            r = requests.put(url, timeout=5)
            if r.status_code == 200:
                print(f"💓 Heartbeat envoyé: {r.status_code}")
            else:
                print(f"⚠️ Heartbeat échoué: {r.status_code}")
                register_to_eureka()
        except Exception as e:
            print(f"❌ Erreur heartbeat : {e}")
            time.sleep(5)
            register_to_eureka()

        time.sleep(30)

if __name__ == "__main__":
    print("🚀 Démarrage du service AUTHENTIFICATION")
    register_to_eureka()
    start_heartbeat()
