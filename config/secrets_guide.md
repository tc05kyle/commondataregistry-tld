# Production Secrets Configuration Guide

This guide explains how to configure all the required secrets for the Data Registry Platform production deployment.

## Required Secrets

### Linode Object Storage
Configure these secrets for media and static file storage:

```bash
LINODE_BUCKET_NAME=your-bucket-name
LINODE_ACCESS_KEY=your-linode-access-key
LINODE_SECRET_KEY=your-linode-secret-key
LINODE_REGION=us-east-1  # Optional, defaults to us-east-1
```

**How to get these:**
1. Login to Linode Cloud Manager
2. Go to Object Storage section
3. Create a new bucket or use existing one
4. Go to Access Keys section
5. Create a new access key pair

### Linode Database
Configure these secrets for production database:

```bash
LINODE_DB_HOST=your-database-host.linode.com
LINODE_DB_NAME=dataregistry
LINODE_DB_USER=your-database-user
LINODE_DB_PASSWORD=your-database-password
LINODE_DB_PORT=5432  # Optional, defaults to 5432
LINODE_DB_SSL_MODE=require  # Optional, defaults to require
```

**How to get these:**
1. Login to Linode Cloud Manager
2. Go to Databases section
3. Create a new PostgreSQL database or use existing one
4. Get connection details from database dashboard

### SendGrid Email Service
Configure these secrets for production email sending:

```bash
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=Your Organization Name
SENDGRID_TEMPLATE_APPROVAL=d-template-id-for-approval  # Optional
SENDGRID_TEMPLATE_REJECTION=d-template-id-for-rejection  # Optional
```

**How to get these:**
1. Sign up for SendGrid account
2. Go to Settings > API Keys
3. Create a new API key with Full Access
4. Verify your sender email/domain in Settings > Sender Authentication

### Application Configuration
Optional application settings:

```bash
APP_ENVIRONMENT=production
APP_DEBUG=false
APP_DOMAIN=yourdomain.com
APP_SECRET_KEY=your-secret-key-for-encryption
APP_TIMEZONE=UTC
```

## Setting Secrets in Replit

1. Go to your Replit project
2. Click on "Secrets" tab in the left sidebar
3. Add each secret as key-value pairs
4. Click "Add new secret" for each one

## Verification

After setting all secrets, the application will automatically:
- Test Linode Object Storage connection
- Verify Linode Database connection
- Validate SendGrid API key
- Display status in the production dashboard

## Troubleshooting

### Linode Object Storage Issues
- Ensure bucket name is globally unique
- Verify access key has proper permissions
- Check region matches your bucket location

### Linode Database Issues
- Ensure database is running and accessible
- Verify user has proper permissions
- Check SSL requirements

### SendGrid Issues
- Verify API key has full access permissions
- Ensure sender email is verified
- Check domain authentication status

## Security Best Practices

1. **Never commit secrets to code**
2. **Use environment variables only**
3. **Rotate API keys regularly**
4. **Use least privilege access**
5. **Enable 2FA on all service accounts**
6. **Monitor usage and access logs**

## Testing Configuration

Use the production configuration panel in the admin dashboard to verify all services are properly configured and connected.