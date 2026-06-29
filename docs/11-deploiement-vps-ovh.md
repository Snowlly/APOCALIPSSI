# Guide de déploiement en production — EduTutor IA sur VPS OVHcloud

> ⚠️ **À lire avant tout.** Le Kit `IPSSI_APOCAL_KIT` est conçu pour le **développement local** : le frontend tourne via `npm run dev` (serveur Vite), le backend via `manage.py runserver`, les quatre services (postgres, ollama, backend, frontend) exposent leurs ports directement sur l'hôte, et `.env.example` contient des **secrets de démonstration** — dont une clé SMTP Brevo en clair dans un dépôt **public**. **Rien de tout cela n'est acceptable sur une machine publique.** Ce guide bascule le Kit en configuration de **production** sur un VPS OVHcloud (Ubuntu 24.04 LTS) : reverse proxy Caddy en HTTPS, frontend buildé en statique, backend servi par gunicorn, base PostgreSQL, LLM cloud par défaut, et **aucun port applicatif exposé sur Internet** (seul Caddy écoute sur 80/443).

Public visé : formateur + étudiants, niveau intermédiaire. OS supposé : **Ubuntu 24.04 LTS**. Tout au long du guide, remplacez les placeholders `<IP_VPS>`, `<DOMAINE>` et `<USER>` par vos valeurs réelles. Les commandes shell sont exactes et testables ; pour l'espace client OVH (dont les écrans changent souvent), on décrit l'**intention** plutôt que des libellés de menus précis.

> ✅ **Fichiers de production déjà fournis dans le dépôt** (pré-configurés pour `apocalipssi26.elafrit.com` et validés : build des images OK, fusion Compose OK, `settings.py` conforme black/ruff). Inutile de recréer les artefacts décrits plus bas — ils existent : [`docker-compose.prod.yml`](../docker-compose.prod.yml), [`Caddyfile`](../Caddyfile), [`docker/backend.prod.Dockerfile`](../docker/backend.prod.Dockerfile), [`docker/frontend.prod.Dockerfile`](../docker/frontend.prod.Dockerfile), [`.env.prod.example`](../.env.prod.example) et le durcissement de [`settings.py`](../backend/apocal/settings.py) (drapeau `DJANGO_SECURE_PROD`). Aux sections 4 à 6, contentez-vous de **vérifier/adapter**. Déploiement résumé : `cp .env.prod.example .env` (compléter les secrets) puis `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`.

## Résumé express

1. **Choisir et commander le VPS OVH** — dimensionner selon le backend LLM, commander en Ubuntu 24.04, récupérer l'IP et repérer la console KVM.
2. **Première connexion SSH & durcissement** — clé SSH, utilisateur sudo non-root, mises à jour, durcissement `sshd`, swap, fail2ban, UFW (22/80/443).
3. **Installer Docker Engine + Compose v2** — dépôt officiel Docker, plugin Compose v2, utilisateur dans le groupe `docker`, rotation des logs.
4. **Récupérer le code & créer le `.env` de production** — cloner le dépôt, révoquer ET purger la clé Brevo fuitée, générer des secrets forts, `DJANGO_DEBUG=False`, `.env` en `600` et hors Git.
5. **Adapter le code Django pour la production** — service des statiques (WhiteNoise **activé**), durcissement cookies/HSTS/CSRF/proxy TLS dans `settings.py`.
6. **Adapter la stack Docker (override Compose)** — `docker-compose.prod.yml` : Dockerfile backend prod dégraissé, service one-shot `migrate`, gunicorn, frontend statique Nginx, ports fermés, healthchecks `/health/`, limites RAM/CPU, service Caddy.
7. **Domaine, reverse proxy & HTTPS** — DNS A/AAAA, Caddy en conteneur, certificat Let's Encrypt automatique.
8. **Stratégie LLM** — backend cloud free tier (Groq/Mistral) par défaut ; Ollama local seulement si le VPS a la RAM.
9. **Premier déploiement & vérifications** — build, migrations, superuser, `check --deploy`, smoke tests (dont statiques admin/Swagger), checklist de validation.
10. **Exploitation** — sauvegardes PostgreSQL chiffrées + volumes, copie hors-VPS, mises à jour, supervision, restauration, renouvellement TLS.

Les sections suivent cet ordre : chacune suppose la précédente terminée.

---

## 1. Choisir et commander le VPS OVH

Cette section couvre le choix de la gamme, le dimensionnement selon votre backend LLM, la commande, la récupération des accès et la console de secours. C'est l'étape préalable à tout le reste du guide : on ne touche pas encore à la machine, on la dimensionne et on la commande correctement.

### 1.1. Décider d'abord du backend LLM (c'est lui qui fixe le dimensionnement)

Le choix du VPS dépend presque entièrement de **comment EduTutor IA génère les QCM** :

| Critère | LLM cloud (recommandé par défaut) | Ollama local |
|---|---|---|
| Variable `.env` | `LLM_BACKEND=groq` (ou `mistral`, `gemini`, `cerebras`) | `LLM_BACKEND=ollama` + `OLLAMA_MODEL=llama3.1:8b` |
| RAM requise | 2–4 Go suffisent | **8 Go minimum**, 16 Go confortable (modèle ~5–6 Go + Postgres/Django/front) |
| Disque | 20–40 Go | **+5 à 8 Go rien que pour le modèle** (llama3.1:8b ≈ 4,7 Go) |
| Vitesse de génération | ~1–5 s (Groq/Cerebras très rapides) | **2 à 5 min par QCM sur CPU sans GPU** (timeout 600 s) |
| RGPD / souveraineté | Données envoyées au fournisseur (Mistral = hébergé UE) | Tout reste sur votre VPS |
| Coût | Free tier gratuit | Inclus dans le VPS (mais VPS plus gros = plus cher) |

> ⚠️ **Les VPS OVH n'ont pas de GPU.** Faire tourner `llama3.1:8b` en CPU pur est très lent (2 à 5 min par génération) et sature 100 % des cœurs, ce qui bloque les autres services pendant la génération. **Pour une démo fluide en formation, choisissez un backend cloud free tier (Groq ou Mistral) et un petit VPS.** Ne partez sur Ollama local que si la souveraineté/le hors-ligne est une exigence explicite, et dans ce cas dimensionnez large. La stratégie LLM détaillée fait l'objet de la **section 8**.

### 1.2. Choisir la gamme VPS OVHcloud

OVHcloud propose plusieurs gammes de VPS (les noms commerciaux évoluent ; à l'heure de la rédaction : **VPS Value, Essential, Comfort, Elite**). Elles se distinguent surtout par le couple vCore/RAM et le type de stockage (NVMe sur les gammes supérieures).

> ⚠️ Les libellés exacts, prix et caractéristiques des gammes changent régulièrement sur le site OVH. Fiez-vous au **comparatif vCPU / RAM / disque affiché sur la page produit au moment de la commande**, pas à un nom de gamme mémorisé. Les chiffres ci-dessous sont des cibles de dimensionnement, pas des références produit figées.

**Reco chiffrée — Cas A : LLM cloud (par défaut, recommandé)**

- **2 vCore / 4 Go RAM / 80 Go SSD-NVMe** : confortable pour les 4 conteneurs (Postgres + backend gunicorn + frontend statique + Caddy), avec marge pour les pics.
- Minimum viable : **2 vCore / 2 Go RAM / 40 Go**, suffisant pour une classe en démo si vous ne lancez **pas** Ollama.
- C'est une gamme d'entrée/milieu de gamme, peu coûteuse.

**Reco chiffrée — Cas B : Ollama local (souveraineté / hors-ligne)**

- **4 vCore / 16 Go RAM / 160 Go SSD-NVMe** recommandé : le modèle occupe ~5–6 Go de RAM en plus de Postgres/Django/front.
- Plancher absolu : **4 vCore / 8 Go RAM / 80 Go**, et dans ce cas réduisez le modèle (`OLLAMA_MODEL=llama3.2:3b` ≈ 2 Go ou `phi3:mini` ≈ 2,3 Go) pour éviter l'OOM-killer.
- Prévoyez le disque : l'image Ollama + le modèle ajoutent plusieurs Go ; un disque trop petit fait échouer le `ollama pull`.

> ⚠️ Sous-dimensionner la RAM avec Ollama = le conteneur se fait tuer par l'OOM-killer Linux ou la machine part en swap (lenteur extrême). En cas de doute, prenez la RAM au-dessus : c'est moins cher que de migrer le VPS en pleine semaine de formation.

**Localisation et OS :**
- Choisissez un **datacenter européen** (ex. Gravelines/Roubaix en France) pour la latence et le RGPD.
- OS à l'installation : **Ubuntu Server 24.04 LTS** (la distribution supposée par tout ce guide). Si OVH propose des images « Docker ready », vous pouvez les prendre, mais une Ubuntu 24.04 nue convient et le guide installe Docker lui-même.

### 1.3. Commander le VPS dans l'espace client OVH

> Les écrans de commande OVH changent souvent : je décris l'**intention** et où chercher, pas des libellés de menus exacts.

1. Connectez-vous sur le site OVHcloud, rubrique **VPS / Serveurs**, et lancez une commande de VPS.
2. Sélectionnez la **gamme** correspondant à votre cas A ou B (section 1.2).
3. À l'étape **système d'exploitation / image**, choisissez **Ubuntu Server 24.04 LTS** (architecture 64 bits / x86-64). Laissez le partitionnement par défaut.
4. Choisissez la **localisation** (datacenter européen).
5. Choisissez la durée d'engagement (mensuel pour une formation, c'est le plus souple) puis validez et payez.
6. Le provisionnement prend quelques minutes à quelques dizaines de minutes. Vous recevez un **e-mail de livraison** quand le VPS est prêt.

> ⚠️ **Si OVH propose d'ajouter votre clé SSH publique pendant la commande, faites-le** : c'est plus sûr qu'un mot de passe root envoyé par e-mail, et ça évite l'étape de connexion par mot de passe initial. Si vous n'avez pas encore de clé, vous en générerez une à la section 2.

### 1.4. Récupérer l'IP et les identifiants initiaux

1. L'**adresse IPv4 publique** du VPS (`<IP_VPS>`) figure dans l'e-mail de livraison **et** dans l'espace client OVH, dans le **tableau de bord du VPS** (section Bare Metal Cloud / VPS, puis votre instance, onglet d'informations générales).
2. Les **identifiants initiaux** :
   - Si vous avez fourni une clé SSH à la commande : connexion par clé, pas de mot de passe à récupérer.
   - Sinon : OVH envoie un **mot de passe initial** (souvent pour l'utilisateur `ubuntu` ou `root` selon l'image) par e-mail, ou vous propose de le (ré)initialiser depuis le tableau de bord du VPS (cherchez une action du type « réinitialiser le mot de passe »).
3. Notez l'IP. Pour la suite du guide, **`<IP_VPS>` = cette adresse** et **`<USER>` = le compte administrateur** que vous créerez à la section 2 (ou `ubuntu` par défaut sur les images Ubuntu OVH).

### 1.5. Accès console KVM/VNC de secours

Si vous **perdez l'accès SSH** (mauvaise règle UFW qui bloque le port 22, erreur de config réseau, mot de passe oublié), OVH fournit une **console KVM/VNC** qui donne un accès écran-clavier directement à la machine, indépendamment du réseau SSH.

1. Dans l'espace client OVH, ouvrez le **tableau de bord de votre VPS**.
2. Cherchez une action du type **« Console KVM »**, **« noVNC »** ou une icône de terminal/écran (souvent dans le menu d'actions « … » de l'instance ou un bouton en haut de la fiche VPS).
3. Une console web s'ouvre : vous y tapez vos identifiants Linux comme sur un écran physique.

> ⚠️ La console KVM est votre **filet de sécurité** : c'est par là qu'on rattrape une règle de pare-feu qui s'est verrouillée toute seule. Repérez **où elle se trouve avant** d'avoir besoin d'urgence — notamment avant d'activer UFW à la section 2. La saisie clavier dans la console VNC peut être en **QWERTY** par défaut quel que soit votre clavier physique : tapez les mots de passe avec prudence (vérifiez les caractères spéciaux).

Une fois le VPS commandé, l'IP notée et la console KVM repérée, passez à la sécurisation du serveur.

---

## 2. Première connexion SSH & durcissement

Cette section couvre la prise en main initiale du VPS fraîchement livré jusqu'à un serveur durci prêt à recevoir Docker et Caddy. Toutes les commandes sont exactes et testées pour Ubuntu 24.04.

> ⚠️ **Effectuez ces étapes dans l'ordre, sans fermer votre session SSH initiale tant que vous n'avez pas vérifié le nouvel accès.** La désactivation du login root et du mot de passe (étape 6) peut vous verrouiller dehors si la clé SSH n'est pas correctement en place. Gardez TOUJOURS un second terminal connecté en parallèle pendant ces manipulations. En cas de verrouillage, utilisez la console KVM/VNC repérée à la section 1.5.

### 2.1. Se connecter en root (ou en `ubuntu`)

À la livraison, OVH a fourni soit un accès par votre clé SSH, soit un mot de passe root initial (voir section 1.4). Depuis votre machine locale (Linux/macOS, ou PowerShell/Windows Terminal sous Windows, OpenSSH étant intégré à Windows 10/11) :

```bash
ssh root@<IP_VPS>
```

À la première connexion, acceptez l'empreinte du serveur (`yes`). Si OVH a fourni un mot de passe initial, il vous sera probablement demandé de le changer immédiatement.

> ⚠️ **Si vous voyez un avertissement `REMOTE HOST IDENTIFICATION HAS CHANGED` lors d'une reconnexion ultérieure** (par exemple après une réinstallation du VPS), supprimez l'ancienne empreinte localement avec `ssh-keygen -R <IP_VPS>` avant de réessayer. À l'inverse, si cet avertissement réapparaît alors que vous n'avez rien réinstallé, ne l'ignorez pas (risque d'usurpation).

Vérifiez que vous êtes bien sur Ubuntu 24.04 :

```bash
lsb_release -a
# Doit afficher : Description: Ubuntu 24.04 ... LTS
```

### 2.2. Générer une clé SSH (sur votre machine locale)

Si vous n'avez pas encore de paire de clés, générez-la **sur votre poste local**, jamais sur le serveur :

```bash
ssh-keygen -t ed25519 -C "<USER>@apocalipssi" -f ~/.ssh/apocalipssi_ed25519
```

- Validez par une **passphrase** robuste (elle chiffre la clé privée au repos).
- Cela crée `~/.ssh/apocalipssi_ed25519` (clé **privée**, à NE JAMAIS partager) et `~/.ssh/apocalipssi_ed25519.pub` (clé **publique**, à déposer sur le serveur).

