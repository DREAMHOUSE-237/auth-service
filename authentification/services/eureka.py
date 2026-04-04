import requests
import os
import json
import time

EUREKA_URL = os.getenv("EUREKA_URL", "http://192.168.172.81:8761/eureka")
APP_NAME = "AUTHENTIFICATION"

def cleanup_old_instances():
    """Supprime les anciennes instances de AUTHENTIFICATION"""
    try:
        # Récupère toutes les instances actuelles
        response = requests.get(f"{EUREKA_URL}/apps/{APP_NAME}", timeout=5)
        if response.status_code == 200:
            print("🧹 Nettoyage des anciennes instances...")
            # Supprime toutes les instances existantes
            for instance_type in ["heil-ThinkPad-E560", "192.168.172.81"]:
                try:
                    delete_url = f"{EUREKA_URL}/apps/{APP_NAME}/{instance_type}:{APP_NAME}:8000"
                    r = requests.delete(delete_url, timeout=5)
                    print(f"   Supprimé {instance_type}: {r.status_code}")
                except:
                    pass
    except Exception as e:
        print(f"⚠️ Impossible de nettoyer: {e}")

def register_to_eureka():
    # ⚠️ IP FIXE - pas de détection automatique
    ip = "192.168.172.81"  # IP fixe pour garantir l'instanceId
    port = 8000
    
    # InstanceId EXACTEMENT comme vous le voulez
    INSTANCE_ID = f"{ip}:{APP_NAME}:{port}"
    
    payload = {
        "instance": {
            "instanceId": INSTANCE_ID,  # Format exact
            "hostName": ip,             # Même que IP
            "app": APP_NAME.upper(),
            "ipAddr": ip,
            "status": "UP",
            "port": {"$": port, "@enabled": "true"},
            "securePort": {"$": 443, "@enabled": "false"},
            "healthCheckUrl": f"http://{ip}:{port}/health",
            "statusPageUrl": f"http://{ip}:{port}/info",
            "homePageUrl": f"http://{ip}:{port}/",
            "vipAddress": APP_NAME.lower(),  # Important pour Gateway
            "secureVipAddress": APP_NAME.lower(),
            "dataCenterInfo": {
                "@class": "com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo",
                "name": "MyOwn"
            },
            "metadata": {
                "management.port": str(port),
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
        # 1. Nettoie les anciennes instances
        cleanup_old_instances()
        
        # 2. Enregistre la nouvelle instance
        r = requests.post(
            f"{EUREKA_URL}/apps/{APP_NAME}",
            json=payload,  # Utilise json= au lieu de data=json.dumps()
            headers=headers,
            timeout=10
        )
        print(f"✅ Réponse Eureka : {r.status_code}")
        if r.status_code not in [200, 204]:
            print(f"⚠️ Body: {r.text}")
        else:
            print(f"🎯 Instance créée : {INSTANCE_ID}")
    except Exception as e:
        print(f"❌ Erreur enregistrement Eureka : {e}")

def start_heartbeat():
    """Envoi d'un heartbeat toutes les 30s avec l'instanceId fixe"""
    ip = "192.168.172.81"
    port = 8000
    INSTANCE_ID = f"{ip}:{APP_NAME}:{port}"
    
    print(f"💓 Démarrage heartbeat pour: {INSTANCE_ID}")
    
    while True:
        try:
            url = f"{EUREKA_URL}/apps/{APP_NAME}/{INSTANCE_ID}"
            r = requests.put(url, timeout=5)
            if r.status_code == 200:
                print(f"💓 Heartbeat envoyé: {r.status_code}")
            else:
                print(f"⚠️ Heartbeat échoué: {r.status_code}")
                # Ré-enregistrement si échec
                register_to_eureka()
        except Exception as e:
            print(f"❌ Erreur heartbeat : {e}")
            # Ré-enregistrement en cas d'erreur
            time.sleep(5)
            register_to_eureka()
        
        time.sleep(30)

# Pour exécuter directement
if __name__ == "__main__":
    print("🚀 Démarrage du service AUTHENTIFICATION")
    register_to_eureka()
    start_heartbeat()