# Guide : Mode Démo vs Déploiement Réel

## 📺 Mode Démo (Par défaut)

**Caractéristiques :**
- ⚡ Ultra rapide (2-3 secondes)
- 🎭 Simule tous les déploiements
- ✅ Parfait pour tester l'orchestration
- 📝 Génère la structure Terraform
- 💡 Idéal pour comprendre le système

**Utilisation :**
```bash
# CLI
python main.py create -p k3s -n 3

# Interactif (choisir option 1 "Démo rapide")
python main.py interactive
```

**Ce qui est simulé :**
- Installation K3s → Simple echo
- Déploiement Prometheus/Grafana → Logs simulés
- Validation cluster → Données fictives (toujours 100/100)

---

## 🚀 Mode Déploiement Réel

**Caractéristiques :**
- ⏱️ Plus lent (2-5 minutes)
- 🔧 Installe vraiment K3s sur votre machine
- 📊 Déploie vraiment Prometheus/Grafana
- ✅ Validations avec de vraies métriques
- 🎯 Production-ready

**Prérequis :**
```bash
# Vérifier les prérequis
which curl     # Doit être installé
which kubectl  # Doit être installé
sudo -v        # Doit avoir accès sudo

# Espace disque
df -h /var     # Minimum 2GB libre
```

**⚠️ Important :**
- Nécessite **accès sudo** pour installer K3s
- Télécharge ~500MB de données
- Modifie votre système (installe K3s)
- Port 6443 doit être disponible

**Utilisation :**

### Option 1 : CLI avec flag
```bash
# Mode réel avec flag --real ou --real-deployment
python main.py create -p k3s -n 1 --real-deployment

# Exemple complet
python main.py create \\
  --platform k3s \\
  --nodes 1 \\
  --monitoring \\
  --real-deployment
```

### Option 2 : Mode interactif
```bash
python main.py interactive

# Puis choisir :
# - Platform : K3s
# - Environment : development
# - Nodes : 1 (recommandé pour premier test)
# - Monitoring : Oui
# - Mode : 2. 🚀 Déploiement réel (installe vraiment K3s) 👈
```

**Ce qui sera installé en mode réel :**

1. **K3s Server** (Control Plane)
   ```bash
   curl -sfL https://get.k3s.io | sh -s -
   ```
   - Installe K3s dans `/usr/local/bin/`
   - Crée le service systemd
   - Configure kubeconfig dans `/etc/rancher/k3s/k3s.yaml`

2. **Prometheus Operator**
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/...
   ```
   - Namespace `monitoring`
   - ServiceMonitors, PodMonitors
   - Alertmanager

3. **Grafana**
   ```bash
   kubectl apply -f output/.../monitoring/grafana.yaml
   ```
   - Déploiement Grafana
   - Service LoadBalancer
   - Dashboards pré-configurés

4. **Validation**
   - Vraies requêtes kubectl
   - Score basé sur métriques réelles
   - Tests de connectivité

---

## 📊 Comparaison

| Aspect | Mode Démo | Mode Réel |
|--------|-----------|-----------|
| **Durée** | 2-3s | 2-5 min |
| **Sudo requis** | ❌ Non | ✅ Oui |
| **Installe K3s** | ❌ Non | ✅ Oui |
| **Téléchargements** | ~0 MB | ~500 MB |
| **Validations** | Fictives | Réelles |
| **Kubeconfig** | Simulé | Fonctionnel |
| **Monitoring** | Simulé | Opérationnel |

---

## 🧪 Test Rapide du Mode Réel

### Test 1 : Vérifier que tout fonctionne
```bash
# 1. Test démo (rapide)
python main.py create -p k3s -n 1 --no-monitoring

# 2. Test réel (patience!)
python main.py create -p k3s -n 1 --no-monitoring --real
```

### Après le déploiement réel :
```bash
# Vérifier K3s
sudo systemctl status k3s
kubectl cluster-info

# Voir les nodes
kubectl get nodes

# Voir les pods
kubectl get pods --all-namespaces

# Utiliser le kubeconfig généré
export KUBECONFIG=$(ls -t output/kubeconfigs/*.kubeconfig | head -1)
kubectl get nodes
```

### Test 2 : Avec monitoring complet
```bash
python main.py create \\
  --platform k3s \\
  --nodes 1 \\
  --monitoring \\
  --real-deployment

# Après déploiement, accéder à :
# - Grafana : http://localhost:3000
# - Prometheus : http://localhost:9090
```

---

## 🧹 Nettoyage après test réel

```bash
# Désinstaller K3s complètement
sudo /usr/local/bin/k3s-uninstall.sh

# Nettoyer les fichiers générés
rm -rf output/terraform/*
rm -rf output/kubeconfigs/*
rm -rf output/docs/*
```

---

## 🐛 Dépannage

### Erreur : "K3s installation failed"
```bash
# Vérifier les logs
sudo journalctl -u k3s -n 50

# Vérifier l'espace disque
df -h

# Nettoyer et réessayer
sudo /usr/local/bin/k3s-uninstall.sh
python main.py create -p k3s -n 1 --real
```

### Erreur : "Port 6443 already in use"
```bash
# Un autre K3s/K8s tourne déjà
sudo systemctl stop k3s
# ou
sudo /usr/local/bin/k3s-uninstall.sh
```

### Timeout pendant le déploiement
```bash
# Le téléchargement peut être lent
# Augmenter le timeout ou vérifier la connexion
curl -I https://get.k3s.io
```

---

## 💡 Recommandations

**Pour apprendre l'architecture :**
→ Utilisez le **mode démo** (rapide, sans risque)

**Pour tester localement :**
→ Utilisez le **mode réel avec --no-monitoring** d'abord  
→ Puis ajoutez `--monitoring` ensuite

**Pour production :**
→ Utilisez EKS/AKS avec le mode réel
→ Configurez les alertes et backups

---

## 📚 Prochaines Étapes

1. **Tester en démo** : `python main.py interactive` (option 1)
2. **Tester en réel** : `python main.py create -p k3s -n 1 --real`
3. **Explorer la doc générée** : `cat output/docs/*/README.md`
4. **Personnaliser** : Modifier `examples/k3s-local.yaml`

Bon déploiement ! 🚀
