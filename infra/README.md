# Infrastructure notes

This directory holds AWS deployment documentation. Production stack:

```
Route 53 → CloudFront → ALB → EC2 (gunicorn → app.server:server)
                                  │
                                  ├── S3      (data bucket: CSV / GeoJSON / Parquet)
                                  ├── Cognito (user pool, hosted UI)
                                  └── DynamoDB (sessions, audit log)
```

## EC2 unit file

`/etc/systemd/system/wildfire-app.service`:

```ini
[Unit]
Description=Wildfire Mapping Platform
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/wildfire-app
EnvironmentFile=/etc/wildfire-app/env
ExecStart=/opt/wildfire-app/.venv/bin/gunicorn \
  --workers 4 --worker-class gthread --threads 2 \
  --bind 0.0.0.0:8050 --timeout 60 \
  app.server:server
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## CloudFront

- Origin: ALB DNS name, HTTPS only
- Cache policy: pass-through for `/_dash-*` (Dash component bundles cache
  by hash, safe to cache forever)
- TTL=0 for `/`, `/login`, `/health`
- Forward all cookies (Flask session) and `Authorization` header

## Cognito wiring

1. Create a user pool with email as username, MFA optional.
2. Create an app client with `code` grant + `openid email profile` scopes.
3. Set allowed callback URL = `https://<your-domain>/auth/callback`.
4. In `app/auth.py`, replace `_verify_demo_credentials` with a Cognito
   `initiate-auth` call (USER_PASSWORD_AUTH flow), exchange the JWT, and
   store the verified email in the Flask session.

## DynamoDB tables

- **`wildfire-sessions`** — PK `session_id`, TTL on `expires_at`. Replaces
  Flask's default in-memory session store for multi-instance deploys.
- **`wildfire-audit`** — PK `event_id`, GSI on `user_email + timestamp`.
  For activity logging once required.

## TODO (real IaC)

- Terraform module: VPC + EC2 + ALB + CloudFront + Cognito + S3 + DynamoDB
- GitHub Actions: build + push to ECR (when we containerize) + EC2 deploy
- CloudWatch dashboard: requests/sec, p95 latency, 5xx rate, gunicorn worker memory
