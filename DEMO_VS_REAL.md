# Guide: Demo Mode vs Real Deployment

## 📺 Demo Mode (Default)

**Characteristics:**
- ⚡ Ultra fast (2-3 seconds)
- 🎭 Simulates all deployments
- ✅ Perfect for testing orchestration
- 📝 Generates Terraform structure
- 💡 Ideal for understanding the system

**Usage:**
```bash
# CLI
python main.py create -p k3s -n 3

# Interactive (choose option 1 "Quick demo")
python main.py interactive
```

**What is simulated:**
- K3s installation → Simple echo
- Prometheus/Grafana deployment → Simulated logs
- Cluster validation → Fake data (always 100/100)

---

## 🚀 Real Deployment Mode

**Characteristics:**
- ⏱️ Slower (2-5 minutes)
- 🔧 Actually installs K3s on your machine
- 📊 Actually deploys Prometheus/Grafana
- ✅ Validations with real metrics
- 🎯 Production-ready

**Prerequisites:**
```bash
# Check prerequisites
which curl     # Must be installed
which kubectl  # Must be installed
sudo -v        # Must have sudo access

# Disk space
df -h /var     # Minimum 2GB free
```

**⚠️ Important:**
- Requires **sudo access** to install K3s
- Downloads ~500MB of data
- Modifies your system (installs K3s)
- Port 6443 must be available

**Usage:**

### Option 1: CLI with flag
```bash
# Real mode with --real or --real-deployment flag
python main.py create -p k3s -n 1 --real-deployment

# Complete example
python main.py create \
  --platform k3s \
  --nodes 1 \
  --monitoring \
  --real-deployment
```

### Option 2: Interactive mode
```bash
python main.py interactive

# Then choose:
# - Platform: K3s
# - Environment: development
# - Nodes: 1 (recommended for first test)
# - Monitoring: Yes
# - Mode: 2. 🚀 Real deployment (actually installs K3s) 👈
```

**What will be installed in real mode:**

1. **K3s Server** (Control Plane)
   ```bash
   curl -sfL https://get.k3s.io | sh -s -
   ```
   - Installs K3s in `/usr/local/bin/`
   - Creates systemd service
   - Configures kubeconfig in `/etc/rancher/k3s/k3s.yaml`

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
   - Grafana deployment
   - LoadBalancer service
   - Pre-configured dashboards

4. **Validation**
   - Real kubectl requests
   - Score based on real metrics
   - Connectivity tests

---

## 📊 Comparison

| Aspect | Demo Mode | Real Mode |
|--------|-----------|-----------|
| **Duration** | 2-3s | 2-5 min |
| **Sudo required** | ❌ No | ✅ Yes |
| **Installs K3s** | ❌ No | ✅ Yes |
| **Downloads** | ~0 MB | ~500 MB |
| **Validations** | Fake | Real |
| **Kubeconfig** | Simulated | Functional |
| **Monitoring** | Simulated | Operational |

---

## 🧪 Quick Real Mode Test

### Test 1: Verify everything works
```bash
# 1. Demo test (quick)
python main.py create -p k3s -n 1 --no-monitoring

# 2. Real test (patience!)
python main.py create -p k3s -n 1 --no-monitoring --real
```

### After real deployment:
```bash
# Check K3s
sudo systemctl status k3s
kubectl cluster-info

# See nodes
kubectl get nodes

# See pods
kubectl get pods --all-namespaces

# Use generated kubeconfig
export KUBECONFIG=$(ls -t output/kubeconfigs/*.kubeconfig | head -1)
kubectl get nodes
```

### Test 2: With complete monitoring
```bash
python main.py create \
  --platform k3s \
  --nodes 1 \
  --monitoring \
  --real-deployment

# After deployment, access:
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

---

## 🧹 Cleanup after real test

```bash
# Completely uninstall K3s
sudo /usr/local/bin/k3s-uninstall.sh

# Clean generated files
rm -rf output/terraform/*
rm -rf output/kubeconfigs/*
rm -rf output/docs/*
```

---

## 🐛 Troubleshooting

### Error: "K3s installation failed"
```bash
# Check logs
sudo journalctl -u k3s -n 50

# Check disk space
df -h

# Clean and retry
sudo /usr/local/bin/k3s-uninstall.sh
python main.py create -p k3s -n 1 --real
```

### Error: "Port 6443 already in use"
```bash
# Another K3s/K8s is already running
sudo systemctl stop k3s
# or
sudo /usr/local/bin/k3s-uninstall.sh
```

### Timeout during deployment
```bash
# Download can be slow
# Increase timeout or check connection
curl -I https://get.k3s.io
```

---

## 💡 Recommendations

**To learn the architecture:**
→ Use **demo mode** (fast, risk-free)

**To test locally:**
→ Use **real mode with --no-monitoring** first  
→ Then add `--monitoring` afterwards

**For production:**
→ Use EKS/AKS with real mode
→ Configure alerts and backups

---

## 📚 Next Steps

1. **Test in demo**: `python main.py interactive` (option 1)
2. **Test in real**: `python main.py create -p k3s -n 1 --real`
3. **Explore generated docs**: `cat output/docs/*/README.md`
4. **Customize**: Modify `examples/k3s-local.yaml`

Happy deploying! 🚀
