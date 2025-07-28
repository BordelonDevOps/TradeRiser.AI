# AWS Amplify Deployment Guide for TradeRiser

This guide will help you deploy your TradeRiser platform to AWS Amplify directly from your GitHub repository.

## Prerequisites

1. **AWS Account**: Ensure you have an active AWS account
2. **GitHub Repository**: Your code is already pushed to `https://github.com/BordelonDevOps/TradeRiser.AI`
3. **Environment Variables**: You'll need to configure your API keys in Amplify

## Deployment Files Created

The following files have been added to support AWS Amplify deployment:

- `amplify.yml` - Build configuration for Amplify
- `application.py` - Main entry point for AWS deployment
- `runtime.txt` - Specifies Python version
- `Procfile` - Process configuration for web server

## Step-by-Step Deployment

### 1. Access AWS Amplify Console

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. Click "Get Started" under "Deploy"

### 2. Connect Your Repository

1. Select "GitHub" as your repository service
2. Authorize AWS Amplify to access your GitHub account
3. Select your repository: `BordelonDevOps/TradeRiser.AI`
4. Choose the `main` branch

### 3. Configure Build Settings

1. Amplify will automatically detect the `amplify.yml` file
2. Review the build configuration (it should be automatically populated)
3. Click "Next"

### 4. Environment Variables

Add the following environment variables in the Amplify console:

```
FLASK_ENV=production
PORT=8000
HOST=0.0.0.0

# Add your API keys (replace with actual values)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Redis configuration (if using)
REDIS_URL=your_redis_url
```

### 5. Deploy

1. Review all settings
2. Click "Save and Deploy"
3. Wait for the deployment to complete (usually 5-10 minutes)

### 6. Access Your Application

Once deployed, Amplify will provide you with a URL like:
`https://main.d1234567890.amplifyapp.com`

## Post-Deployment Configuration

### Custom Domain (Optional)

1. In the Amplify console, go to "Domain Management"
2. Add your custom domain
3. Follow the DNS configuration instructions

### Monitoring and Logs

1. Use the Amplify console to monitor deployments
2. Check CloudWatch logs for application errors
3. Set up alarms for critical metrics

## Troubleshooting

### Common Issues

1. **Build Failures**: Check the build logs in Amplify console
2. **Missing Dependencies**: Ensure all packages are in `requirements.txt`
3. **Environment Variables**: Verify all required API keys are set
4. **Port Issues**: Ensure the application binds to `0.0.0.0:$PORT`

### Build Logs

If deployment fails, check:
1. Amplify console > App > Build logs
2. Look for Python/pip installation errors
3. Check for missing environment variables

## Updating Your Application

To update your deployed application:

1. Push changes to your GitHub repository
2. Amplify will automatically trigger a new build
3. Monitor the deployment in the Amplify console

## Cost Considerations

- AWS Amplify pricing is based on build minutes and data transfer
- Estimate: ~$5-15/month for a small to medium application
- Monitor usage in the AWS billing console

## Security Best Practices

1. **Never commit API keys** to your repository
2. **Use environment variables** for all sensitive data
3. **Enable HTTPS** (automatically handled by Amplify)
4. **Regular security updates** for dependencies

## Support

For issues:
1. Check AWS Amplify documentation
2. Review CloudWatch logs
3. Contact AWS support if needed

---

**Note**: This deployment configuration is optimized for production use with proper security and performance settings.