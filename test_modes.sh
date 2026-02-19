#!/bin/bash
# Script de test des deux modes : démo vs réel

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║        Test des modes Démo vs Réel                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier l'environnement virtuel
if [[ ! -d "venv" ]]; then
    echo -e "${YELLOW}⚠️  Environnement virtuel non trouvé${NC}"
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

echo -e "${GREEN}✅ Environnement virtuel activé${NC}"
echo ""

# Menu
echo "Que voulez-vous tester ?"
echo ""
echo "  1. 📺 Mode DÉMO (rapide, simulation)"
echo "  2. 🚀 Mode RÉEL (installe K3s sur votre machine)"
echo "  3. 🔍 Comparer les deux (démo puis réel)"
echo "  4. 🧪 Test rapide CLI"
echo ""

read -p "Votre choix [1-4]: " choice

case $choice in
    1)
        echo ""
        echo -e "${YELLOW}🎬 Lancement du mode DÉMO...${NC}"
        echo ""
        python main.py create --platform k3s --nodes 1 --no-monitoring
        ;;
        
    2)
        echo ""
        echo -e "${RED}⚠️  ATTENTION : Mode RÉEL${NC}"
        echo ""
        echo "Ce mode va :"
        echo "  • Installer K3s sur votre machine"
        echo "  • Nécessiter l'accès sudo"
        echo "  • Télécharger ~500MB"
        echo "  • Prendre 2-5 minutes"
        echo ""
        read -p "Continuer? [y/N]: " confirm
        
        if [[ $confirm == [yY] ]]; then
            echo ""
            echo -e "${GREEN}🚀 Lancement du mode RÉEL...${NC}"
            echo ""
            python main.py create --platform k3s --nodes 1 --no-monitoring --real-deployment
            
            echo ""
            echo -e "${GREEN}✅ Déploiement terminé!${NC}"
            echo ""
            echo "Vérifications :"
            echo ""
            
            if command -v kubectl &> /dev/null; then
                echo "📊 Nodes:"
                kubectl get nodes
                echo ""
                echo "🔍 Pods système:"
                kubectl get pods -n kube-system
            else
                echo -e "${YELLOW}kubectl non trouvé, impossible de vérifier${NC}"
            fi
        else
            echo "Annulé."
        fi
        ;;
        
    3)
        echo ""
        echo -e "${YELLOW}🔬 Test comparatif${NC}"
        echo ""
        
        echo "═══════════════════════════════════════"
        echo "📺 TEST 1: Mode DÉMO"
        echo "═══════════════════════════════════════"
        time python main.py create --platform k3s --nodes 1 --no-monitoring
        
        echo ""
        echo ""
        echo "═══════════════════════════════════════"
        echo "🚀 TEST 2: Mode RÉEL"
        echo "═══════════════════════════════════════"
        
        read -p "Continuer avec le mode réel? [y/N]: " confirm
        if [[ $confirm == [yY] ]]; then
            time python main.py create --platform k3s --nodes 1 --no-monitoring --real-deployment
        else
            echo "Test réel annulé."
        fi
        ;;
        
    4)
        echo ""
        echo -e "${YELLOW}🧪 Tests CLI rapides${NC}"
        echo ""
        
        echo "1️⃣ Help command:"
        python main.py --help
        echo ""
        
        echo "2️⃣ Version:"
        python main.py version
        echo ""
        
        echo "3️⃣ Create help:"
        python main.py create --help
        echo ""
        
        echo "4️⃣ Test démo rapide (1 node, no monitoring):"
        python main.py create -p k3s -n 1 --no-monitoring
        ;;
        
    *)
        echo "Choix invalide."
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Test terminé!${NC}"
echo ""
echo "📚 Documentation :"
echo "  • DEMO_VS_REAL.md - Guide complet des deux modes"
echo "  • docs/QUICKSTART.md - Guide de démarrage"
echo "  • docs/ARCHITECTURE.md - Architecture du système"
echo ""