> ⚠️ **Sous Windows**, ces commandes fonctionnent dans **PowerShell** ou **Windows Terminal**. La clé est créée dans `C:\Users\<vous>\.ssh\`. Évitez de générer la clé dans Git Bash si vous comptez l'utiliser depuis PowerShell, pour ne pas vous perdre entre deux emplacements `.ssh`.

### 2.3. Créer un utilisateur sudo non-root

Toujours connecté **en root sur le VPS**, créez un compte d'administration dédié. Travailler en root au quotidien est à proscrire.

```bash
adduser <USER>
```

Renseignez un mot de passe fort (il servira pour `sudo`, pas pour la connexion SSH une fois le durcissement terminé). Les autres champs (nom complet, etc.) sont facultatifs : laissez-les vides en appuyant sur Entrée.

Ajoutez ce compte au groupe `sudo` et vérifiez :

```bash
usermod -aG sudo <USER>
groups <USER>
```

La sortie doit contenir `sudo`.

### 2.4. Déposer la clé publique sur le compte sudo

Le but est d'installer votre **clé publique** dans `~/.ssh/authorized_keys` du compte `<USER>` (pas de root).

**Méthode A — depuis votre machine locale (recommandée, si `ssh-copy-id` est disponible) :**

```bash
ssh-copy-id -i ~/.ssh/apocalipssi_ed25519.pub <USER>@<IP_VPS>
```

(Le mot de passe du compte `<USER>` créé à l'étape 2.3 vous sera demandé.)

**Méthode B — manuelle (Windows PowerShell, ou si `ssh-copy-id` est absent).** Affichez d'abord le contenu de votre clé publique locale :

```powershell
Get-Content $env:USERPROFILE\.ssh\apocalipssi_ed25519.pub
```

Puis, **sur le VPS en root**, créez le dossier et le fichier pour `<USER>` en collant la ligne obtenue :

```bash
mkdir -p /home/<USER>/.ssh
echo "ssh-ed25519 AAAA...la_cle_publique_complete... <USER>@apocalipssi" >> /home/<USER>/.ssh/authorized_keys
chmod 700 /home/<USER>/.ssh
chmod 600 /home/<USER>/.ssh/authorized_keys
chown -R <USER>:<USER> /home/<USER>/.ssh
```

> ⚠️ **Les permissions sont critiques.** SSH refuse silencieusement les clés si `~/.ssh` n'est pas en `700` et `authorized_keys` en `600`, ou si le propriétaire n'est pas le bon utilisateur. Une clé « qui ne marche pas » vient presque toujours de là.

**Validez le nouvel accès dans un terminal SÉPARÉ, sans fermer la session root :**

```bash
ssh -i ~/.ssh/apocalipssi_ed25519 <USER>@<IP_VPS>
sudo whoami   # doit afficher : root
```

Vous devez arriver sur un shell `<USER>@...` sans qu'aucun mot de passe SSH ne soit demandé (seule la passphrase de la clé, gérée localement, peut l'être). **Ne passez à l'étape 2.6 que si ces deux tests réussissent.**

> 💡 **Astuce confort** — sur votre machine locale, ajoutez un alias dans `~/.ssh/config` pour ne plus retaper les options :
> ```
> Host apocalipssi
>     HostName <IP_VPS>
>     User <USER>
>     IdentityFile ~/.ssh/apocalipssi_ed25519
> ```
> Vous vous connecterez ensuite avec un simple `ssh apocalipssi`.

### 2.5. Mettre à jour le système et installer les outils de base

Connecté en `<USER>` (via la clé SSH), mettez le système à jour et installez les outils utiles pour la suite :

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y curl git ufw fail2ban unattended-upgrades ca-certificates dnsutils gnupg
```

Activez les mises à jour de sécurité automatiques (réglages détaillés en section 10.6) :

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

> ⚠️ **Si une mise à jour du noyau a été installée, un redémarrage est nécessaire.** Vérifiez avec `[ -f /var/run/reboot-required ] && echo "REDEMARRAGE REQUIS"`. Le cas échéant, `sudo reboot`, puis reconnectez-vous en `<USER>` avant de continuer.

### 2.6. Durcir la configuration SSH (sshd_config)

> ⚠️ **C'est l'étape qui peut vous verrouiller hors du serveur.** Ne la faites qu'après avoir confirmé à l'étape 2.4 que la connexion par clé en `<USER>` ET `sudo` fonctionnent. Gardez une session active en parallèle.

Sur Ubuntu 24.04, privilégiez un **fichier de surcharge dédié** (les fichiers dans `/etc/ssh/sshd_config.d/` sont inclus automatiquement et survivent mieux aux mises à jour du paquet) plutôt que d'éditer directement `/etc/ssh/sshd_config`.

```bash
sudo tee /etc/ssh/sshd_config.d/99-durcissement.conf > /dev/null <<'EOF'
# Durcissement SSH - APOCAL'IPSSI
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
X11Forwarding no
MaxAuthTries 3
EOF
```

