# auth-service

Service d'authentification de la plateforme **DREAMHOUSE237**, développé en **Django** (Django REST Framework).

## Rôle

Gère l'identité et la sécurité des comptes utilisateurs :

- Inscription (réception de l'événement `user_created` depuis `user-service` via RabbitMQ)
- Connexion / génération de tokens JWT
- Réinitialisation de mot de passe
- Vérification de compte par email
- Source de vérité pour `email`, `password` (hash `pbkdf2_sha256`), `role`, `region`, `is_active`, `is_verified`

Ce service ne stocke pas les informations de profil détaillées (nom, ville, quartier, etc.) — celles-ci résident dans `user-service`. Le lien entre les deux se fait via `user_service_id` (côté auth) et `user_auth_id` (côté user), synchronisés de façon asynchrone par RabbitMQ.

## Stack

- Python 3 / Django / Django REST Framework
- MySQL (AWS RDS, connexion TLS)
- Gunicorn (serveur WSGI, port interne `8001`)
- Pika (client RabbitMQ) pour la consommation des queues `user_created` / `user_verified` et la publication de `user_auth_ack`

## Architecture & découverte de service

Au démarrage, le service :
1. Récupère sa configuration depuis `config-service` (Spring Cloud Config Server)
2. S'enregistre auprès de `registry-service` (Eureka)
3. Démarre les consumers RabbitMQ en tâche de fond

Il est exposé en interne au reste de la plateforme via `proxy-service` (Spring Cloud Gateway) sous le préfixe `/AUTHENTIFICATION/`.

## Variables d'environnement clés

| Variable | Description |
|---|---|
| `DB_SSL_CA` | Chemin vers le certificat CA pour la connexion TLS à RDS (par défaut `/certs/global-bundle.pem`) |
| `RABBITMQ_USER` / `RABBITMQ_PASSWORD` | Identifiants du broker RabbitMQ |
| Secrets DB (host/user/password) | Injectés via les secrets GitHub Actions → variables d'environnement au déploiement |

La configuration applicative (URL Eureka, Config Server, routes) est centralisée dans le repo [`config`](https://github.com/DREAMHOUSE-237/config).

## Développement local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Déploiement

Le déploiement se fait via **Docker Swarm** (voir le repo [`infrastructure`](https://github.com/DREAMHOUSE-237/infrastructure)). Un push sur `dev` déclenche automatiquement : build CI → merge vers `main` → notification à `infrastructure` → `docker stack deploy` sur le cluster EC2.
