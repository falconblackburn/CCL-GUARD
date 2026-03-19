# Cloudflare Integration Guide: CCL Guard

This guide outlines how to connect your Cloudflare infrastructure to CCL Guard for autonomous protection and edge-level remediation.

## 1. Automated Log Ingestion
CCL Guard can ingest Cloudflare WAF and Firewall events via Logpush or the API.

### Option A: API Streaming (Recommended)
Add your Cloudflare credentials to the `.env` file:
```env
CLOUDFLARE_EMAIL=your@email.com
CLOUDFLARE_API_KEY=your_global_api_key
CLOUDFLARE_ZONE_ID=your_zone_id
```

### Option B: Syslog/Webhook
Point your Cloudflare Logpush job to the CCL Guard ingestion endpoint:
`http://your-server-ip:5001/api/v2/ingest`

## 2. Autonomous Edge Remediation
When an AI agent identifies a critical threat, it can automatically trigger Cloudflare actions:

- **IP Jail:** Blocks the offending IP at the Cloudflare Edge firewall.
- **Under Attack Mode:** Dynamically enables high-security challenges for a specific zone.
- **WAF Custom Rules:** Deploys a temporary rule based on the attack signature.

## 3. Deployment Steps
1. **MFA Enforcement:** Ensure your Cloudflare account uses MFA.
2. **API Scoping:** It is recommended to use a scoped API Token with `Zone.Firewall` and `Zone.Logs` permissions rather than the Global API Key.
3. **Verify Connection:** Use the `Agentic Assistant` on the dashboard to ask: "Are we receiving Cloudflare telemetry?"

---
*For technical support, contact the SOC Engineering team.*
