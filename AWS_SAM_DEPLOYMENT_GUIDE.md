# AWS SAM Deployment Guide for TradeRiser AI

This guide will help you deploy the TradeRiser AI platform to AWS Lambda using AWS SAM (Serverless Application Model).

## Prerequisites

1. **AWS CLI** - Install and configure with your AWS credentials
   ```bash
   aws configure
   ```

2. **AWS SAM CLI** - Install the SAM CLI
   ```bash
   # Windows (using Chocolatey)
   choco install aws-sam-cli
   
   # macOS (using Homebrew)
   brew install aws-sam-cli
   
   # Linux
   pip install aws-sam-cli
   ```

3. **Docker** - Required for local testing (optional)

## Deployment Steps

### 1. Switch to Lambda Branch
```bash
git checkout lambda
```

### 2. Build the SAM Application
```bash
sam build
```

### 3. Deploy to AWS

#### First-time deployment:
```bash
sam deploy --guided
```

This will prompt you for:
- Stack name (default: `traderiser-ai`)
- AWS Region (default: `us-east-1`)
- Confirm changes before deploy
- Allow SAM to create IAM roles
- Save parameters to samconfig.toml

#### Subsequent deployments:
```bash
sam deploy
```

### 4. Get the API Endpoint
After deployment, SAM will output the API Gateway URL:
```
Outputs:
TradeRiserApiUrl: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod/
```

## Local Testing (Optional)

### Start API locally:
```bash
sam local start-api
```

### Test a specific function:
```bash
sam local invoke TradeRiserFunction
```

## Configuration Files

- **`template.yaml`** - SAM template defining the Lambda function and API Gateway
- **`lambda_handler.py`** - Lambda entry point that adapts Flask to Lambda
- **`samconfig.toml`** - SAM configuration file with deployment settings

## Architecture

```
API Gateway → Lambda Function → Flask Application
```

- **API Gateway**: Handles HTTP requests and CORS
- **Lambda Function**: Runs the Flask application in serverless mode
- **Flask Application**: Your TradeRiser AI platform

## Environment Variables

The Lambda function is configured with:
- `FLASK_ENV=production`
- `PYTHONPATH=/var/task`

## CORS Configuration

CORS is automatically configured to allow:
- All origins (`*`)
- Methods: `GET, POST, PUT, DELETE, OPTIONS`
- Headers: `Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token`

## Monitoring

- **CloudWatch Logs**: Automatic logging for Lambda function
- **CloudWatch Metrics**: Function duration, invocations, errors
- **X-Ray Tracing**: Can be enabled for detailed request tracing

## Cost Optimization

- **Memory**: Set to 1024MB (adjustable in template.yaml)
- **Timeout**: Set to 30 seconds (adjustable in template.yaml)
- **Cold Start**: First request may be slower due to Lambda cold start

## Troubleshooting

### Common Issues:

1. **Import Errors**: Ensure all dependencies are in `requirements.txt`
2. **Timeout**: Increase timeout in `template.yaml` if needed
3. **Memory Issues**: Increase memory allocation in `template.yaml`
4. **CORS Issues**: Check API Gateway CORS configuration

### View Logs:
```bash
sam logs -n TradeRiserFunction --stack-name traderiser-ai --tail
```

### Delete Stack:
```bash
aws cloudformation delete-stack --stack-name traderiser-ai
```

## Security

- Lambda functions run in isolated environments
- API Gateway provides DDoS protection
- Consider adding API keys or authentication for production use

## Next Steps

1. Deploy using the steps above
2. Test the API endpoints
3. Update your frontend to use the new API Gateway URL
4. Set up monitoring and alerts
5. Consider adding authentication (AWS Cognito)

## Support

For issues with AWS SAM deployment, check:
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)