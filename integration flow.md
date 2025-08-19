```markdown
+---------------------+
| Customer Device     |
| (Router, ONU, etc.) |
+----------+----------+
           |
           v
+---------------------+           +-------------------+
| NAS (e.g. Mikrotik, | <-------> |   RADIUS Server   |
| Cisco, etc.)        |           | (FreeRADIUS, etc.)|
+----------+----------+           +--------+----------+
           |                               |
           v                               v
+---------------------+           +------------------------+
| ISP Framework CRM   | <-------> | Customer Tariff Plans  |
| (Accounts, Billing) |           | & Authentication Store |
+---------------------+           +------------------------+

```