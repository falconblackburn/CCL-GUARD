# Multi-Customer Scaling Guide (Enterprise Edition)

This guide provides the architectural blueprint for deploying CCL Guard across multiple customers, maintaining security isolation, and managing global WhatsApp notifications.

## 1. Single-Instance vs. Multi-Tenant
For maximum data isolation, we recommend the **Isolated Instance Model**:
- **Each Customer**: One VPS (e.g., AWS EC2, DigitalOcean Droplet) + One Cloudflare Tunnel.
- **Benefits**: No data leakage between customers, localized AI processing (Ollama per customer), and custom security policies.

## 2. Managing WhatsApp at Scale
To manage alerts for many customers using one Twilio account:

### A. Customer-Specific Messaging Services
In the Twilio Console, create a **Messaging Service** for each customer. This allows you to:
- Assign different WhatsApp numbers (or use the same Sandbox for testing).
- Track usage and logs per customer.

### B. Dynamic Webhook Routing
Each customer instance will have its own Cloudflare Tunnel URL.
- **Customer A**: `https://soc-a.yourdomain.com/api/whatsapp/webhook`
- **Customer B**: `https://soc-b.yourdomain.com/api/whatsapp/webhook`

Update each customer's `.env` with their specific `TWILIO_WHATSAPP_ID` and the `ADMIN_WHATSAPP` number for their personnel.

## 3. Automated Fleet Management
For deploying 10+ customers, use the provided `deploy_production.sh` script in conjunction with a configuration management tool like **Ansible**:

```yaml
# Example Ansible Snippet
- name: Deploy CCL Guard to Customer Instance
  hosts: customer_vps
  tasks:
    - name: Clone Repository
      git: repo=https://github.com/your-org/CCL-Guard dest=/opt/soc
    - name: Run Production Setup
      command: bash /opt/soc/deploy_production.sh
```

## 4. Centralized Monitoring (Director's View)
While instances are isolated, you can point all logs to a central **Grafana/Loki** instance by updating the `logging` configuration in `app.py` to forward events via Syslog or HTTP.

---
*For high-volume licensing and white-labeling requests, contact the SOC Engineering Lead.*
