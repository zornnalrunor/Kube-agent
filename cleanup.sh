#!/bin/bash

###############################################################################
# Cleanup Script - Terraform Agent EKS/AKS
# Supprime K3s, fichiers générés, et réinitialise l'environnement
###############################################################################

set -e

echo "🧹 Nettoyage du système..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running with necessary privileges
if [[ $EUID -ne 0 ]] && ! sudo -n true 2>/dev/null; then
    print_warning "Ce script nécessite sudo pour désinstaller K3s"
    echo "Vous serez invité à entrer votre mot de passe si nécessaire"
fi

# Ask for confirmation
echo "Ce script va:"
echo "  • Désinstaller K3s (si installé)"
echo "  • Supprimer les namespaces monitoring"
echo "  • Nettoyer les fichiers générés (output/, data/)"
echo "  • Nettoyer les fichiers Terraform"
echo ""
read -p "Continuer? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Annulé par l'utilisateur"
    exit 0
fi

echo ""

###############################################################################
# 1. Nettoyer les namespaces Kubernetes AVANT de désinstaller K3s
###############################################################################

if command -v kubectl &> /dev/null && command -v k3s &> /dev/null; then
    echo "🧹 Nettoyage des namespaces Kubernetes..."
    
    # Utiliser le kubeconfig de K3s directement
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
    
    # Supprimer le namespace monitoring
    if sudo kubectl get namespace monitoring &>/dev/null; then
        echo "  Suppression du namespace 'monitoring'..."
        sudo kubectl delete namespace monitoring --timeout=30s 2>/dev/null || true
        print_status "Namespace 'monitoring' supprimé"
    else
        print_status "Namespace 'monitoring' n'existe pas"
    fi
    
    # Supprimer le namespace argocd
    if sudo kubectl get namespace argocd &>/dev/null; then
        echo "  Suppression du namespace 'argocd'..."
        sudo kubectl delete namespace argocd --timeout=30s 2>/dev/null || true
        print_status "Namespace 'argocd' supprimé"
    else
        print_status "Namespace 'argocd' n'existe pas"
    fi
else
    print_status "K3s n'est pas installé ou kubectl non disponible"
fi

echo ""

###############################################################################
# 2. Désinstaller K3s
###############################################################################

if command -v k3s &> /dev/null; then
    echo "🗑️  Désinstallation de K3s..."
    
    if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
        sudo /usr/local/bin/k3s-uninstall.sh
        print_status "K3s désinstallé"
    else
        print_warning "Script de désinstallation K3s non trouvé"
    fi
else
    print_status "K3s n'est pas installé"
fi

echo ""

###############################################################################
# 3. Nettoyer les fichiers générés
###############################################################################

echo "🧹 Nettoyage des fichiers générés..."

# Output directory
if [ -d "output" ]; then
    echo "  Suppression de output/..."
    rm -rf output/terraform/*
    rm -rf output/kubeconfigs/*
    rm -rf output/docs/*
    rm -rf output/manifests/*
    rm -rf output/gitops/*
    rm -rf output/argocd-apps/*
    print_status "Fichiers output/ nettoyés"
fi

# Nettoyer les contextes k3s de ~/.kube/config
if [ -f "$HOME/.kube/config" ]; then
    echo "  Nettoyage des contextes k3s dans ~/.kube/config..."
    # Sauvegarder
    cp "$HOME/.kube/config" "$HOME/.kube/config.backup.$(date +%s)"
    
    # Supprimer les contextes k3s-* avec kubectl
    if command -v kubectl &> /dev/null; then
        # Afficher les contextes k3s avant nettoyage
        k3s_contexts=$(kubectl config get-contexts -o name 2>/dev/null | grep "^k3s-" || true)
        if [ -n "$k3s_contexts" ]; then
            echo "    Contextes k3s trouvés:"
            echo "$k3s_contexts" | sed 's/^/      • /'
            
            # Supprimer chaque contexte k3s
            for ctx in $k3s_contexts; do
                echo "      Suppression: $ctx"
                kubectl config delete-context "$ctx" &>/dev/null || true
                # Supprimer aussi les clusters et users associés
                kubectl config delete-cluster "$ctx" &>/dev/null || true
                kubectl config delete-user "$ctx" &>/dev/null || true
                # Variantes possibles de nommage
                kubectl config delete-cluster "k3s-cluster-${ctx#k3s-}" &>/dev/null || true
                kubectl config delete-user "k3s-user-${ctx#k3s-}" &>/dev/null || true
            done
            print_status "$(echo "$k3s_contexts" | wc -l) contexte(s) k3s nettoyé(s)"
        else
            print_status "Aucun contexte k3s trouvé"
        fi
    fi
    
    # Nettoyage agressif: supprimer toutes les entrées contenant 'k3s' dans le kubeconfig
    if command -v yq &> /dev/null; then
        echo "    Nettoyage avancé avec yq..."
        yq eval 'del(.clusters[] | select(.name | test("k3s")))' -i "$HOME/.kube/config" 2>/dev/null || true
        yq eval 'del(.users[] | select(.name | test("k3s")))' -i "$HOME/.kube/config" 2>/dev/null || true
        yq eval 'del(.contexts[] | select(.name | test("k3s")))' -i "$HOME/.kube/config" 2>/dev/null || true
        print_status "Nettoyage avancé effectué"
    fi
fi

# Data directory (SQLite, logs)
if [ -d "data" ]; then
    echo "  Suppression de data/..."
    rm -rf data/state.db
    rm -rf data/*.log
    print_status "Fichiers data/ nettoyés"
fi

# Logs
if [ -d "logs" ]; then
    echo "  Suppression de logs/..."
    rm -rf logs/*
    print_status "Logs nettoyés"
fi

echo ""

###############################################################################
# 4. Nettoyer les états Terraform (si présents)
###############################################################################

echo "🧹 Nettoyage des états Terraform..."

find . -type f -name "terraform.tfstate*" -delete 2>/dev/null || true
find . -type d -name ".terraform" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name ".terraform.lock.hcl" -delete 2>/dev/null || true

print_status "États Terraform nettoyés"

echo ""

###############################################################################
# 5. Nettoyer les fichiers temporaires
###############################################################################

echo "🧹 Nettoyage des fichiers temporaires..."

# Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# pytest cache
rm -rf .pytest_cache 2>/dev/null || true

print_status "Cache Python nettoyé"

echo ""

###############################################################################
# Résumé
###############################################################################

echo ""
echo "✅ Nettoyage terminé!"
echo ""
echo "Le système est maintenant dans un état propre."
echo "Vous pouvez relancer un déploiement avec:"
echo "  python main.py interactive"
echo ""