> ⚠️ **Sur Ubuntu 24.04, un réglage par défaut peut écraser le vôtre.** Le fichier `/etc/ssh/sshd_config.d/50-cloud-init.conf` (présent sur beaucoup d'images cloud OVH) contient parfois `PasswordAuthentication yes`. Comme les fichiers sont chargés par ordre alphabétique et que la **première** directive rencontrée l'emporte, un `50-...` prime sur votre `99-...`. Vérifiez et neutralisez-le si besoin :
> ```bash
> sudo grep -R "PasswordAuthentication" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/
> ```
> Si une ligne `PasswordAuthentication yes` apparaît dans un fichier au numéro inférieur, éditez ce fichier pour la passer à `no` (ou commentez-la).

Validez la syntaxe **avant** de recharger le service, puis redémarrez SSH (Ubuntu 24.04 utilise l'activation par socket) :

```bash
sudo sshd -t
sudo systemctl restart ssh.socket ssh.service
```

**Test final décisif — dans un NOUVEAU terminal** (sans fermer la session courante) :

```bash
ssh -i ~/.ssh/apocalipssi_ed25519 <USER>@<IP_VPS>   # doit fonctionner
ssh root@<IP_VPS>                                    # doit être refusé (Permission denied)
```

> ⚠️ **Ne fermez votre session de secours qu'après avoir confirmé que la nouvelle connexion par clé fonctionne.** Si vous êtes verrouillé, utilisez la console KVM/VNC de l'espace client OVH (section 1.5) pour corriger le fichier de configuration.

### 2.7. Fuseau horaire

Réglez l'horloge du serveur sur le fuseau de la formation et vérifiez la synchro NTP :

```bash
sudo timedatectl set-timezone Europe/Paris
timedatectl
```

Les lignes `Time zone: Europe/Paris` et `System clock synchronized: yes` doivent apparaître.

> ℹ️ **Conséquence pour les tâches planifiées.** À partir de maintenant, `cron`, les timers systemd et `unattended-upgrades` suivent ce fuseau **`Europe/Paris`** (et non UTC). Les horaires de la section 10 (dump à 03h00, rsync à 04h00, reboot auto à 04h30) sont donc bien des heures **locales**. Si vous changez le fuseau plus tard, ces horaires se décalent en conséquence. Pour lever toute ambiguïté, vous pouvez vérifier que `cron` voit le bon fuseau avec `cat /etc/timezone` (doit afficher `Europe/Paris`).

### 2.8. Créer un fichier d'échange (swap) si peu de RAM

Les petits VPS OVH disposent souvent de **2 à 4 Go de RAM**. Un build Docker (frontend Vite, image backend) ou un pic mémoire peut déclencher l'**OOM-killer**. Un fichier swap sert de filet de sécurité.

> ⚠️ **Le swap ne remplace PAS la RAM** et reste lent. Pour faire tourner **Ollama en local** (`llama3.1:8b` exige 5–6 Go rien que pour le modèle), il faut de la RAM réelle, pas du swap (voir section 8). Sur un VPS sans GPU et peu doté, privilégiez un backend LLM cloud. Le swap reste utile pour absorber les builds et les pics ponctuels. Il **ne dispense pas** de plafonner la RAM des conteneurs (section 6.7), qui borne réellement la consommation pour protéger Postgres.

Vérifiez d'abord la RAM et un éventuel swap existant :

```bash
free -h
```

Si la colonne `Swap` est à `0B` et que vous avez peu de RAM, créez un fichier swap de 2 Go (ajustez à 4 Go si la RAM est très faible) et rendez-le permanent :

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Réglez un `swappiness` bas (privilégie la RAM, n'utilise le swap qu'en dernier recours) et confirmez :

```bash
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-swappiness.conf
sudo sysctl --system
free -h
```

### 2.9. Configurer fail2ban

`fail2ban` bannit automatiquement les IP qui multiplient les tentatives de connexion SSH échouées. Le paquet a été installé à l'étape 2.5. Créez une configuration locale (ne modifiez jamais `jail.conf` directement, il est écrasé aux mises à jour) :

```bash
sudo tee /etc/fail2ban/jail.local > /dev/null <<'EOF'
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
backend  = systemd

[sshd]
enabled = true
EOF
```

> ⚠️ **Sur Ubuntu 24.04, les logs SSH ne sont plus dans un fichier `/var/log/auth.log` classique mais dans le journal systemd.** D'où `backend = systemd` ci-dessus : sans cela, la jail `sshd` peut ne rien surveiller. C'est un piège fréquent sur les versions récentes.

Activez et démarrez le service, puis vérifiez l'état de la jail SSH :

```bash
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

### 2.10. Configurer le pare-feu UFW (ports 22 / 80 / 443 uniquement)

Le pare-feu local n'ouvre que le strict nécessaire : **SSH (22)**, **HTTP (80)** et **HTTPS (443)**. Le proxy Caddy (section 7) sera le **seul** service exposé sur 80/443. Les ports applicatifs — **postgres 5432, ollama 11434, backend 8000, frontend 3000** — ne doivent **jamais** être ouverts sur Internet.

> ⚠️ **Ordre impératif : autorisez SSH AVANT d'activer UFW**, sinon `ufw enable` coupe votre session en cours.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

Vous devez voir `22/tcp`, `80/tcp`, `443/tcp` en `ALLOW IN`, et la politique par défaut `deny (incoming)`. Aucune ligne pour 5432, 11434, 8000 ou 3000 ne doit apparaître.

> ⚠️ **Piège Docker + UFW.** Docker manipule directement `iptables` et **contourne UFW** : un port publié via `ports:` dans un `docker-compose.yml` (ex. `5432:5432`) peut être joignable depuis Internet **même si UFW le bloque en apparence**. La parade dans ce guide est de **ne publier aucun port applicatif** en production (section 6) — les services restent sur le réseau Docker interne, seul Caddy expose 80/443. Si vous devez exposer un port pour du débogage, bindez-le explicitement sur la boucle locale (`127.0.0.1:8000:8000`), jamais `0.0.0.0`. Dans ce cas, c'est le **bind loopback lui-même** qui protège d'Internet, **pas** UFW (que Docker contourne).

### 2.11. Pare-feu réseau et anti-DDoS OVH (couche externe)

En complément d'UFW (qui agit **sur** le VPS), OVHcloud fournit deux protections en amont, côté infrastructure :

- **Protection anti-DDoS** : active **en permanence et automatiquement** sur les VPS OVH, sans configuration de votre part. Elle absorbe les attaques volumétriques avant qu'elles n'atteignent votre serveur. Rien à faire, mais bon à savoir en cas d'incident.
- **Firewall Network (pare-feu réseau OVH)** : un pare-feu **matériel en amont** du VPS, configurable depuis l'espace client. Il agit avant le système, donc avant UFW et avant Docker — ce qui le rend utile précisément parce qu'il **n'est pas contourné par Docker** (contrairement à UFW, cf. piège ci-dessus). Dans la fiche de votre VPS, cherchez la zone réseau / sécurité IP permettant d'ajouter des règles de filtrage sur l'IP du serveur.

> ⚠️ **Le Firewall Network OVH est en mode « stateless »** (il ne suit pas l'état des connexions). Mal configuré, il peut casser des connexions sortantes ou des réponses légitimes. Pour la formation, **UFW sur le VPS suffit dans la plupart des cas** ; n'activez le Firewall Network OVH que si vous maîtrisez les règles stateless (penser à autoriser le trafic retour sur les ports hauts), ou pour bloquer en urgence une plage d'IP malveillante en amont du serveur.

### État du serveur après cette section

| Élément | État attendu |
|---|---|
| Connexion SSH | Par clé Ed25519 uniquement, en `<USER>` |
| Login root SSH | Désactivé |
| Auth par mot de passe SSH | Désactivée |
| Compte de travail | `<USER>` avec `sudo` |
| Système | À jour + mises à jour de sécurité auto |
| Fuseau horaire | `Europe/Paris`, NTP synchronisé (impacte cron) |
| Swap | Actif si RAM faible (`swappiness=10`) |
| fail2ban | Jail `sshd` active (backend systemd) |
| UFW | `deny incoming` ; seuls 22/80/443 ouverts |
| OVH | Anti-DDoS actif ; Firewall Network optionnel |

> ⚠️ **Rappel sécurité transverse** : ce durcissement réseau ne protège pas des secrets exposés. La clé SMTP Brevo committée en clair dans le dépôt public devra être **révoquée, régénérée ET purgée de l'historique Git** (section 4), et le `.env` de prod devra rester **hors du dépôt**, en permissions `600`.

---

## 3. Installer Docker Engine + Compose v2

Cette section installe **Docker Engine** et le plugin **Compose v2** depuis le dépôt officiel Docker. C'est le socle technique : tout le reste du déploiement (Caddy, gunicorn, build statique du frontend, Postgres) repose sur `docker compose`.

> ⚠️ **Pourquoi PAS `apt install docker.io` ?** Le paquet `docker.io` des dépôts Ubuntu est souvent en retard de plusieurs versions et **n'inclut pas le plugin Compose v2** (la commande `docker compose`, en deux mots). Vous devriez alors installer séparément l'ancien `docker-compose` v1 (en Python, en un mot avec tiret), aujourd'hui **abandonné**. Le Kit utilise exclusivement la syntaxe `docker compose` (v2). Le dépôt officiel Docker fournit Engine + Buildx + Compose v2 à jour, ensemble : c'est la seule voie supportée ici.

### 3.1. Prérequis et purge des anciens paquets

Connecté en SSH (`ssh <USER>@<IP_VPS>`), installez les prérequis du dépôt HTTPS, puis retirez toute installation Docker antérieure issue des dépôts Ubuntu :

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
  sudo apt-get remove -y $pkg
done
```

> ⚠️ Cette commande désinstalle les **binaires** mais **ne supprime PAS** vos images, conteneurs ni volumes. Sur un VPS fraîchement provisionné, il est normal qu'`apt` réponde « Package ... is not installed » : ce n'est pas une erreur.

### 3.2. Ajouter la clé GPG et le dépôt officiels Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

La commande détecte automatiquement votre architecture et le codename Ubuntu (`noble` pour 24.04).

> ⚠️ Si `sudo apt-get update` renvoie une erreur de signature GPG (`NO_PUBKEY` ou `signed-by`), c'est presque toujours que l'étape précédente a échoué (clé absente ou droits trop restrictifs). Vérifiez que `/etc/apt/keyrings/docker.asc` existe et est lisible (`ls -l /etc/apt/keyrings/`) avant de continuer.

### 3.3. Installer Docker Engine + Compose v2

```bash
sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

| Paquet | Rôle |
| --- | --- |
| `docker-ce` | Le démon Docker Engine (le service `dockerd`). |
| `docker-ce-cli` | La commande `docker`. |
| `containerd.io` | Le runtime de conteneurs sous-jacent. |
| `docker-buildx-plugin` | Build d'images moderne (nécessaire au build multi-stage du frontend et du backend). |
| `docker-compose-plugin` | **Compose v2** : la commande `docker compose` utilisée par tout le Kit. |

### 3.4. Activer Docker au démarrage et autoriser `<USER>`

```bash
sudo systemctl enable --now docker
sudo systemctl status docker --no-pager   # attendu : Active: active (running)
sudo usermod -aG docker <USER>
```

> ⚠️ **Le changement de groupe n'est PAS actif dans la session SSH courante.** Vous devez **vous déconnecter puis vous reconnecter** (ou ouvrir une nouvelle session SSH) pour que l'appartenance au groupe prenne effet :
> ```bash
> exit
> ssh <USER>@<IP_VPS>
> ```
> Astuce : `newgrp docker` recharge le groupe dans le shell courant, mais une reconnexion propre reste la méthode la plus fiable.

> ⚠️ **Note de sécurité.** Appartenir au groupe `docker` équivaut à des privilèges `root` sur la machine (on peut monter `/` dans un conteneur). N'ajoutez à ce groupe que les comptes d'administration de confiance — jamais un compte partagé étudiant sur un VPS de production.

### 3.5. Plafonner les logs Docker (rotation) — avant de lancer la stack

C'est le bon moment pour plafonner la taille des logs au niveau du démon : un service bavard peut sinon saturer le disque et faire tomber tout le VPS (y compris Postgres). À faire **avant** de lancer la stack, car un `systemctl restart docker` redémarre les conteneurs.

```bash
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
EOF
sudo systemctl restart docker
```

Chaque conteneur est désormais plafonné à 3 × 10 Mo de logs.

### 3.6. Vérifier l'installation

Après reconnexion, contrôlez les versions. La commande clé est `docker compose version` (en **deux mots** = plugin v2) :

```bash
docker --version
docker compose version
docker buildx version
docker run --rm hello-world
```

Sorties attendues (les numéros peuvent différer, l'important est le format `Docker Compose version v2.x.x`). Le `hello-world` doit réussir **sans `sudo`** (confirme que l'étape 3.4 a pris effet).

> ⚠️ La syntaxe `!reset` employée par l'override de prod (section 6) requiert **Compose v2.24+**. Vérifiez que `docker compose version` affiche au moins `v2.24`. C'est le cas avec le paquet `docker-compose-plugin` officiel récent ; en cas de version plus ancienne, voir le repli loopback en section 6.5.

> ⚠️ Si `docker compose version` renvoie `docker: 'compose' is not a docker command`, le plugin Compose v2 n'est pas installé : reprenez l'étape 3.3. Et si vous voyez `docker-compose` (avec un tiret) installé quelque part, **ne l'utilisez pas** — c'est la v1 abandonnée, incompatible avec les fichiers `docker-compose.prod.yml` de ce guide.

---

## 4. Récupérer le code & créer le `.env` de PRODUCTION

Cette étape récupère le code du Kit sur le VPS et construit un fichier `.env` **de production** propre, dérivé de `.env.example` mais débarrassé de toutes les valeurs de démonstration dangereuses. Les commandes sont à exécuter en tant qu'utilisateur non-root `<USER>`.

> ⚠️ **Avant toute chose — la clé SMTP Brevo du dépôt public est compromise.** Le fichier `.env.example` du dépôt contient une **vraie clé SMTP Brevo en clair** (`BREVO_SMTP_KEY=xsmtpsib-...`) et son login, dans un repo **public**. Considérez-la comme **déjà fuitée**. Trois actions sont nécessaires (détaillées en 4.6) : (1) **révoquer** la clé côté Brevo, (2) **scanner** l'historique Git pour repérer tous les secrets, (3) idéalement **purger l'historique**. La retirer du fichier courant ne suffit **pas** : elle reste dans l'historique public.

### 4.1. Cloner le dépôt

Connecté en SSH, placez-vous dans le répertoire de l'utilisateur et clonez le dépôt (ou le fork de votre équipe).

```bash
cd ~
git clone https://github.com/melafrit/IPSSI_APOCAL_KIT.git
cd IPSSI_APOCAL_KIT/Kit
ls -1 docker-compose.yml .env.example Makefile
```

> 💡 **Fork d'équipe :** si votre équipe travaille sur un fork, remplacez l'URL par celle de votre dépôt. Pour un dépôt **privé**, préférez le SSH (`git@github.com:<orga>/IPSSI_APOCAL_KIT.git`) après avoir déposé une clé de déploiement, ou un *Personal Access Token* — jamais votre mot de passe GitHub en clair.

> ℹ️ **Convention de chemin pour tout le guide.** On suppose désormais le projet dans `/home/<USER>/IPSSI_APOCAL_KIT`, avec la racine applicative (docker-compose, `.env`, Makefile) dans le sous-dossier **`Kit/`** : `/home/<USER>/IPSSI_APOCAL_KIT/Kit`. Toutes les commandes des sections suivantes s'exécutent depuis ce dossier `Kit/`.

### 4.2. Vérifier que le `.env` est bien ignoré par Git

Le `.env` de prod contiendra de vrais secrets : il ne doit **jamais** partir dans un commit. Confirmez que Git l'ignore avant même de le créer.

```bash
git check-ignore .env && echo "OK : .env est ignore par git" || echo "ATTENTION : .env N'EST PAS ignore, corrigez .gitignore"
```

> ⚠️ **Si la commande répond « N'EST PAS ignoré »**, ajoutez la règle avant de continuer : `echo ".env" >> .gitignore`.

### 4.3. Créer le `.env` et générer des secrets robustes

On part du modèle fourni (ne modifiez pas `.env.example`, il reste versionné sans secrets), puis on génère les secrets nécessaires :

```bash
cp .env.example .env

# Clé secrète Django (chaîne aléatoire de 50+ caractères)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Mot de passe PostgreSQL fort (remplace l'inacceptable apocal-dev-only)
openssl rand -base64 32
```

**Gardez ces deux secrets sous la main** (copiez-les dans un gestionnaire de mots de passe, pas dans un fichier en clair).

> 💡 Si `python3` n'est pas installé : `sudo apt install -y python3`. `openssl` fonctionne d'office sur Ubuntu 24.04.

### 4.4. Éditer le `.env` avec les valeurs de production

```bash
nano .env
```

Appliquez **exactement** les changements suivants (remplacez les `<...>` et collez les secrets générés à l'étape 4.3) :

```dotenv
# --- Django : durcissement prod ---
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<collez_ici_la_sortie_de_secrets.token_urlsafe>
DJANGO_ALLOWED_HOSTS=<DOMAINE>,www.<DOMAINE>
CSRF_TRUSTED_ORIGINS=https://<DOMAINE>,https://www.<DOMAINE>
CORS_ALLOWED_ORIGINS=https://<DOMAINE>,https://www.<DOMAINE>
FRONTEND_URL=https://<DOMAINE>

# --- PostgreSQL : mot de passe fort (NE PAS laisser apocal-dev-only) ---
POSTGRES_DB=apocal
POSTGRES_USER=apocal
POSTGRES_PASSWORD=<collez_ici_la_sortie_de_openssl_rand>

# --- Frontend : l'URL de l'API est figée AU BUILD (vite build) ---
VITE_API_BASE_URL=https://<DOMAINE>/api

# --- LLM : sur VPS OVH sans GPU, NE PAS utiliser Ollama par defaut (voir section 8) ---
LLM_BACKEND=groq
GROQ_API_KEY=gsk_<votre_cle_groq>
GROQ_MODEL=llama-3.3-70b-versatile
LLM_API_TIMEOUT=60

# --- Email : laisser VIDE tant que vous n'avez pas une NOUVELLE cle Brevo ---
BREVO_SMTP_KEY=
BREVO_SMTP_LOGIN=
DEFAULT_FROM_EMAIL=EduTutor IA <contact@<DOMAINE>>
```

Précisions, point par point :

- **`DJANGO_DEBUG=False`** — obligatoire. Laissé à `True` (la valeur par défaut du modèle !), Django afficherait la stack trace complète, ses settings et vos variables d'environnement à la moindre erreur 500. C'est aussi `DEBUG=False` qui **active** le durcissement de sécurité ajouté en section 5.
- **`DJANGO_SECRET_KEY`** — la valeur du modèle (`change-me-en-production`) est publique et connue : la garder casserait toute la sécurité des sessions et des tokens.
- **`DJANGO_ALLOWED_HOSTS`** — votre **vrai domaine** (pas `*`). Ajoutez `<IP_VPS>` uniquement si vous devez tester l'accès par IP avant la propagation DNS.
- **`CSRF_TRUSTED_ORIGINS` / `CORS_ALLOWED_ORIGINS`** — exigent le **schéma** `https://` (contrairement à `ALLOWED_HOSTS`). Détaillé en section 5. Sans eux : 403 CSRF sur l'admin/Swagger et appels bloqués.
- **`FRONTEND_URL`** — utilisée par Django pour construire les liens cliquables des emails (validation de compte, reset password). Doit pointer vers votre domaine HTTPS public, sinon les liens des emails restent en `http://localhost:3000`.
- **`POSTGRES_PASSWORD`** — collez le mot de passe `openssl`. C'est l'unique rempart de la base ; en prod le port 5432 ne sera plus exposé (section 6), mais un mot de passe fort reste indispensable.
- **`VITE_API_BASE_URL`** — Vite **fige cette valeur au moment du `vite build`**, pas au runtime. Elle doit pointer vers votre domaine HTTPS public avant de builder le frontend. La changer plus tard impose un **rebuild** de l'image.
- **`LLM_BACKEND`** — `groq` recommandé par défaut (free tier, très rapide). Alternatives : `mistral` (UE, meilleur pour le RGPD), `gemini`, `cerebras`. Ne gardez `ollama` que si votre VPS a ≥ 8 Go de RAM dédiables (section 8).
- **`BREVO_SMTP_KEY` / `BREVO_SMTP_LOGIN`** — laissez **vides** pour l'instant. Sans clé, Django bascule sur l'envoi « console » (inoffensif : l'email s'affiche dans les logs). Vous ne remettrez ici qu'une **nouvelle** clé Brevo régénérée.

Enregistrez et quittez nano : `Ctrl+O`, `Entrée`, puis `Ctrl+X`.

> ⚠️ **Le piège des secrets de démo.** Le `.env` fraîchement copié hérite **de toutes** les valeurs de `.env.example`, y compris la clé Brevo compromise, le mot de passe `apocal-dev-only`, `DJANGO_SECRET_KEY=change-me-en-production` et `DJANGO_DEBUG=True`. Si vous ne les écrasez pas un par un comme ci-dessus, vous déployez en prod avec exactement les failles que cette section cherche à éliminer.

### 4.5. Restreindre les permissions et contrôle final

Le fichier ne doit être lisible que par son propriétaire :

```bash
chmod 600 .env
chown <USER>:<USER> .env
ls -l .env   # attendu : -rw-------
```

Confirmez en un coup d'œil qu'aucun secret de démo ne subsiste et que le `.env` ne sera pas committé :

```bash
# Doit renvoyer AUCUNE ligne (sinon, une valeur dangereuse traine encore) :
grep -E "apocal-dev-only|change-me-en-production|dev-secret-key-change-me|DJANGO_DEBUG=True|xsmtpsib-" .env

# Doit confirmer que git ignore bien le fichier :
git check-ignore .env
```

### 4.6. Révoquer, scanner et purger la clé Brevo fuitée

Retirer la clé du `.env` courant ne suffit pas : elle reste dans l'**historique public** du dépôt et dans `.env.example`. Trois actions, dans l'ordre :

**1. Révoquer (le plus urgent).** Connectez-vous sur https://app.brevo.com/settings/keys/smtp, supprimez/désactivez la clé SMTP fuitée et générez-en une nouvelle. La révocation rend la clé fuitée inopérante, même si elle reste lisible quelque part.

**2. Scanner l'historique Git** pour recenser tous les secrets exposés (la clé Brevo, mais aussi d'éventuels autres) avec un outil dédié, par exemple `gitleaks` :

```bash
# Installation rapide de gitleaks (binaire unique)
cd /tmp
curl -sSL https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_$(uname -s | tr A-Z a-z)_x64.tar.gz | tar xz gitleaks
sudo install gitleaks /usr/local/bin/

# Scan de tout l'historique du dépôt
cd /home/<USER>/IPSSI_APOCAL_KIT
gitleaks detect --source . --verbose
```

(Alternative équivalente : `trufflehog git file://.`.)

**3. Purger l'historique** si vous contrôlez le dépôt (ou un fork). Le scan confirmera que la clé est dans l'historique ; pour l'en retirer, réécrivez l'historique avec `git filter-repo` (recommandé par GitHub) ou BFG :

```bash
# Exemple avec git-filter-repo (à installer : pipx install git-filter-repo)
# Remplace toute occurrence de la clé par ***REMOVED*** dans tout l'historique.
cd /home/<USER>/IPSSI_APOCAL_KIT
echo 'xsmtpsib-***==>***REMOVED***' > /tmp/secrets-rules.txt   # adaptez au motif exact trouvé
git filter-repo --replace-text /tmp/secrets-rules.txt
git push --force --all      # réécrit l'historique distant (préviens ton équipe avant)
```

> ⚠️ **La purge d'historique réécrit tous les commits** : tous les collaborateurs devront re-cloner. Prévenez l'équipe. **Quoi qu'il arrive, l'étape 1 (révocation) reste la seule garantie réelle** : une clé fuitée dans un dépôt public a pu être moissonnée par des bots en quelques minutes ; on la considère comme définitivement compromise.

> ⚠️ **Rappel final, non négociable :**
> 1. Le `.env` de prod **ne doit jamais être committé ni poussé**.
> 2. La clé Brevo doit être **révoquée**, et idéalement **purgée de l'historique** (la retirer du fichier courant ne suffit pas).
> 3. Ne lancez **jamais** `make seed` sur l'instance de prod : il crée un compte de démo public (`test` / `motdepasse123`). Voir aussi la vérification 4.7 si la base provient d'une instance dev.

### 4.7. (Migration depuis une instance dev) Vérifier l'absence du compte de démo

Si la base de prod est **repartie d'un dump issu d'une instance dev** (et non d'une base vierge), le compte `make seed` (`test` / `motdepasse123`, documenté et public) peut **déjà exister**. Ne jamais lancer `make seed` ne suffit alors pas : il faut **vérifier et supprimer** le compte s'il est présent. Cette commande est à exécuter une fois les conteneurs lancés (après la section 9), elle est rappelée ici pour mémoire :

```bash
# Vérifier l'existence du compte de démo
dcprod exec backend python manage.py shell -c \
  "from django.contrib.auth import get_user_model; U=get_user_model(); print('PRESENT' if U.objects.filter(username='test').exists() else 'absent')"

# Le supprimer s'il est présent
dcprod exec backend python manage.py shell -c \
  "from django.contrib.auth import get_user_model; U=get_user_model(); U.objects.filter(username='test').delete(); print('compte test supprime')"
```

---

## 5. Adapter le CODE Django pour la production (`settings.py`)

Avant de toucher à Docker, deux corrections de **code** sont indispensables, sinon le but « admin Django et Swagger fonctionnels en HTTPS » n'est **pas** atteint et `check --deploy` (section 9.5) reste rempli de warnings. Le `settings.py` du Kit ne contient **ni** WhiteNoise, **ni** `CSRF_TRUSTED_ORIGINS`, **ni** les cookies sécurisés / HSTS / `SECURE_PROXY_SSL_HEADER`. On les ajoute ici, pilotés par `DEBUG=False`.

> ℹ️ Le fichier concerné est `backend/apocal/settings.py`. Éditez-le **localement dans votre fork** (puis `git pull` sur le VPS) ou directement sur le VPS avant le build. Ces modifications sont du **code** : elles doivent être versionnées (contrairement au `.env`).

### 5.1. Activer le service des fichiers statiques (WhiteNoise)

C'est le **point bloquant** signalé par l'audit. Avec `DEBUG=False`, **ni `runserver` ni gunicorn ne servent les fichiers statiques** : `collectstatic` remplit bien `staticfiles/`, mais rien ne le sert → le CSS/JS de l'**admin Django** et de **Swagger UI** renvoient 404 (interfaces visuellement cassées). Installer le paquet WhiteNoise (section 6.1) ne suffit **pas** : il faut l'**activer**.

Dans `backend/apocal/settings.py`, insérez le middleware WhiteNoise **juste après** `SecurityMiddleware` :

```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # avant CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # <-- AJOUT : sert /static/ en prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

Puis, dans la section « Statics » de `settings.py`, ajoutez le backend de stockage WhiteNoise (compression + manifeste à empreinte, pour un cache sûr) :

```python
# ----------------------------------------------------------------------------
# Statics
# ----------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Service des statiques en production par WhiteNoise (sans serveur web séparé).
# CompressedManifestStaticFilesStorage : fichiers compressés + noms à hash
# (cache long et invalidation automatique). Django 5.x utilise le réglage STORAGES.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

Avec WhiteNoise actif, **c'est Django/gunicorn qui sert `/static/`** ; le routage `@backend` du Caddyfile (section 7.2) envoie donc bien `/static/*` vers `backend:8000`, qui le sert correctement.

> ⚠️ **Une alternative existe** (faire servir `/static/` par Caddy via `file_server`), décrite en annexe 7.3. Ne combinez pas les deux : **soit** WhiteNoise (recommandé, retenu ici), **soit** Caddy `file_server`. Avec WhiteNoise activé, vous n'avez **rien** à changer dans le Caddyfile par rapport à la section 7.

### 5.2. Durcir cookies, HSTS, CSRF et proxy TLS

Le `settings.py` du Kit ne définit aucun de ces réglages. Résultat : `check --deploy` remonte des warnings (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, etc.) et le login admin échoue en **403 CSRF** derrière le proxy. Ajoutez le bloc suivant **à la fin** de `backend/apocal/settings.py` :

```python
# ----------------------------------------------------------------------------
# Durcissement production (actif uniquement quand DEBUG=False)
# ----------------------------------------------------------------------------
# CSRF : Django exige les origines de confiance AVEC le schéma https://
# (contrairement à ALLOWED_HOSTS qui ne prend que le nom d'hôte).
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://localhost",
    cast=Csv(),
)

if not DEBUG:
    # Django est derrière le proxy TLS de Caddy : le trafic interne
    # caddy -> backend:8000 est en HTTP clair. On fait confiance à l'en-tête
    # transmis par le proxy, sinon Django se croit en HTTP (cookies/redirections cassés).
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # Caddy gère déjà la redirection HTTP->HTTPS. On NE met PAS SECURE_SSL_REDIRECT
    # côté Django pour éviter une double redirection / boucle.
    SECURE_SSL_REDIRECT = False

    # Cookies de session et CSRF uniquement sur HTTPS.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS : force HTTPS côté navigateur pendant 1 an.
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Durcissements complémentaires attendus par check --deploy.
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
```

> ⚠️ **N'activez `SECURE_HSTS_SECONDS` qu'une fois le HTTPS confirmé fonctionnel.** HSTS demande aux navigateurs de **refuser le HTTP** pour votre domaine pendant 1 an : si le certificat est cassé après l'avoir posé, les visiteurs ne pourront plus accéder au site facilement. Validez d'abord le HTTPS en staging (section 7.4), puis gardez ces valeurs.

> ⚠️ **HSTS posé deux fois (Caddy + Django).** Le Caddyfile (section 7.2) ajoute déjà un en-tête `Strict-Transport-Security`. Avec WhiteNoise + Django qui le pose aussi, le navigateur peut recevoir l'en-tête en double. Ce n'est pas bloquant, mais pour éviter la redondance vous pouvez **retirer la ligne `Strict-Transport-Security` du bloc `header` du Caddyfile** et laisser Django seul le gérer (c'est `check --deploy` qui le réclame côté Django). Choisissez une seule source.

Ces réglages étant pilotés par `DEBUG=False`, ils **n'affectent pas** le développement local (où `DEBUG=True`).

---

## 6. Adapter la stack Docker pour la production (override Compose)

C'est l'étape la plus critique du déploiement. En l'état, le `docker-compose.yml` du Kit lance **Vite en serveur de dev** (`npm run dev`) pour le frontend et **Django en `runserver`** pour le backend, expose les 4 services (`5432`, `11434`, `8000`, `3000`) directement sur l'hôte, monte le code source via des bind mounts, et **réutilise un Dockerfile backend qui installe `requirements-dev.txt` + gcc** (image « dev »). **Aucun de ces choix n'est acceptable sur une machine publique.**

Plutôt que de modifier le fichier de dev (qui doit rester utilisable par les étudiants en local), on applique la stratégie d'**override Compose** : un second fichier `docker-compose.prod.yml` qui surcharge le premier. La commande finale fusionne les deux :

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

> ⚠️ **Principe de l'override.** Compose fusionne les deux fichiers clé par clé. Les `command`, `build`, `volumes`, `environment` du fichier de prod **remplacent** ceux du dev. **Mais** une section `ports:` ne peut pas être « supprimée » par simple override : Compose fusionne les listes de ports, il ne les vide pas. Pour réellement fermer un port, on l'écrase avec `!reset []` (Compose v2.24+). Le seul service réellement public sera Caddy sur `80/443`.

Tous les fichiers ci-dessous se créent à la racine `Kit/` (`/home/<USER>/IPSSI_APOCAL_KIT/Kit`).

### 6.1. Ajouter les dépendances de production manquantes (backend)

`gunicorn` et `whitenoise` sont **absents** de `backend/requirements.txt`. Sans eux, pas de serveur WSGI de prod ni de service des fichiers statiques. Ajoutez ces deux lignes à la fin de `backend/requirements.txt` :

```text
# --- Production (ajouté pour le déploiement VPS) ---
gunicorn==23.0.0
whitenoise==6.8.2
```

> ℹ️ Le paquet seul ne sert à rien sans l'activation faite en **section 5.1** (middleware + `STORAGES`). Les deux vont ensemble.

### 6.2. Créer le Dockerfile backend de PRODUCTION (multi-stage, sans dev-deps)

Le Dockerfile de dev (`docker/backend.Dockerfile`) fait `pip install -r requirements.txt -r requirements-dev.txt` et conserve `gcc` + `libpq-dev` dans l'image finale : l'image embarque pytest, black, ruff, faker **et un compilateur** — surface d'attaque et poids inutiles en prod. On crée un Dockerfile prod **multi-stage** : un stage *builder* avec le compilateur pour fabriquer les wheels, un stage *runtime* slim sans compilateur, n'installant **que** `requirements.txt`.

Créez `docker/backend.prod.Dockerfile` :

```dockerfile
# ============================================================================
# IPSSI_APOCAL_KIT — Dockerfile backend PRODUCTION (multi-stage, sans dev-deps)
# ============================================================================

# ---- Stage 1 : builder (compile les wheels) ----
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Outils de compilation UNIQUEMENT dans le builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# On n'installe QUE les deps de prod (pas requirements-dev.txt)
COPY requirements.txt ./
RUN pip wheel --wheel-dir=/wheels -r requirements.txt

# ---- Stage 2 : runtime (slim, sans compilateur) ----
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# libpq seule (runtime psycopg), PAS gcc ni libpq-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Installe les wheels pré-compilées au stage builder (aucune compilation ici)
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

# Code applicatif
COPY . .

EXPOSE 8000

# gunicorn par défaut (PLUS de runserver). La command effective est fixée
# dans docker-compose.prod.yml (workers/timeout ajustables).
CMD ["gunicorn", "apocal.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
```

> ℹ️ `curl` est installé dans le runtime pour permettre un healthcheck léger (`curl` sur `/health/`). Si vous préférez ne rien ajouter, le healthcheck Python (sans dépendance externe) de la section 6.4 fonctionne aussi.

### 6.3. Créer le Dockerfile de production du frontend (multi-stage → Nginx)

Le frontend de prod doit être un **bundle statique buildé** (`npm run build` = `tsc -b && vite build`), servi par un petit Nginx — jamais le serveur de dev Vite.

> ⚠️ **`VITE_API_BASE_URL` est figée au BUILD, pas au runtime.** Vite remplace `import.meta.env.VITE_API_BASE_URL` par sa valeur littérale au moment du `vite build`. On la passe donc en **ARG Docker** au build, pointée vers `https://<DOMAINE>/api`. Changer cette URL plus tard **exige un rebuild de l'image** (`--build`).

Créez `docker/frontend.prod.Dockerfile` :

```dockerfile
# ============================================================================
# IPSSI_APOCAL_KIT — Dockerfile frontend PRODUCTION (multi-stage → nginx)
# ============================================================================

# ---- Stage 1 : build du bundle statique ----
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# URL de l'API injectée au BUILD (figée dans le bundle)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY . .
RUN npm run build            # tsc -b && vite build → génère /app/dist

# ---- Stage 2 : service statique léger ----
FROM nginx:1.27-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
# nginx:alpine définit déjà le bon CMD (nginx -g 'daemon off;')
```

> ⚠️ **Contexte de build.** Le `COPY docker/nginx.conf ...` impose que le **contexte de build soit la racine `Kit/`** (et non `./frontend`), pour que le dossier `docker/` soit visible. Le `docker-compose.prod.yml` ci-dessous fixe donc `context: .` pour le frontend. Conséquence : ajoutez un `.dockerignore` à la racine (étape 6.6), sinon `node_modules` et `dist` de l'hôte seraient copiés dans le contexte.

### 6.4. Créer la configuration Nginx interne du frontend (fallback SPA)

Le frontend utilise `react-router-dom`. Sans fallback `try_files`, un rechargement (F5) sur une route profonde type `/login` renverrait un 404. Cette Nginx **interne** ne gère QUE les fichiers statiques du frontend ; le routage `/api` vers le backend est assuré par Caddy (section 7).

Créez `docker/nginx.conf` :

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Fallback SPA : toute route inconnue renvoie index.html (react-router)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Assets hashés par Vite : cache long et immuable
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # index.html ne doit jamais être mis en cache (sinon vieux bundle servi)
    location = /index.html {
        add_header Cache-Control "no-cache";
    }

    # Endpoint de santé pour le healthcheck du conteneur
    location = /healthz {
        access_log off;
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
```

### 6.5. Créer le fichier d'override `docker-compose.prod.yml`

Ce fichier est le cœur de l'adaptation. Il : (1) reconstruit le frontend en statique Nginx, (2) ajoute un service **one-shot `migrate`** (migrations + collectstatic, joué **une seule fois**, pas par chaque worker gunicorn), (3) lance le backend via le **Dockerfile prod** + `gunicorn`, (4) ferme l'exposition hôte des 4 services applicatifs, (5) ajoute `restart`, des **healthchecks sur `/health/`** (et non `/api/llm/ping/`) et des **limites RAM/CPU**, (6) épingle les images de base, (7) ajoute **Caddy** comme seul point d'entrée public. Le service `ollama` est placé derrière un **profil optionnel** `ollama`.

Créez `docker-compose.prod.yml` à la racine `Kit/` :

```yaml
# ============================================================================
# IPSSI_APOCAL_KIT — Override PRODUCTION
# Usage :
#   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
# ============================================================================

services:

  # --------------------------------------------------------------------------
  # POSTGRES : plus d'exposition publique. Limite mémoire pour protéger l'hôte.
  # --------------------------------------------------------------------------
  postgres:
    restart: unless-stopped
    ports: !reset []          # neutralise la liste de ports héritée du dev
    deploy:
      resources:
        limits:
          memory: 512m

  # --------------------------------------------------------------------------
  # OLLAMA : optionnel (profil "ollama"). Par défaut NON démarré en prod
  # (VPS sans GPU = trop lent — voir section 8). Plus d'exposition du 11434.
  # Limite mémoire stricte pour éviter qu'il n'étouffe Postgres en cas d'OOM.
  # --------------------------------------------------------------------------
  ollama:
    restart: unless-stopped
    profiles: ["ollama"]
    ports: !reset []
    image: ollama/ollama:0.5.7   # version épinglée (plus de :latest)
    deploy:
      resources:
        limits:
          memory: 7g            # adaptez selon la RAM du VPS (cas B section 1.2)

  # --------------------------------------------------------------------------
  # MIGRATE : service ONE-SHOT. Joue migrate + collectstatic UNE fois, puis
  # s'arrête (restart: "no"). Évite que chaque worker/réplica gunicorn ne
  # relance migrate (migrations concurrentes si on scale).
  # --------------------------------------------------------------------------
  migrate:
    build:
      context: ./backend
      dockerfile: ../docker/backend.prod.Dockerfile
    image: apocalipssi-2026-backend:prod
    env_file:
      - .env
    restart: "no"
    command: >
      sh -c "python manage.py migrate --noinput &&
             python manage.py collectstatic --noinput"
    depends_on:
      postgres:
        condition: service_healthy

  # --------------------------------------------------------------------------
  # BACKEND : gunicorn (PLUS de runserver), image PROD (sans dev-deps).
  # Ne fait PAS migrate (délégué à 'migrate'). Healthcheck sur /health/
  # (toujours 200, ne dépend PAS du LLM). Plus d'exposition, plus de bind mount.
  # --------------------------------------------------------------------------
  backend:
    restart: unless-stopped
    build:
      context: ./backend
      dockerfile: ../docker/backend.prod.Dockerfile
    image: apocalipssi-2026-backend:prod
    volumes: !reset []        # supprime le bind mount ./backend:/app du dev
    ports: !reset []          # plus de port 8000 sur l'hôte
    command: >
      gunicorn apocal.wsgi:application
        --bind 0.0.0.0:8000
        --workers 3
        --timeout 120
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health/ || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 5
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 768m
    depends_on:
      postgres:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully

  # --------------------------------------------------------------------------
  # FRONTEND : bundle statique Vite servi par nginx (multi-stage).
  # Contexte de build = racine Kit/ (pour accéder à docker/nginx.conf).
  # --------------------------------------------------------------------------
  frontend:
    restart: unless-stopped
    build:
      context: .
      dockerfile: docker/frontend.prod.Dockerfile
      args:
        VITE_API_BASE_URL: "https://<DOMAINE>/api"
    image: apocalipssi-2026-frontend:prod
    volumes: !reset []        # supprime ./frontend:/app et /app/node_modules
    ports: !reset []          # plus de port 3000 sur l'hôte
    command: !reset null      # neutralise "npm run dev" ; on garde le CMD nginx
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost/healthz || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 10s
    deploy:
      resources:
        limits:
          memory: 128m
    depends_on:
      backend:
        condition: service_healthy

  # --------------------------------------------------------------------------
  # CADDY : SEUL service exposé publiquement (80/443). HTTPS Let's Encrypt
  # automatique. Détaillé en section 7. Le Caddyfile doit exister à la racine.
  # --------------------------------------------------------------------------
  caddy:
    image: caddy:2.8-alpine
    container_name: apocalipssi-2026-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"        # HTTP/3 (QUIC)
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data       # certificats Let's Encrypt (NE PAS supprimer)
      - caddy-config:/config
    deploy:
      resources:
        limits:
          memory: 256m
    depends_on:
      frontend:
        condition: service_healthy
      backend:
        condition: service_healthy

volumes:
  caddy-data:
  caddy-config:
```

> ⚠️ **Healthcheck = `/health/`, pas `/api/llm/ping/`.** L'endpoint `/api/llm/ping/` renvoie **HTTP 503** quand `LLM_BACKEND=ollama` et qu'Ollama est injoignable ou que le modèle n'est pas encore téléchargé. Si on l'utilisait comme healthcheck du conteneur, le backend serait marqué `unhealthy` au démarrage Ollama → Caddy (qui dépend de `backend healthy`) ne démarrerait **jamais** → site entièrement indisponible. L'endpoint `/health/` (défini dans `apocal/urls.py`) renvoie **toujours 200** et n'appelle pas le LLM : il découple la santé du backend de celle d'Ollama. `/api/llm/ping/` reste réservé aux smoke tests manuels (section 9.10).

> ⚠️ **Le service `migrate` est en `restart: "no"`** : c'est un one-shot. Ne le mettez **jamais** en `unless-stopped` (il rejouerait `migrate`/`collectstatic` en boucle). Le backend en dépend via `condition: service_completed_successfully` : gunicorn ne démarre qu'une fois migrations et statiques prêtes. Ce schéma évite aussi les **migrations concurrentes** si vous montez le nombre de workers/replicas.

> ⚠️ **`!reset` requiert Compose v2.24+** (vérifié en section 3.6). **S'il n'est pas supporté** : Compose **ne sait pas retirer** une clé héritée, il ne fait que fusionner. Écrasez alors les ports par une liaison **loopback** en réécrivant la liste — ex. pour le backend `ports: ["127.0.0.1:8000:8000"]`. **Important :** c'est le **bind sur `127.0.0.1` lui-même** qui rend le service injoignable depuis Internet (le paquet n'est jamais publié sur l'interface publique), **pas** UFW — qui, on l'a vu (section 2.10), est contourné par Docker pour les ports publiés en `0.0.0.0`. Ne présentez donc pas UFW comme le garant de fermeture des ports Docker. Pour `postgres`, notez que même bindé sur `127.0.0.1`, la base reste joignable par tout processus de l'hôte : le mot de passe fort (section 4) reste indispensable. Le cas nominal `!reset []` (aucun port publié) est de loin préférable.

> ⚠️ **Le `Caddyfile` est créé à la section 7.** Ce fichier le référence (`./Caddyfile`) : il doit exister à la racine `Kit/` avant le `up`, sinon Caddy ne démarrera pas.

### 6.6. Ajouter un `.dockerignore` à la racine

Comme le contexte de build du frontend devient la racine `Kit/`, empêchez la copie de gros dossiers inutiles (qui ralentiraient le build et pourraient écraser le `dist/` propre généré dans l'image). Créez `.dockerignore` à la racine `Kit/` :

```text
**/node_modules
**/dist
**/__pycache__
**/.pytest_cache
backend/staticfiles
.git
.env
*.md
```

### 6.7. Limites de ressources et épinglage des images

Deux durcissements de prod, déjà intégrés au `docker-compose.prod.yml` ci-dessus mais à comprendre :

- **Limites RAM/CPU (`deploy.resources.limits`)** : sur un petit VPS, rien ne plafonne nativement la consommation d'un conteneur. Un pic (build, Ollama, fuite mémoire) peut faire passer la machine en swap ou déclencher l'OOM-killer **sur Postgres**. Les `limits.memory` ci-dessus bornent chaque service ; **ajustez-les à la RAM réelle** de votre VPS (les valeurs données visent un VPS 4 Go en cas A ; en cas B avec Ollama, augmentez `ollama` et réduisez la marge ailleurs).

  > ℹ️ `deploy.resources.limits` est honoré par `docker compose` (hors Swarm) sur les versions récentes. Vérifiez l'application avec `docker stats --no-stream` après démarrage. Sur une version qui l'ignorerait, utilisez l'équivalent `mem_limit: 768m` au niveau du service.

- **Épinglage des images de base** : le guide épingle `postgres:16-alpine`, `ollama/ollama:0.5.7`, `caddy:2.8-alpine`, `nginx:1.27-alpine`. Les Dockerfiles `python:3.11-slim` et `node:20-alpine` restent sur des tags mineurs flottants. Pour des **builds totalement reproductibles**, épinglez-les par **digest** (récupéré une fois avec `docker buildx imagetools inspect python:3.11-slim`), par exemple :

  ```dockerfile
  FROM python:3.11-slim@sha256:<digest> AS builder
  ```
  ```dockerfile
  FROM node:20-alpine@sha256:<digest> AS builder
  ```

  C'est optionnel mais recommandé pour figer l'image exacte testée pendant la semaine de formation.

### 6.8. Vérifier la présence du `.env` de production

L'override charge toujours `env_file: .env` (hérité du dev). Sur le VPS, ce `.env` doit être le **`.env` de prod** créé à la section 4 (jamais versionné, permissions `600`) :

```bash
cd /home/<USER>/IPSSI_APOCAL_KIT/Kit
ls -l .env
chmod 600 .env
```

> ⚠️ **Ne lancez JAMAIS `make reset-db` ni `docker compose down -v` en prod** : `-v` supprime les volumes nommés, donc **toute la base Postgres**. La cible `reset-db` du Makefile est purement destructive et orientée dev (elle enchaîne `down -v` puis `make seed`).

Récapitulatif des fichiers créés ou modifiés dans cette section et la précédente :

| Fichier | Action | Rôle |
|---|---|---|
| `backend/apocal/settings.py` | **modifié** | WhiteNoise (middleware + STORAGES), CSRF/cookies/HSTS/proxy TLS |
| `backend/requirements.txt` | modifié | ajout `gunicorn` + `whitenoise` |
| `docker/backend.prod.Dockerfile` | **créé** | image backend prod multi-stage, sans dev-deps ni compilateur |
| `docker/frontend.prod.Dockerfile` | créé | build statique Vite multi-stage → Nginx |
| `docker/nginx.conf` | créé | service statique + fallback SPA react-router |
| `docker-compose.prod.yml` | créé | override prod : migrate one-shot, gunicorn, ports fermés, healthchecks `/health/`, limites RAM |
| `.dockerignore` | créé | allège le contexte de build (racine `Kit/`) |
| `Caddyfile` | section 7 | route publique 80/443 → frontend + /api backend |

---

## 7. Domaine, reverse proxy & HTTPS

Cette section met le Kit derrière un nom de domaine en HTTPS, avec **Caddy en conteneur** (certificat Let's Encrypt automatique). C'est la seule porte d'entrée publique : Caddy écoute sur `80` et `443`, et redistribue vers le frontend statique et le backend gunicorn **sur le réseau Docker interne**. Les services `postgres`, `ollama`, `backend` et `frontend` ne sont jamais exposés directement (sections 2.10 et 6).

> ⚠️ Prérequis : votre VPS a une IP publique `<IP_VPS>`, le port `22` est ouvert, et vous contrôlez la zone DNS de `<DOMAINE>`. La validation Let's Encrypt (HTTP-01) exige que `80` et `443` soient joignables depuis Internet : UFW les autorise déjà (section 2.10) ; vérifiez aussi le Firewall Network OVH s'il est activé.

### 7.1. Enregistrer le domaine en DNS (A / AAAA)

L'objectif est de faire pointer `<DOMAINE>` (et `www.<DOMAINE>`) vers l'IP du VPS.

1. Récupérez l'IP publique depuis le serveur :

   ```bash
   curl -4 ifconfig.me ; echo
   curl -6 ifconfig.me ; echo   # IPv6, si le VPS en a une
   ```

2. Connectez-vous à l'espace qui gère la **zone DNS** de votre domaine. Si le domaine est chez OVH : espace client, gestion des noms de domaine, onglet « zone DNS ». Sinon, même manipulation dans l'interface de votre registrar.

3. Créez les enregistrements à la racine (`@`) et pour `www` (remplacez `<IP_VPS>` par votre IPv4) :

   | Type   | Nom (sous-domaine) | Cible / Valeur          |
   |--------|--------------------|-------------------------|
   | `A`    | `@`                | `<IP_VPS>`              |
   | `A`    | `www`              | `<IP_VPS>`              |
   | `AAAA` | `@`                | `<IPv6_VPS>` (si IPv6)  |
   | `AAAA` | `www`              | `<IPv6_VPS>` (si IPv6)  |

   > ⚠️ N'ajoutez un `AAAA` **que** si le VPS a réellement une IPv6 fonctionnelle. Un `AAAA` qui pointe vers une IPv6 injoignable fait échouer la validation Let's Encrypt pour les clients en IPv6.

4. Laissez le TTL par défaut. La **propagation DNS** peut prendre de quelques minutes à plusieurs heures (jusqu'à 24-48 h selon le TTL précédent).

5. Vérifiez la propagation (`dnsutils` a été installé en section 2.5) :

   ```bash
   dig +short A <DOMAINE>
   dig +short A www.<DOMAINE>
   dig +short AAAA <DOMAINE>
   ```

   Chaque commande doit renvoyer `<IP_VPS>` (et l'IPv6 le cas échéant).

> ⚠️ Piège fréquent : ne mettez **pas** de `CNAME` ni d'« URL Redirect / redirection web » du registrar sur la racine — Caddy a besoin que `<DOMAINE>` résolve vers l'IP en `A`/`AAAA`. Si OVH a posé une redirection web par défaut, supprimez-la.

> ⚠️ Ne lancez **pas** Caddy en mode production tant que `dig +short A <DOMAINE>` ne renvoie pas la bonne IP : Let's Encrypt refuserait d'émettre le certificat et, après plusieurs échecs, vous pourriez atteindre ses **limites de débit** (attente d'une heure à une semaine). Pendant les tests, utilisez le staging (étape 7.4).

### 7.2. Créer le `Caddyfile`

Caddy route `/api/*`, `/admin/*`, `/static/*`, `/media/*` vers le **backend gunicorn** (`backend:8000`), et tout le reste (`/`) vers le **frontend statique** (`frontend:80`). Comme WhiteNoise est activé (section 5.1), `backend:8000` sert correctement `/static/`. Créez le fichier `Caddyfile` à la racine `Kit/` (à côté de `docker-compose.prod.yml`) :

```caddyfile
<DOMAINE>, www.<DOMAINE> {
    # Compression
    encode gzip zstd

    # API REST, admin Django et statiques Django -> backend gunicorn (WhiteNoise sert /static/)
    @backend path /api/* /admin/* /static/* /media/*
    reverse_proxy @backend backend:8000

    # Tout le reste -> frontend statique (SPA React derrière nginx interne)
    reverse_proxy frontend:80

    # En-têtes de sécurité de base
    # (HSTS volontairement omis ici : il est posé par Django, cf. section 5.2.
    #  Si vous préférez le gérer ici, ajoutez Strict-Transport-Security et
    #  retirez-le côté Django — une seule source.)
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }

    # Journaux d'accès
    log {
        output stdout
        format console
    }
}
```

> ⚠️ Le frontend doit avoir été buildé avec `VITE_API_BASE_URL=https://<DOMAINE>/api` (injecté **au build** — sections 4.4 et 6.3). Avec ce Caddyfile, frontend et API sont servis sur le **même domaine** : les appels `/api/...` restent same-origin, donc pas de problème CORS pour le frontend lui-même. CORS reste néanmoins nécessaire pour Swagger/d'autres origines (le `.env` le couvre, section 4.4).

> ⚠️ Le routage `@backend` envoie `/static/*` vers le backend : cela suppose que Django sert ses statiques via **WhiteNoise** (réellement activé en section 5.1). Le frontend sert ses propres assets buildés sous `/assets/*`, qui ne matchent pas `@backend` et partent donc bien vers `frontend:80`. Aucun chevauchement tant que le front n'utilise pas le préfixe `/static/`.

Le service `caddy` lui-même (ports, volumes `caddy-data`/`caddy-config`) est déjà déclaré dans le `docker-compose.prod.yml` de la section 6.5.

> ⚠️ Le volume `caddy-data` contient vos certificats et clés ACME. Ne le supprimez jamais en routine (un `docker compose down -v` le détruirait) : sans lui, Caddy redemande un certificat à chaque redémarrage et vous risquez les limites de débit Let's Encrypt.

### 7.3. (Alternative au 5.1) Servir `/static/` par Caddy plutôt que WhiteNoise

Si vous **ne voulez pas** activer WhiteNoise, l'autre solution opérationnelle est de faire servir le dossier `staticfiles/` **par Caddy** via `file_server`. Dans ce cas, **n'ajoutez pas** WhiteNoise (section 5.1), montez le volume `staticfiles` dans Caddy, et remplacez le routage des statiques :

```caddyfile
<DOMAINE>, www.<DOMAINE> {
    encode gzip zstd

    # Statiques Django servis directement par Caddy (file_server), pas le backend
    handle_path /static/* {
        root * /srv/static
        file_server
    }

    # API + admin -> backend gunicorn (sans /static/)
    @backend path /api/* /admin/* /media/*
    reverse_proxy @backend backend:8000

    reverse_proxy frontend:80
    # ... (header, log identiques)
}
```

…et côté `docker-compose.prod.yml`, ajoutez un volume partagé `staticfiles` rempli par le service `migrate` (`collectstatic`) puis monté en lecture seule dans `caddy` (`- staticfiles:/srv/static:ro`). **Choisissez une seule des deux approches** : WhiteNoise (5.1, recommandé et retenu pour le reste du guide) **ou** `file_server` Caddy ici — jamais les deux.

### 7.4. (Pendant les tests) Utiliser le staging Let's Encrypt

Pour éviter d'épuiser les quotas Let's Encrypt pendant la mise au point, utilisez l'autorité de **staging**. Ajoutez un bloc global en tête du `Caddyfile` :

```caddyfile
{
    # STAGING : certificats NON reconnus par les navigateurs, mais quota très large.
    # À RETIRER pour passer en production.
    acme_ca https://acme-staging-v02.api.letsencrypt.org/directory
    email <USER>@<DOMAINE>
}

<DOMAINE>, www.<DOMAINE> {
    # ... (même contenu qu'en 7.2)
}
```

Une fois la configuration validée, **supprimez la ligne `acme_ca`** (gardez le bloc `email` pour les notifications d'expiration), puis `docker compose ... restart caddy` pour obtenir un vrai certificat.

> ⚠️ En passant de staging à production, le navigateur peut garder en cache l'ancien certificat de staging. Si l'erreur persiste, supprimez le certificat de staging stocké dans le volume : `docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy rm -rf /data/caddy/certificates` puis redémarrez Caddy.

> ⚠️ **N'activez le HSTS de Django (section 5.2) qu'après avoir validé le vrai certificat de production.** HSTS testé sous staging peut « épingler » un domaine en HTTPS alors que le certificat n'est pas reconnu, rendant l'accès pénible. Confirmez d'abord un cadenas valide en production.

### 7.5. Vérifier le HTTPS et la redirection

Une fois la stack démarrée (section 9), suivez les logs de Caddy : au premier démarrage, il demande automatiquement le certificat à Let's Encrypt (challenge HTTP-01 sur le port 80) et vous devez voir `certificate obtained successfully`. Le HTTPS, la redirection HTTP→HTTPS et le renouvellement automatique sont alors actifs sans configuration supplémentaire.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f caddy

curl -I http://<DOMAINE>       # attendu : 301/308 vers https://
curl -I https://<DOMAINE>      # attendu : HTTP/2 200, en-tête strict-transport-security
curl -sS https://<DOMAINE>/api/llm/ping/   # doit atteindre le backend
```

Ouvrez enfin `https://<DOMAINE>` dans un navigateur : le cadenas doit être valide.

### 7.6. Rappel : CSRF / CORS / proxy TLS sont déjà alignés

Les variables `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `DJANGO_ALLOWED_HOSTS` sont renseignées dans le `.env` (section 4.4), et `CSRF_TRUSTED_ORIGINS` + `SECURE_PROXY_SSL_HEADER` ont été **ajoutés à `settings.py`** en section 5.2. Rien de plus à faire ici : le login de `https://<DOMAINE>/admin/` ne doit pas renvoyer 403 CSRF (vérification en section 9).

> ⚠️ `CSRF_TRUSTED_ORIGINS` exige le **schéma** (`https://`), contrairement à `ALLOWED_HOSTS` qui ne prend que le nom d'hôte. Une valeur sans `https://` est ignorée et le 403 CSRF persiste. Caddy transmet bien `X-Forwarded-Proto` par défaut, exploité par `SECURE_PROXY_SSL_HEADER`.

### 7.7. Alternative : Nginx + Certbot (sur l'hôte)

Si vous préférez ne pas conteneuriser le proxy, installez **Nginx + Certbot** directement sur l'hôte. Dans ce cas, le frontend et le backend doivent être **bindés sur `127.0.0.1`** (ex. `127.0.0.1:8080` pour le Nginx interne du frontend, `127.0.0.1:8000` pour gunicorn) afin que Nginx les atteigne en local sans les exposer publiquement.

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Vhost `/etc/nginx/sites-available/edututor` :

```nginx
server {
    listen 80;
    server_name <DOMAINE> www.<DOMAINE>;

    location ~ ^/(api|admin|static|media)/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/edututor /etc/nginx/sites-enabled/edututor
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d <DOMAINE> -d www.<DOMAINE> --redirect --agree-tos -m <USER>@<DOMAINE> --no-eff-email
sudo certbot renew --dry-run        # vérifie le renouvellement automatique (timer systemd)
```

> ⚠️ Avec l'alternative Nginx, c'est `X-Forwarded-Proto $scheme` qui permet à Django (via `SECURE_PROXY_SSL_HEADER`) de savoir qu'il est en HTTPS — comme avec Caddy. Ne combinez pas les deux proxys : choisissez **soit** Caddy en conteneur (recommandé, et retenu pour tout ce guide), **soit** Nginx+Certbot sur l'hôte, jamais les deux sur 80/443.

À l'issue de cette section : `<DOMAINE>` et `www.<DOMAINE>` pointent vers `<IP_VPS>` ; Caddy sert le frontend statique sur `/` et route `/api`, `/admin`, `/static` vers gunicorn (qui sert les statiques via WhiteNoise) ; le HTTPS Let's Encrypt est automatique ; CSRF/CORS/ALLOWED_HOSTS/SECURE_PROXY_SSL_HEADER sont alignés sur `https://<DOMAINE>`.

---

## 8. Stratégie LLM sur le VPS (cloud vs Ollama local)

Le Kit génère des QCM en appelant un moteur LLM. En développement, le moteur par défaut est **Ollama local** avec `llama3.1:8b`. Cette section explique pourquoi ce choix est **inadapté à un VPS OVH standard sans GPU** et comment basculer par défaut vers un **backend cloud à free tier** (Groq, Gemini, Mistral, Cerebras), qui rend l'application réellement utilisable en production.

### 8.1. Pourquoi Ollama local est rarement praticable sur un VPS OVH

Sur un VPS d'entrée/milieu de gamme (CPU uniquement, **pas de GPU**), faire tourner `llama3.1:8b` pose trois problèmes concrets :

| Contrainte | Réalité mesurée | Conséquence en production |
|---|---|---|
| **Disque** | Le modèle quantifié Q4 pèse **~4,7 Go** à télécharger | Occupe une grande part d'un petit disque VPS |
| **RAM** | Le modèle seul réclame **~5-6 Go** une fois chargé | Sur un VPS 2-4 Go RAM : tué par l'OOM-killer ou swap massif. Il faut **≥ 8 Go dédiables** (idéalement 16 Go avec Postgres + Django + frontend) |
| **CPU / latence** | **2 à 5 min par génération** de QCM en CPU pur ; d'où le réglage `OLLAMA_TIMEOUT=600` (10 min) | CPU à 100 % sur tous les cœurs pendant la génération → sature le VPS. Risque de **502/504** si le proxy ou gunicorn coupe avant la fin |

> ⚠️ Le port Ollama `11434` est exposé en dur sur l'hôte dans le `docker-compose.yml` de dev. L'API Ollama **n'a aucune authentification** : exposée sur Internet, n'importe qui peut l'utiliser et saturer votre CPU. En production, ce port ne doit JAMAIS être public — l'override de la section 6.5 le ferme (`ports: !reset []` + profil `ollama` non démarré).

> ⚠️ La génération est **synchrone** dans la requête HTTP (pas de file d'attente). Avec Ollama CPU (jusqu'à 600 s), une requête dépasse facilement le `--timeout` de gunicorn et du proxy → erreurs 502/504. **Limite structurelle :** avec `--workers 3`, le backend ne traite que **3 générations simultanées** ; pendant une génération Ollama de plusieurs minutes, un worker est monopolisé et les autres requêtes (même légères) attendent. Voir 8.6 pour l'asynchrone. Un backend cloud rapide rend ce problème quasi inexistant.

**Conclusion : par défaut, sur un VPS OVH sans GPU, utilisez un backend LLM cloud à free tier.** Ne lancez Ollama que si votre VPS est spécifiquement dimensionné pour (étape 8.6, et cas B de la section 1.2).

### 8.2. Tableau de décision : quel backend choisir ?

Le Kit câble déjà 9 backends via la variable `LLM_BACKEND`. Voici lesquels retenir en production :

| Priorité | Backend | `LLM_BACKEND` | Modèle par défaut | Pourquoi |
|---|---|---|---|---|
| **Vitesse maximale** | **Groq** | `groq` | `llama-3.3-70b-versatile` | LPU ultra-rapide, free tier généreux. Recommandé par défaut |
| Vitesse maximale (alt.) | Cerebras | `cerebras` | `llama-3.3-70b` | Wafer-scale, très rapide |
| **Conformité RGPD / souveraineté** | **Mistral** | `mistral` | `mistral-small-latest` | Fournisseur **européen**, données hébergées en UE |
| Repli gratuit sans CB | Gemini | `gemini` | `gemini-1.5-flash` | Google AI Studio, free tier sans carte bancaire |
| Souveraineté totale / hors-ligne | Ollama local | `ollama` | `llama3.1:8b` | **Uniquement** si VPS ≥ 8 Go RAM dédiables (étape 8.6) |
| CI / tests | mock | `mock` | — | Faux QCM déterministe instantané, jamais en prod publique |

> ⚠️ **Enjeu RGPD** : tout backend cloud envoie le contenu des cours hors de votre serveur. Le code journalise un avertissement à chaque appel cloud mais **ne bloque pas**. Si la confidentialité est critique, privilégiez **Mistral** (UE) ou Ollama local, et documentez le choix par un ADR.

### 8.3. Obtenir une clé API (exemple avec Groq, recommandé par défaut)

1. Créez un compte sur la console du fournisseur :
   - **Groq** : https://console.groq.com → *API Keys* → *Create API Key*. La clé commence par `gsk_...`.
   - **Gemini** : https://aistudio.google.com/apikey (aucune carte bancaire requise).
   - **Mistral** : https://console.mistral.ai → *API Keys*.
   - **Cerebras** : https://cloud.cerebras.ai → *API Keys*.
2. **Copiez la clé immédiatement** : la plupart des consoles ne la réaffichent qu'une seule fois.
3. Conservez-la hors du dépôt Git.

> ⚠️ Ne mettez **jamais** une vraie clé API dans `.env.example` ni dans aucun fichier versionné : le dépôt `IPSSI_APOCAL_KIT` est **public**. Toute clé committée doit être considérée comme compromise et révoquée (cf. le cas Brevo, section 4.6).

### 8.4. Renseigner la clé dans le `.env` de production

La clé se renseigne dans le `.env` de prod déjà créé (section 4.4). Pour mémoire, le bloc Groq :

```bash
LLM_BACKEND=groq
GROQ_API_KEY=gsk_votre_cle_reelle_ici
GROQ_MODEL=llama-3.3-70b-versatile
LLM_API_TIMEOUT=60
```

Variante **Mistral** (RGPD / UE) :

```bash
LLM_BACKEND=mistral
MISTRAL_API_KEY=votre_cle_mistral
MISTRAL_MODEL=mistral-small-latest
LLM_API_TIMEOUT=60
```

Le fichier reste en permissions `600` (section 4.5).

> ⚠️ La configuration LLM peut aussi être modifiée via l'**admin Django** (modèle `LLMConfig`), qui **écrase** la valeur du `.env`. Protégez impérativement l'admin (HTTPS, mot de passe fort, `DJANGO_DEBUG=False`) : un accès admin compromis permettrait de basculer le backend et d'exfiltrer le contenu des cours vers un cloud non désiré.

### 8.5. Ne PAS lancer le conteneur Ollama en production

Avec un backend cloud, le conteneur `ollama` est inutile : ne le démarrez pas (il consommerait RAM/disque et exposerait `11434`). L'override de la section 6.5 le place déjà derrière le profil `ollama` et neutralise son port. Un simple `docker compose ... up -d` **ne démarre donc pas** Ollama.

Vérifiez qu'il ne tourne pas et qu'aucun port LLM n'est exposé :

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
sudo ss -tlnp | grep 11434   # ne doit RIEN renvoyer
```

### 8.6. Si Ollama local est malgré tout exigé (souveraineté / hors-ligne)

Possible **à condition de dimensionner le VPS** (cas B, section 1.2 : ≥ 8 Go RAM dédiables, idéalement 16 Go) et d'accepter une génération lente.

**Choisir un modèle plus léger (fortement recommandé sur CPU)** et **aligner les timeouts** dans le `.env` :

```bash
LLM_BACKEND=ollama
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b      # ~2 Go ; ou phi3:mini (~2,3 Go)
OLLAMA_TIMEOUT=600
```

L'inférence CPU étant longue, gunicorn doit avoir un `--timeout` au moins égal à `OLLAMA_TIMEOUT` (sinon le worker est tué avant la fin). Adaptez la `command` du backend dans `docker-compose.prod.yml` :

```bash
gunicorn apocal.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 600
```

Le reverse proxy doit aussi tolérer cette durée. Augmentez le timeout du `reverse_proxy` Caddy pour le backend, par exemple :

```caddyfile
@backend path /api/* /admin/* /static/* /media/*
reverse_proxy @backend backend:8000 {
    transport http {
        read_timeout 600s
        write_timeout 600s
    }
}
```

Démarrez ensuite le conteneur via le profil `ollama` et téléchargez le modèle (le port `11434` reste fermé sur l'hôte ; on passe par `exec`) :

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile ollama up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec ollama ollama pull llama3.2:3b
```

> ⚠️ **Génération asynchrone (la vraie solution si Ollama est imposé).** Aligner les timeouts évite les 502/504 mais ne règle pas le fond : un worker gunicorn reste **bloqué plusieurs minutes** par génération, et avec 3 workers vous saturez à 3 requêtes simultanées (le reste fait la queue). La solution propre est de **sortir la génération de la requête HTTP** : la requête crée une tâche et renvoie immédiatement un identifiant ; un **worker dédié** (Celery ou RQ + Redis) exécute la génération en arrière-plan ; le frontend interroge l'état (polling). Procédure de principe :
> 1. Ajouter `celery` + `redis` (ou `rq`) à `requirements.txt`, et un broker `redis:7-alpine` dans `docker-compose.prod.yml` (port **non** exposé, réseau interne).
> 2. Déplacer l'appel LLM de la vue synchrone vers une **tâche** Celery/RQ.
> 3. Ajouter un service `worker` (même image backend prod, `command: celery -A apocal worker -l info`), avec sa propre `limits.memory`.
> 4. Exposer un endpoint d'état `GET /api/quizzes/jobs/<id>/` et faire poller le frontend.
>
> C'est un **chantier de développement**, pas une simple option de déploiement : à planifier en amont si la souveraineté impose Ollama. Avec un backend cloud rapide, l'asynchrone n'est pas nécessaire.

Le téléchargement du modèle persiste dans le volume `ollama-data` (sauvegarde en section 10.2).

**En résumé :** par défaut sur OVH sans GPU, **backend cloud free tier** (Groq pour la vitesse, Mistral pour le RGPD), clé dans le `.env` de prod à `chmod 600`, conteneur `ollama` non démarré et port `11434` jamais exposé.

---

## 9. Premier déploiement & vérifications

Cette section suppose tout ce qui précède en place : VPS durci, Docker installé, dépôt cloné dans `/home/<USER>/IPSSI_APOCAL_KIT`, `settings.py` adapté (WhiteNoise + durcissement), `.env` de prod rempli, Dockerfiles prod + `docker-compose.prod.yml` + `Caddyfile` créés, DNS de `<DOMAINE>` propagé vers `<IP_VPS>`. On exécute tout depuis la racine `Kit/`.

```bash
cd /home/<USER>/IPSSI_APOCAL_KIT/Kit
chmod 600 .env
ls -l .env
git status   # le .env de prod ne doit PAS être listé
```

> 💡 **Astuce : créez un alias** pour ne pas retaper les deux `-f` à chaque commande.
> ```bash
> echo "alias dcprod='docker compose -f docker-compose.yml -f docker-compose.prod.yml'" >> ~/.bashrc
> source ~/.bashrc
> ```
> Dans la suite, `dcprod` = `docker compose -f docker-compose.yml -f docker-compose.prod.yml`.

### 9.1. Build des images de production

Le frontend a besoin de l'URL d'API au moment du build (Vite fige `VITE_API_BASE_URL` dans le bundle) : assurez-vous qu'elle vaut bien `https://<DOMAINE>/api` dans `docker-compose.prod.yml` (section 6.5) **avant** de builder.

```bash
dcprod build
```

> ⚠️ Si vous changez `VITE_API_BASE_URL` plus tard, il faut **rebâtir** l'image frontend (`dcprod build --no-cache frontend`) : ce n'est pas un paramètre runtime. Un frontend qui appelle `http://localhost:8000/api` en production vient presque toujours d'un build fait avec la mauvaise valeur.

### 9.2. Vérifier la configuration fusionnée AVANT de démarrer

Confirmez que l'override a bien neutralisé le `command` de dev du frontend (sinon `npm run dev` relancerait Vite dans une image nginx et le conteneur planterait) et que les ports sont fermés :

```bash
# Le service frontend NE doit PAS afficher de command "npm run dev"
dcprod config | grep -A3 -E "frontend:" 

# Vérifie globalement qu'aucun mapping de port applicatif ne subsiste
dcprod config | grep -E "published|target" || echo "Aucun port publié hors Caddy : OK"
```

Après démarrage (étape 9.3), vous pourrez confirmer le CMD réel du conteneur frontend :

```bash
docker inspect -f '{{.Config.Cmd}}' apocalipssi-2026-frontend
# Attendu : [nginx -g daemon off;]  (et NON npm run dev)
```

### 9.3. Démarrage des services

```bash
dcprod up -d
```

L'ordre est géré par les dépendances : `migrate` (one-shot) s'exécute après que Postgres est `healthy`, puis `backend` démarre une fois `migrate` terminé avec succès, puis `frontend`, puis `caddy`. Par défaut, Ollama n'est **pas** démarré (profil `ollama`). Pour le lancer (uniquement si VPS ≥ 8 Go RAM — section 8.6) : `dcprod --profile ollama up -d --build`.

### 9.4. Attendre que les services soient en bonne santé

Surveillez jusqu'à voir `(healthy)` sur `apocalipssi-2026-postgres`, `apocalipssi-2026-backend` et `apocalipssi-2026-frontend`, et le service `migrate` en état `Exited (0)` :

```bash
dcprod ps
watch -n 3 'docker compose -f docker-compose.yml -f docker-compose.prod.yml ps'
```

> ⚠️ Au tout premier démarrage, Postgres initialise sa base : `migrate` attend `pg_isready`. C'est normal. Si `backend` reste en boucle de redémarrage (`Restarting` répété), passez aux logs (étape 9.9) — c'est en général un secret manquant ou un mot de passe Postgres incohérent entre `.env` et un volume existant. Si `migrate` finit en `Exited (1)`, lisez ses logs : `dcprod logs migrate`.

### 9.5. Vérifier les migrations Django

Les migrations sont jouées par le service one-shot `migrate`. **Confirmez-le** :

```bash
dcprod exec backend python manage.py showmigrations
```

Toutes les migrations doivent être cochées `[X]`. Si certaines sont en `[ ]`, relancez le one-shot : `dcprod up migrate` (il rejoue migrate + collectstatic puis s'arrête).

### 9.6. Vérifier la configuration de production de Django

```bash
dcprod exec backend python manage.py check --deploy
```

> ⚠️ **Objectif : zéro warning.** Grâce aux réglages de la section 5.2 (`DEBUG=False`, `SECRET_KEY` régénéré, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_PROXY_SSL_HEADER`), `check --deploy` ne doit plus remonter de warning de sécurité. S'il en reste, corrigez `settings.py`/`.env` puis `dcprod up -d --build backend` avant de communiquer l'URL. Aucun warning sur `DEBUG`, `SECRET_KEY`, HSTS ou cookies ne doit subsister.

### 9.7. Créer le compte administrateur (interactif)

```bash
dcprod exec backend python manage.py createsuperuser
```

> ⚠️ N'exécutez **PAS** `make seed` sur une instance de production réelle : il crée le compte public `test` / `motdepasse123`, connu et documenté. Si la base provient d'une instance dev déjà seedée, **vérifiez et supprimez** ce compte (section 4.7). Le seed est réservé aux instances de **démo jetables**, sur un domaine distinct.

### 9.8. (Démo uniquement) Jeu de données de démonstration

À ne lancer **que** si cette instance est une démo jetable, jamais la prod publique :

```bash
dcprod exec backend python manage.py seed
```

### 9.9. (Ollama uniquement) Télécharger le modèle LLM

Uniquement si vous avez choisi Ollama local (section 8.6). Avec un backend cloud, **sautez cette étape**.

```bash
dcprod --profile ollama exec ollama ollama pull llama3.2:3b   # ou llama3.1:8b si VPS ≥ 16 Go
```

> ⚠️ Le service `ollama` n'est plus exposé sur l'hôte, d'où le passage par `exec` (pas `curl localhost:11434`).

### 9.10. Où lire les logs

```bash
dcprod logs -f              # tous les services, flux continu
dcprod logs -f backend      # le plus utile au diagnostic
dcprod logs migrate         # diagnostic migrations / collectstatic
dcprod logs -f caddy        # diagnostic HTTPS / certificat
dcprod logs --tail 200 backend
```

> ⚠️ Un échec d'émission de certificat est presque toujours un problème de DNS pas encore propagé (`dig +short A <DOMAINE>`) ou de pare-feu (UFW doit laisser passer 80 et 443).

### 9.11. Smoke tests

**a. HTTPS et certificat valide**

```bash
curl -I https://<DOMAINE>            # attendu : HTTP/2 200
```

Une erreur de certificat (`curl: (60)`) signale un HTTPS non encore établi → logs Caddy (9.10).

**b. API derrière le proxy**

```bash
curl -I https://<DOMAINE>/api/docs/      # attendu : 200 (page HTML Swagger)
curl -s https://<DOMAINE>/api/llm/ping/  # JSON de statut confirmant le backend LLM actif
```

**c. Les fichiers statiques de l'admin/Swagger sont RÉELLEMENT servis (test décisif)**

Un `curl -I` sur `/api/docs/` peut renvoyer 200 alors que l'UI est **cassée** (CSS/JS en 404 si les statiques ne sont pas servis). Vérifiez donc explicitement qu'un asset statique de l'admin Django répond 200 — c'est le test qui valide l'activation de WhiteNoise (section 5.1) :

```bash
# L'asset CSS de base de l'admin Django doit répondre 200 (et non 404)
curl -s -o /dev/null -w "%{http_code}\n" https://<DOMAINE>/static/admin/css/base.css
# Attendu : 200
```

Si ce test renvoie **404**, le service des statiques n'est pas opérationnel : WhiteNoise n'est pas activé (middleware/`STORAGES` manquants, section 5.1) ou `collectstatic` n'a pas tourné (relancez `dcprod up migrate`).

**d. Vérification visuelle dans un navigateur (indispensable)**

`curl` ne suffit pas. Ouvrez dans un navigateur :
- `https://<DOMAINE>/admin/` → la page de login doit être **stylée** (logo Django, champs mis en forme), pas une page brute sans CSS. Connectez-vous : pas d'erreur **403 CSRF**.
- `https://<DOMAINE>/api/docs/` → Swagger UI doit s'afficher **avec son interface** (barre de recherche, endpoints dépliables), pas un écran blanc.

Une page non stylée = statiques en 404 → revoir 5.1 et le test (c).

**e. L'interface charge dans le navigateur**

Ouvrez `https://<DOMAINE>`. La SPA doit s'afficher, et un rechargement (F5) sur une route profonde (`/login`) ne doit **pas** renvoyer 404 (fallback SPA, section 6.4).

> ⚠️ Ouvrez la console du navigateur (F12 → Réseau). Si les appels API partent vers `http://localhost:8000` au lieu de `https://<DOMAINE>/api`, l'image frontend a été buildée avec la mauvaise `VITE_API_BASE_URL` → rebâtir (9.1). Des erreurs CORS/CSRF indiquent que `<DOMAINE>` manque dans `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` (sections 4.4 et 5.2).

**f. Inscription et email**

Créez un compte étudiant test depuis l'interface. Selon la configuration email :
- **Brevo réel** (clé régénérée renseignée) : l'email arrive dans la boîte (vérifiez aussi les spams). `DEFAULT_FROM_EMAIL` doit utiliser un expéditeur validé côté Brevo, et le lien doit pointer vers `https://<DOMAINE>` (variable `FRONTEND_URL`).
- **Console** (pas de clé SMTP) : aucun email envoyé, le contenu est écrit dans les logs : `dcprod logs --tail 100 backend`.

**g. Génération d'un quiz de bout en bout**

Toujours connecté, lancez une génération de quiz (le test le plus représentatif : frontend → backend → LLM), en surveillant `dcprod logs -f backend`. En cas de `502`/`504`, c'est un dépassement de timeout (Ollama CPU trop lent → bascule cloud, ou `gunicorn --timeout` trop court — sections 8.1 et 8.6).

### 9.12. Checklist de validation du déploiement

```text
[ ] .env de prod en permissions 600 et absent de Git
[ ] dcprod config : frontend SANS command "npm run dev"
[ ] migrate : Exited (0) ; postgres + backend + frontend en (healthy)
[ ] Aucun port applicatif exposé sur l'hôte — `ss -tlnp` ne montre que 22/80/443
[ ] showmigrations : toutes les migrations en [X]
[ ] check --deploy : ZÉRO warning (DEBUG=False, SECRET_KEY régénéré, cookies/HSTS OK)
[ ] Superuser admin créé avec mot de passe fort ; PAS de compte test/motdepasse123
[ ] make seed NON exécuté en prod réelle (et compte 'test' supprimé si migration depuis dev)
[ ] (Ollama only) modèle pull terminé ; sinon backend cloud configuré et ping OK
[ ] curl -I https://<DOMAINE> => 200, certificat HTTPS valide
[ ] https://<DOMAINE>/api/docs/ => 200
[ ] curl /static/admin/css/base.css => 200 (statiques RÉELLEMENT servis)
[ ] Navigateur : /admin/ et /api/docs/ STYLÉS (pas d'écran brut/blanc)
[ ] /api/llm/ping/ => statut OK avec le bon backend LLM
[ ] SPA charge ; F5 sur route profonde ne renvoie pas 404
[ ] Console navigateur : appels API vers https://<DOMAINE>/api (pas localhost), zéro erreur CORS/CSRF
[ ] Login admin sans 403 CSRF
[ ] Inscription : email reçu (Brevo réel) ou visible dans les logs (console)
[ ] Génération de quiz de bout en bout réussie (pas de 502/504)
```

> ⚠️ Dernier réflexe avant ouverture : depuis une machine **extérieure** au VPS, tentez `curl http://<IP_VPS>:5432`, `:8000`, `:3000`, `:11434`. Tous doivent échouer (connexion refusée / timeout). Si l'un répond, un mapping de port traîne dans votre Compose ou un bind `0.0.0.0` subsiste — corrigez avant d'ouvrir au public.

---

## 10. Exploitation : sauvegardes, mises à jour, supervision

Une fois EduTutor IA en production, il faut sauvegarder les données, appliquer les mises à jour sans casser le service, et surveiller que tout tourne.

> ⚠️ **Convention.** Projet cloné dans `/home/<USER>/IPSSI_APOCAL_KIT`, racine applicative dans `Kit/`, stack lancée avec `dcprod up -d` (alias défini en 9.0). Nom de projet Compose : `apocalipssi-2026` → conteneurs `apocalipssi-2026-postgres`, `apocalipssi-2026-backend`, `apocalipssi-2026-ollama`, etc. ; volumes nommés `apocalipssi-2026_postgres-data` et `apocalipssi-2026_ollama-data` (Docker préfixe les volumes avec le nom de projet).

> ℹ️ **Fuseau des tâches planifiées.** Comme `timedatectl` est réglé sur `Europe/Paris` (section 2.7), tous les horaires `cron` ci-dessous (03h00, 04h00, 04h30) sont en **heure locale française**, pas UTC.

### 10.1. Sauvegardes de la base PostgreSQL (avec chiffrement)

La base contient tout ce qui a de la valeur (comptes, cours importés, QCM générés, résultats) : c'est la sauvegarde prioritaire. Les dumps pouvant contenir des données métier sensibles, on les **chiffre au repos** avec `age` (chiffrement moderne, simple). Installez-le une fois : `sudo apt install -y age`, puis générez une paire de clés :

```bash
mkdir -p /home/<USER>/backups
age-keygen -o /home/<USER>/backups/age-key.txt   # affiche la clé PUBLIQUE (age1...) à noter
chmod 600 /home/<USER>/backups/age-key.txt
```

> ⚠️ **La clé privée `age-key.txt` est indispensable pour déchiffrer.** Conservez-en une copie **hors du VPS** (gestionnaire de mots de passe / coffre). Sans elle, vos sauvegardes chiffrées sont irrécupérables.

**Script de dump** `/home/<USER>/backups/backup-db.sh` :

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/<USER>/IPSSI_APOCAL_KIT/Kit"
BACKUP_DIR="/home/<USER>/backups/postgres"
CONTAINER="apocalipssi-2026-postgres"
RETENTION_DAYS=14
AGE_RECIPIENT="age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"   # clé PUBLIQUE age

mkdir -p "${BACKUP_DIR}"

# Charge POSTGRES_USER / POSTGRES_DB depuis le .env de prod (sans les exposer)
set -a
# shellcheck disable=SC1091
source "${PROJECT_DIR}/.env"
set +a

DB_USER="${POSTGRES_USER:-apocal}"
DB_NAME="${POSTGRES_DB:-apocal}"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
OUTFILE="${BACKUP_DIR}/${DB_NAME}_${STAMP}.sql.gz.age"

# Dump -> gzip -> chiffrement age, en flux (le clair ne touche jamais le disque)
docker exec -t "${CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists \
  | gzip \
  | age -r "${AGE_RECIPIENT}" > "${OUTFILE}"
echo "Dump chiffré créé : ${OUTFILE} ($(du -h "${OUTFILE}" | cut -f1))"

# Rotation : suppression des dumps de plus de RETENTION_DAYS jours
find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql.gz.age" -mtime +"${RETENTION_DAYS}" -delete
echo "Rotation effectuée (conservation : ${RETENTION_DAYS} jours)."
```

Préparez le dossier, rendez le script exécutable et testez-le :

```bash
mkdir -p /home/<USER>/backups/postgres
chmod +x /home/<USER>/backups/backup-db.sh
/home/<USER>/backups/backup-db.sh
ls -lh /home/<USER>/backups/postgres
```

**Planification via cron** (`crontab -e` de l'utilisateur `<USER>`, pas root ; heure locale `Europe/Paris`) :

```cron
# Sauvegarde quotidienne de la base EduTutor IA à 03h00 (heure de Paris)
0 3 * * * /home/<USER>/backups/backup-db.sh >> /home/<USER>/backups/backup-db.log 2>&1
```

> ⚠️ **`--clean --if-exists`** : le dump contient des `DROP` avant chaque `CREATE` (restauration idempotente), donc **restaurer ce dump écrase les données existantes** (section 10.7).

> ⚠️ **Une sauvegarde jamais restaurée n'est pas une sauvegarde.** Au moins une fois, faites un test de restauration complet (section 10.7) sur une base jetable — y compris l'étape de **déchiffrement** `age`, pour confirmer que vous avez bien la clé privée.

### 10.2. Sauvegarde des volumes Docker (Ollama, médias)

Le dump SQL ne couvre que PostgreSQL. À part la base, deux données vivent dans des volumes :

- **`apocalipssi-2026_ollama-data`** : les modèles LLM téléchargés. **À sauvegarder uniquement si vous faites tourner Ollama en local** (section 8.6) ; avec un backend cloud ce volume est inutile, le modèle se re-télécharge en une commande.
- **Médias / fichiers uploadés** : à date, le backend ne définit **pas** de `MEDIA_ROOT` (les PDF de cours sont traités en mémoire, pas stockés sur disque). Si une future version ajoute un stockage de médias, ce sera un volume à inclure ici.

Script `/home/<USER>/backups/backup-volumes.sh` (utile seulement si Ollama tourne) :

```bash
#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="/home/<USER>/backups/volumes"
RETENTION_DAYS=14
STAMP="$(date +%Y-%m-%d_%H%M%S)"
mkdir -p "${BACKUP_DIR}"

docker run --rm \
  -v apocalipssi-2026_ollama-data:/data:ro \
  -v "${BACKUP_DIR}":/backup \
  alpine:3.20 \
  tar czf "/backup/ollama-data_${STAMP}.tar.gz" -C /data .
echo "Volume ollama-data sauvegardé : ${BACKUP_DIR}/ollama-data_${STAMP}.tar.gz"

find "${BACKUP_DIR}" -name "ollama-data_*.tar.gz" -mtime +"${RETENTION_DAYS}" -delete
```

> ⚠️ **Sauvegarder un volume Postgres « à chaud » (en copiant `postgres-data`) est risqué** : la base peut être incohérente. Pour Postgres, fiez-vous au `pg_dump` de la section 10.1, **pas** à une copie du volume.

> 💡 Le volume `ollama-data` ne contient que des modèles publics re-téléchargeables : sa sauvegarde n'est qu'un gain de temps, pas une donnée critique (inutile de le chiffrer).

### 10.3. Copie hors-VPS (règle 3-2-1)

Une sauvegarde qui reste sur le VPS disparaît avec le VPS. Il faut une copie **ailleurs**. Les dumps étant **déjà chiffrés** par `age` (section 10.1), ils transitent et reposent chiffrés sur la machine distante — même si celle-ci est moins sécurisée. Depuis votre machine de sauvegarde (poste formateur, autre serveur, NAS), tirez les dumps via `rsync` :

```bash
rsync -avz --delete \
  <USER>@<IP_VPS>:/home/<USER>/backups/postgres/ \
  /chemin/local/backups-edututor/postgres/
```

Automatisez ce `rsync` **depuis la machine distante** (cron local), une heure après le dump du VPS :

```cron
# Rapatriement quotidien à 04h00 (sur la machine distante)
0 4 * * * rsync -avz --delete <USER>@<IP_VPS>:/home/<USER>/backups/postgres/ /chemin/local/backups-edututor/postgres/ >> /chemin/local/backups-edututor/rsync.log 2>&1
```

> ⚠️ **N'inversez pas le sens du `--delete`.** Ici la machine distante tire (`pull`) depuis le VPS. Ne lancez jamais un `rsync --delete` qui prendrait la copie locale comme source vers le VPS : vous effaceriez vos dumps serveur.

> ⚠️ **Le déchiffrement exige la clé privée `age`** (`age-key.txt`), qui ne doit **pas** être stockée à côté des dumps sur la machine distante. Gardez-la dans un coffre séparé. Test de bout en bout : `age -d -i age-key.txt fichier.sql.gz.age | gunzip | head`.

> 💡 **Alternative objet** : OVH propose un Object Storage (compatible S3). Vous pouvez pousser les dumps chiffrés avec `rclone` ou la CLI `aws --endpoint-url ...`, identifiants dans `~/.config/rclone/rclone.conf` en `600`.

### 10.4. Snapshots et Backup automatique OVH

En complément des sauvegardes applicatives, OVH protège au niveau de l'infrastructure (espace client) :

- **Snapshot manuel** : avant toute opération sensible (mise à jour majeure, migration de schéma), prenez un snapshot de l'instance (action dans le menu « … » de la fiche VPS). Il fige le disque à un instant T et permet un retour arrière rapide.
- **Backup automatique** : option payante de sauvegarde planifiée du VPS, à souscrire sur la fiche du VPS.

> ⚠️ Les libellés exacts des menus OVH changent : cherchez l'intention (« snapshot », « sauvegarde automatique »). **Le snapshot OVH ne remplace pas le `pg_dump`** : un snapshot pris pendant que Postgres écrit peut contenir une base incohérente. Le snapshot restaure **toute la machine** ; le `pg_dump` restaure **proprement les données**. Gardez les deux.

### 10.5. Mises à jour applicatives (redéploiement)

Les images de prod sont autosuffisantes (pas de bind mount du code) : un changement de code **exige un rebuild**, pas un simple redémarrage. Les migrations sont jouées par le service one-shot `migrate`, pas dans la boucle gunicorn.

```bash
# 1. Sauvegarde avant toute mise à jour (réflexe systématique)
/home/<USER>/backups/backup-db.sh

# 2. Récupérer la dernière version
cd /home/<USER>/IPSSI_APOCAL_KIT/Kit
git pull origin main

# 3. Reconstruire les images
dcprod build

# 4. Jouer les migrations + collectstatic via le service one-shot AVANT de basculer le backend
dcprod up migrate            # s'exécute puis s'arrête (Exited 0 attendu)

# 5. Redémarrer avec les nouvelles images
dcprod up -d

# 6. Contrôler la conformité prod, puis nettoyer les images obsolètes
dcprod exec backend python manage.py check --deploy
docker image prune -f
```

> ⚠️ **Si vous avez modifié `VITE_API_BASE_URL`**, elle est figée **au build** du frontend : l'étape 3 (`build`) la régénère, mais vérifiez que `build.args.VITE_API_BASE_URL` vaut bien `https://<DOMAINE>/api` dans `docker-compose.prod.yml`.

> ⚠️ **Ne lancez JAMAIS `make reset-db` ni `docker compose down -v` en production** : ces commandes suppriment les volumes, donc **détruisent la base**. Irréversible. **Migrations = point de non-retour potentiel** : c'est pourquoi l'étape 1 (dump) n'est pas optionnelle ; en cas de problème après `migrate`, votre seul recours propre est la restauration (section 10.7).

### 10.6. Mises à jour système et comportement au reboot

**Mises à jour de sécurité automatiques** (`unattended-upgrades`, installé en section 2.5) :

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
cat /etc/apt/apt.conf.d/50unattended-upgrades   # vérifier les sources de sécurité actives
```

(Optionnel) Redémarrage automatique si une mise à jour du noyau l'exige, à une heure creuse (**heure de Paris**, cf. section 2.7) — dans `/etc/apt/apt.conf.d/50unattended-upgrades` :

```conf
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:30";
```

**Redémarrage au boot.** Les services longue durée sont en `restart: unless-stopped` : un conteneur qui plante est relancé, et au reboot du VPS, Docker (service systemd) relance les conteneurs non arrêtés manuellement.

```bash
sudo systemctl enable docker
sudo systemctl is-enabled docker
docker inspect -f '{{.Name}} -> {{.HostConfig.RestartPolicy.Name}}' \
  apocalipssi-2026-backend apocalipssi-2026-frontend apocalipssi-2026-postgres
```

> ℹ️ Le service one-shot **`migrate`** est volontairement en `restart: "no"` : il ne doit **pas** être relancé au boot (il rejouerait migrate/collectstatic inutilement). Au reboot, c'est `backend` (en `unless-stopped`) qui remonte ; comme `migrate` a déjà appliqué les migrations dans la base persistée, le backend démarre directement. Si vous redéployez avec de nouvelles migrations, jouez `dcprod up migrate` manuellement (section 10.5).

Testez le comportement au reboot **une fois**, en heure creuse : `sudo reboot`, puis après reconnexion `dcprod ps` et `curl -I https://<DOMAINE>`.

> ⚠️ **Vérifiez que les conteneurs remontent seuls AVANT d'activer `Automatic-Reboot`**, sinon le service reste à terre après une mise à jour nocturne du noyau.

### 10.7. Procédure de restauration

À exécuter en cas de corruption, de migration ratée, ou de migration vers un nouveau VPS. La commande **source le `.env`** pour utiliser les vrais `POSTGRES_USER`/`POSTGRES_DB` (et non `apocal` codé en dur), et **déchiffre** d'abord le dump.

```bash
# 0. Charger les identifiants de la base depuis le .env de prod
cd /home/<USER>/IPSSI_APOCAL_KIT/Kit
set -a; source .env; set +a
DB_USER="${POSTGRES_USER:-apocal}"
DB_NAME="${POSTGRES_DB:-apocal}"

# 1. Identifier le dump à restaurer
ls -lh /home/<USER>/backups/postgres

# 2. Arrêter le backend/frontend (on garde Postgres up) pour figer les écritures
dcprod stop backend frontend

# 3. Déchiffrer (age) + décompresser + restaurer (--clean --if-exists : écrase l'état actuel)
DUMP="/home/<USER>/backups/postgres/${DB_NAME}_2026-06-15_030000.sql.gz.age"
age -d -i /home/<USER>/backups/age-key.txt "${DUMP}" \
  | gunzip \
  | docker exec -i apocalipssi-2026-postgres psql -U "${DB_USER}" -d "${DB_NAME}"

# 4. Relancer la stack et vérifier
dcprod up -d
dcprod ps
curl -I https://<DOMAINE>
```

Restauration du volume Ollama (seulement si sauvegardé et perdu), sinon re-téléchargez simplement le modèle :

```bash
docker run --rm \
  -v apocalipssi-2026_ollama-data:/data \
  -v /home/<USER>/backups/volumes:/backup:ro \
  alpine:3.20 \
  sh -c "cd /data && tar xzf /backup/ollama-data_<STAMP>.tar.gz"
# OU : dcprod --profile ollama exec ollama ollama pull llama3.2:3b
```

> ⚠️ **La restauration écrase les données actuelles.** Si vous n'êtes pas certain que la base courante est perdue, prenez d'abord un dump de l'état courant (`backup-db.sh`) avant de restaurer un ancien dump.

### 10.8. Supervision et journaux

Sur un VPS unique, une supervision simple suffit : logs, état des conteneurs, espace disque.

**10.8.1. Logs des conteneurs et rotation**

La rotation des logs Docker est **déjà en place** (section 3.5 : `/etc/docker/daemon.json`, plafond 3 × 10 Mo par conteneur). Pour consulter :

```bash
dcprod logs -f backend
dcprod logs --tail=200
```

Si vous n'aviez pas fait la section 3.5, faites-la maintenant (puis `sudo systemctl restart docker`, ce qui redémarre les conteneurs).

> ⚠️ **Sans rotation, un service bavard peut saturer le disque** et faire tomber tout le VPS (y compris Postgres).

**10.8.2. Journaux système et espace disque**

```bash
journalctl -u docker --since "1 hour ago"
journalctl -p err --since today
journalctl --disk-usage
sudo journalctl --vacuum-time=14d

df -h /
docker system df
free -h
docker stats --no-stream    # vérifie aussi que les limits.memory (section 6.7) sont honorées
```

**10.8.3. Check d'uptime simple (HTTP)** — `/home/<USER>/backups/healthcheck.sh` :

```bash
#!/usr/bin/env bash
URL="https://<DOMAINE>/health/"
STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "${URL}" || echo "000")"
if [ "${CODE}" != "200" ]; then
  echo "${STAMP} ALERTE: ${URL} a répondu ${CODE}" >> /home/<USER>/backups/healthcheck.log
fi
```

```cron
*/5 * * * * /home/<USER>/backups/healthcheck.sh
```

> ℹ️ La sonde vise `/health/` (toujours 200 si le backend tourne), pas `/api/llm/ping/` (qui peut renvoyer 503 selon l'état du LLM sans que le site soit en panne).

> 💡 Pour être alerté par e-mail/SMS sans rien installer, un service externe d'*uptime monitoring* (type UptimeRobot, gratuit) qui interroge `https://<DOMAINE>` toutes les 5 min suffit. Inutile de déployer Prometheus/Grafana sur un VPS d'entrée de gamme : cela consommerait la RAM dont Postgres et le backend ont besoin.

### 10.9. Renouvellement du certificat TLS

Avec **Caddy** (solution retenue), le renouvellement TLS est **entièrement automatique** : Caddy renouvelle les certificats Let's Encrypt avant expiration, sans cron. Rien à planifier.

```bash
dcprod logs caddy | grep -i "certificate"
echo | openssl s_client -servername <DOMAINE> -connect <DOMAINE>:443 2>/dev/null \
  | openssl x509 -noout -dates
```

> ⚠️ **Pour que Caddy renouvelle, les ports 80 et 443 doivent rester ouverts** (Let's Encrypt valide via le port 80). Si UFW bloque le 80, le renouvellement échoue silencieusement et le certificat expire. Gardez `80/tcp` et `443/tcp` autorisés (`sudo ufw status`).

> 💡 **Alternative Nginx + Certbot** (section 7.7) : le renouvellement passe par un timer systemd (`systemctl list-timers | grep certbot`), à vérifier avec `sudo certbot renew --dry-run`. C'est l'un des avantages de Caddy : zéro gestion TLS.

### Récapitulatif des tâches planifiées (heure de Paris)

| Quand | Quoi | Où |
|---|---|---|
| Quotidien 03h00 | Dump PostgreSQL **chiffré (age)** + rotation 14 j | cron `<USER>` sur le VPS |
| Quotidien 04h00 | `rsync` des dumps chiffrés hors-VPS | cron sur la machine distante |
| Toutes les 5 min | Sonde HTTP `healthcheck.sh` sur `/health/` | cron `<USER>` sur le VPS |
| Automatique | Mises à jour de sécurité système | `unattended-upgrades` |
| Automatique | Renouvellement TLS | Caddy (aucune action) |
| Avant chaque déploiement | Dump manuel + (option) snapshot OVH | Manuel |
| Ponctuel | Backup automatique / snapshot VPS | Espace client OVH |

---

## Checklist de mise en production

À cocher avant de communiquer l'URL aux étudiants.

**Serveur & réseau**
```text
[ ] VPS Ubuntu 24.04 commandé, dimensionné selon le backend LLM (cloud = 2-4 Go ; Ollama = ≥ 8 Go)
[ ] Console KVM/VNC repérée dans l'espace client OVH (filet de sécurité)
[ ] SSH par clé Ed25519 uniquement ; login root et mot de passe désactivés
[ ] Utilisateur <USER> sudo non-root ; jamais de travail quotidien en root
[ ] Système à jour ; unattended-upgrades activé
[ ] Fuseau Europe/Paris réglé (impacte les horaires cron)
[ ] Swap actif si RAM faible (swappiness=10)
[ ] fail2ban actif (jail sshd, backend systemd)
[ ] UFW : deny incoming ; seuls 22/80/443 ouverts
[ ] Vérif externe : 5432/8000/3000/11434 injoignables depuis Internet
```

**Docker & code**
```text
[ ] Docker Engine + Compose v2 (>= 2.24) installés depuis le dépôt officiel
[ ] <USER> dans le groupe docker ; docker run hello-world OK sans sudo
[ ] Rotation des logs Docker configurée (/etc/docker/daemon.json)
[ ] Dépôt cloné dans /home/<USER>/IPSSI_APOCAL_KIT (racine applicative Kit/)
[ ] settings.py : WhiteNoise activé (middleware + STORAGES)
[ ] settings.py : CSRF_TRUSTED_ORIGINS + cookies/HSTS/SECURE_PROXY_SSL_HEADER (pilotés par DEBUG=False)
[ ] gunicorn + whitenoise ajoutés à backend/requirements.txt
[ ] docker/backend.prod.Dockerfile (multi-stage, sans dev-deps) créé
[ ] docker-compose.prod.yml (migrate one-shot, healthcheck /health/, limits RAM), frontend.prod.Dockerfile, nginx.conf, .dockerignore créés
```

**Secrets & configuration**
```text
[ ] Ancienne clé SMTP Brevo RÉVOQUÉE côté Brevo
[ ] Historique Git scanné (gitleaks/trufflehog) ; clé purgée si dépôt sous contrôle
[ ] .env de prod en permissions 600, absent de Git
[ ] DJANGO_DEBUG=False ; DJANGO_SECRET_KEY aléatoire ; POSTGRES_PASSWORD fort
[ ] DJANGO_ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS / CORS_ALLOWED_ORIGINS = https://<DOMAINE>
[ ] FRONTEND_URL = https://<DOMAINE> (liens des emails)
[ ] VITE_API_BASE_URL = https://<DOMAINE>/api (figée au build)
[ ] BREVO_SMTP_KEY vide, ou nouvelle clé régénérée (jamais l'ancienne)
[ ] Aucun secret de démo résiduel (grep apocal-dev-only|change-me|dev-secret-key|DEBUG=True|xsmtpsib- => vide)
```

**Domaine, HTTPS & LLM**
```text
[ ] DNS A/AAAA de <DOMAINE> et www.<DOMAINE> pointent vers <IP_VPS> (dig OK)
[ ] Caddyfile créé ; Caddy seul à exposer 80/443
[ ] Certificat Let's Encrypt obtenu (logs caddy : certificate obtained) ; HTTP→HTTPS OK
[ ] HSTS activé côté Django UNIQUEMENT après validation du vrai certificat
[ ] LLM_BACKEND cloud (Groq/Mistral) configuré, clé en place ; Ollama NON démarré (sauf VPS dédié)
[ ] /api/llm/ping/ répond avec le bon backend
```

**Application & exploitation**
```text
[ ] migrate : Exited (0) ; tous les conteneurs longue durée (healthy)
[ ] check --deploy : ZÉRO warning (DEBUG, SECRET_KEY, cookies, HSTS tous traités)
[ ] /static/admin/css/base.css => 200 ; /admin/ et /api/docs/ STYLÉS dans le navigateur
[ ] Superuser admin créé (mot de passe fort) ; PAS de compte test/motdepasse123 (supprimé si migration dev)
[ ] SPA charge ; F5 sur route profonde ≠ 404 ; appels API vers https://<DOMAINE>/api ; login admin sans 403 CSRF
[ ] Inscription + génération de quiz de bout en bout réussies (pas de 502/504)
[ ] backup-db.sh testé (dump CHIFFRÉ age) + cron quotidien 03h00 ; rsync hors-VPS planifié
[ ] Clé privée age conservée HORS du VPS ; test de restauration (déchiffrement inclus) effectué une fois
[ ] healthcheck.sh planifié (sonde /health/) ou UptimeRobot externe configuré
```

---

## Pièges fréquents sur OVH (et ailleurs)

- **WhiteNoise installé mais pas activé = admin/Swagger cassés.** Ajouter `whitenoise` à `requirements.txt` ne sert à rien sans le **middleware** (`whitenoise.middleware.WhiteNoiseMiddleware`, après `SecurityMiddleware`) ET `STORAGES['staticfiles']`. Sans ça, avec `DEBUG=False`, `/static/*` renvoie 404 et les interfaces sont sans CSS. Test décisif : `curl /static/admin/css/base.css` doit répondre 200 (section 9.11.c).
- **Image backend restée en mode dev.** Réutiliser `docker/backend.Dockerfile` en prod embarque `requirements-dev.txt` + gcc. Utilisez `docker/backend.prod.Dockerfile` (multi-stage, slim, sans dev-deps), référencé dans `docker-compose.prod.yml`.
- **Healthcheck sur `/api/llm/ping/` = site mort avec Ollama.** Cet endpoint renvoie 503 si Ollama est injoignable/modèle non pull → backend `unhealthy` → Caddy ne démarre jamais. Utilisez `/health/` (toujours 200) pour le healthcheck conteneur.
- **`migrate` dans la command de gunicorn = migrations concurrentes au scale.** Extrayez migrate+collectstatic dans un service one-shot `migrate` (`restart: "no"`), dont le backend dépend via `service_completed_successfully`.
- **Docker contourne UFW.** Un port publié dans Compose (`5432:5432`) reste joignable depuis Internet même avec UFW « deny ». Parade : ne publier **aucun** port applicatif (`ports: !reset []`). Le repli `127.0.0.1:8000:8000` protège par le **bind loopback**, pas par UFW. Vérifiez toujours depuis une machine **externe** (section 9.12).
- **`PasswordAuthentication yes` ressuscité par cloud-init.** Sur les images cloud OVH, `/etc/ssh/sshd_config.d/50-cloud-init.conf` peut réactiver l'auth par mot de passe et primer sur votre `99-durcissement.conf` (la première directive l'emporte). Vérifiez avec `grep -R PasswordAuthentication /etc/ssh/sshd_config.d/`.
- **fail2ban qui ne bannit rien sur Ubuntu 24.04.** Les logs SSH sont dans journald, pas dans `/var/log/auth.log` : sans `backend = systemd` dans `jail.local`, la jail `sshd` ne surveille rien.
- **Verrouillage SSH après UFW.** Autorisez toujours le 22 **avant** `ufw enable`. Si vous êtes dehors, la **console KVM/VNC** OVH (section 1.5) est le seul recours — entrée clavier souvent en QWERTY.
- **Let's Encrypt qui échoue.** DNS pas encore propagé, port 80 fermé, ou redirection web du registrar sur la racine. Utilisez le **staging** pendant les tests. `caddy-data` doit persister pour ne pas redemander un certificat à chaque redémarrage.
- **HSTS posé trop tôt.** Activer `SECURE_HSTS_SECONDS` sous staging (certificat non reconnu) « épingle » le domaine en HTTPS et rend l'accès pénible. N'activez HSTS qu'après un vrai certificat de production valide. Et ne le posez pas en double (Caddy ET Django) : une seule source.
- **`VITE_API_BASE_URL` figée au build.** Le frontend appelle `localhost:8000` en prod = build fait avec la mauvaise valeur. Ce n'est pas un paramètre runtime : rebâtir l'image (`build --no-cache frontend`).
- **403 CSRF sur l'admin derrière le proxy.** `CSRF_TRUSTED_ORIGINS` exige le schéma `https://` et doit être **lu dans `settings.py`** (ajout section 5.2). Sans `SECURE_PROXY_SSL_HEADER`, Django se croit en HTTP et casse cookies/redirections.
- **Ollama sur CPU OVH = 502/504 et workers bloqués.** 2 à 5 min par QCM, CPU saturé, 3 workers max simultanés. Par défaut : backend cloud. Si Ollama imposé : VPS ≥ 8 Go RAM, modèle léger, timeouts alignés (gunicorn/proxy), et idéalement génération **asynchrone** (Celery/RQ, section 8.6).
- **Conteneur non borné = OOM global.** Sans `deploy.resources.limits`, un conteneur (Ollama, fuite) peut faire tuer Postgres par l'OOM-killer. Plafonnez la RAM par service (section 6.7) ; le swap seul ne suffit pas.
- **Dumps en clair rapatriés hors-VPS.** Les dumps contiennent des données métier : chiffrez-les (`age`) avant le `rsync`, et gardez la clé privée hors du VPS et hors de la machine distante.
- **`docker compose down -v` = base détruite.** Le `-v` supprime les volumes nommés (`postgres-data`, `caddy-data`). Ne jamais l'utiliser en prod ; `make reset-db` est un outil de dev purement destructif (`down -v` + `seed`).
- **Snapshot OVH pris pour une sauvegarde de base.** Un snapshot disque à chaud peut contenir une base Postgres incohérente. Le `pg_dump` reste la référence pour les données ; le snapshot, pour la machine entière.
- **Compte de démo en prod.** `make seed` crée `test` / `motdepasse123`, public et documenté. Jamais sur l'instance ouverte aux étudiants ; et s'il provient d'une base dev migrée, **supprimez-le** (section 4.7).
- **Cron en UTC au lieu de l'heure locale.** Sans `timedatectl set-timezone Europe/Paris` (section 2.7), les horaires de sauvegarde/reboot tournent en UTC. Réglez le fuseau et gardez à l'esprit que cron, les timers et `unattended-upgrades` le suivent.

---

Fichiers du dépôt vérifiés pour cette version (chemins relatifs à la racine applicative `Kit/`) :
- `docker/backend.Dockerfile` (dev) — confirme `pip install -r requirements.txt -r requirements-dev.txt`, `gcc`+`libpq-dev`, `runserver`, base `python:3.11-slim`.
- `backend/apocal/settings.py` — confirme l'absence de WhiteNoise, `CSRF_TRUSTED_ORIGINS`, cookies/HSTS, `SECURE_PROXY_SSL_HEADER` ; `STATIC_ROOT = BASE_DIR / "staticfiles"`.
- `backend/apocal/urls.py` — `/health/` renvoie toujours 200 ; `/api/docs/` = Swagger.
- `backend/llm/views.py` — `PingView` renvoie `HTTP_503_SERVICE_UNAVAILABLE` quand Ollama est injoignable.
- `docker-compose.yml` — `name: apocalipssi-2026`, ports `5432/11434/8000/3000` exposés, bind mounts, `ollama:latest`.
- `Makefile` — `reset-db` = `down -v` + `seed` ; `seed` crée `test`/`motdepasse123` (confirmé dans la commande `seed`).
- `frontend/package.json` — `build` = `tsc -b && vite build`.