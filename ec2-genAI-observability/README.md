# Amazon EC2 GenAI Observability Example

## Introduction

This example demonstrates how to deploy a generative AI application to Amazon EC2 with comprehensive CloudWatch observability.  
The example deploys a weather forecaster CLI application that runs directly on an EC2 instance with OpenTelemetry tracing and CloudWatch integration.

## Prerequisites

- An AWS account with AWS Identity and Access Management (IAM) permissions for Amazon Bedrock, Amazon CloudWatch, AWS X-Ray, and Amazon EC2
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- Python 3.10 or later
- Amazon [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled for **Claude Sonnet 4** in your AWS environment
- Enable [Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html) in the CloudWatch console

## Configuration

Before deployment, review and update these configuration values in the application files:

**In `app/app.py` and `app/app-customspan.py`:**

```python
# Update model_id and region_name if necessary before deployment
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",  # Change model_id if needed
    region_name="us-east-1"  # Change region_name if needed
)
```

**In `cloudformation/weather-agent-ec2.yaml`:**

```python
# Update model_id and region_name if necessary before deployment
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",  # Change model_id if needed
    region_name=os.environ.get("AWS_REGION", "us-east-1")  # Change region_name if needed
)
```

## Project Structure

- `cloudformation/` - Contains the CloudFormation template
  - `weather-agent-ec2.yaml` - EC2 instance, VPC, IAM roles, and security groups
- `app/` - Contains the application code:
  - `app.py` - Weather agent application
  - `app-customspan.py` - Weather agent with custom OpenTelemetry spans
  - `requirements.txt` - Python dependencies
  - `user-data.sh` - EC2 user data script for setup

## Set Environment Variables

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export AWS_REGION=us-east-1
export INSTANCE_NAME=weather-agent-ec2
```

## Deploy EC2 Stack

1. Create the CloudWatch log group and log stream:

```bash
aws logs create-log-group --log-group-name weather-agent-logs
aws logs create-log-stream --log-group-name weather-agent-logs --log-stream-name ec2
```

2. Deploy the complete stack:

```bash
aws cloudformation deploy \
  --template-file cloudformation/weather-agent-ec2.yaml \
  --stack-name weather-agent-ec2 \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    InstanceName=${INSTANCE_NAME}
```

## Connect to EC2 Instance

1. Get the instance ID:

```bash
export INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name weather-agent-ec2 \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)
```

2. Connect using Session Manager:

```bash
aws ssm start-session --target ${INSTANCE_ID}
```

## Run the Weather Agent

After connecting to the EC2 instance, execute the following command to auto-instrument the agent and launch the application:

```
sudo -u ec2-user bash -c "cd /opt/weather-agent && source venv/bin/activate && opentelemetry-instrument python app.py"
```

Note: The user data script automatically installs Python 3.12 and sets up the environment. If you encounter issues, check the logs:

```bash
sudo cat /var/log/cloud-init-output.log
```

## Troubleshooting

If the user data script failed or packages aren't installed:

1. Manually install Python 3.12 (if not already done):

```bash
sudo yum install -y python3.12
```

2. Recreate the virtual environment:

```bash
cd /opt/weather-agent
sudo rm -rf venv
python3.12 -m venv venv
sudo chown -R ec2-user:ec2-user venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Update Application Code

To update the application code on EC2:

1. Connect to the instance (using Session Manager or SSH)
2. Navigate to the application directory:

```bash
cd /opt/weather-agent
```

3. Edit the application file:

```bash
sudo nano app.py
```

4. Restart the application:

```bash
source venv/bin/activate
opentelemetry-instrument python app.py
```

## Cleanup

Delete the CloudFormation stack:

```bash
aws cloudformation delete-stack --stack-name weather-agent-ec2
```

Wait for stack to be deleted:

```bash
aws cloudformation wait stack-delete-complete --stack-name weather-agent-ec2
```

Delete the CloudWatch log group:

```bash
aws logs delete-log-group --log-group-name weather-agent-logs
```
