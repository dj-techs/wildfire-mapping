---
name: deploy-aws
description: Use when the user wants to deploy or update the production stack on AWS — pushing a new image to EC2, updating CloudFront, rotating Cognito config, or troubleshooting the live deploy. Triggers: "deploy this", "push to prod", "update CloudFront", "Cognito isn't working", "production env vars".
---

# AWS deploy workflow

Production architecture (per the project brief):

```
Browser → CloudFront (CDN, TLS, caching) → EC2 (gunicorn → Flask+Dash app)
                                              ↓
                                     Cognito (auth) + DynamoDB (sessions)
                                              ↓
                                     S3 (data bucket: CSV/GeoJSON/Parquet)
```

## Pre-deploy checklist

Before any deploy:
- [ ] `pytest` is green
- [ ] `python -m app.server` boots locally with `AUTH_DISABLED=false` and you can log in
- [ ] If data shape changed, the matching files are uploaded to S3 *first*
      (the running app caches at boot; new schema in code + old schema in
      S3 = silent breakage)
- [ ] `.env.production` matches what's set on the EC2 instance — diff them

**Confirm with the user before running any `aws` command that changes
state.** This skill describes the moves; the user authorizes them.

## Common operations

### Update the data files in S3

```bash
aws s3 sync data/ s3://$S3_DATA_BUCKET/ --exclude ".*" --dryrun
# Review the dry-run output, then re-run without --dryrun
```

After upload, restart gunicorn on the EC2 box so the lru_cache reloads:
```bash
ssh ec2-user@<host> "sudo systemctl restart wildfire-app"
```

### Push a code change

The project uses a simple deploy: SSH + pull + restart. (CI/CD is on the
roadmap; see `infra/README.md`.)

```bash
ssh ec2-user@<host> "cd /opt/wildfire-app && git pull && \
  source .venv/bin/activate && pip install -r requirements.txt && \
  sudo systemctl restart wildfire-app"
```

### Invalidate CloudFront after a CSS/JS change

```bash
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/_dash-component-suites/*" "/assets/*"
```

### Cognito user pool sanity check

```bash
aws cognito-idp describe-user-pool --user-pool-id $COGNITO_USER_POOL_ID \
  --query 'UserPool.{Status:Status,Domain:Domain,Schema:SchemaAttributes[?Name==`email`]}'
```

### Tail the app log

```bash
ssh ec2-user@<host> "sudo journalctl -u wildfire-app -f --since '5 minutes ago'"
```

## Rollback

If a deploy goes wrong:
```bash
ssh ec2-user@<host> "cd /opt/wildfire-app && git reset --hard HEAD~1 && \
  sudo systemctl restart wildfire-app"
```
**This is destructive — get user approval first.** If the new code wrote
data to S3 in a new format, rolling back code without rolling back data
will break the app.

## Things this skill won't do without explicit confirmation

- `aws s3 rm` — never delete bucket contents without a green light
- `aws iam` writes — IAM changes need human review
- `aws cognito-idp delete-*` — destructive Cognito ops
- Any production database operation
- Force-pushing to the deploy branch

## When something goes wrong

1. Check the app log first (`journalctl -u wildfire-app`).
2. Check the EC2 instance health (CPU, disk, RAM).
3. Check CloudFront error rate in CloudWatch.
4. Check Cognito sign-in metrics if it's an auth issue.
5. Only then start changing things.

If the deploy is broken and you don't yet know why, **roll back first, then
debug**. The user can wait 60 seconds for a working app; they can't wait
30 minutes for a fix-forward.
