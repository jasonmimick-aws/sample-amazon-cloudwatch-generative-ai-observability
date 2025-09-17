# Amazon ECS GenAI Observability Example

## Introduction

This example demonstrates how to deploy a generative AI application to Amazon ECS with comprehensive CloudWatch observability.   
The example deploys a weather forecaster CLI application that runs as a containerized service in Amazon ECS using AWS Fargate with OpenTelemetry tracing.

## Prerequisites

- An AWS account with AWS Identity and Access Management (IAM) permissions for Amazon Bedrock, Amazon CloudWatch, AWS X-Ray, and Amazon ECS
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- Python 3.10 or later
- Amazon [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled for **Claude Sonnet 4** in your AWS environment
- Enable [Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html) in the CloudWatch console
- Either:
  - [Podman](https://podman.io/) installed and running
  - (or) [Docker](https://www.docker.com/) installed and running   

## Project Structure

- `cloudformation/` - Contains the CloudFormation template
    - `weather-agent-ecs.yaml` - Complete ECS deployment (VPC, cluster, task definition, service)
- `docker/` - Contains the Dockerfile and application code for the container:
     - `Dockerfile` - Docker image definition
     - `app/` - Application code
     - `requirements.txt` - Python dependencies for the container & local development
  
## Configuration

Before deployment, review and update these configuration values in `docker/app/app.py`:

```python
# Update model_id and region_name if necessary before deployment
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",  # Change model_id if needed
    region_name="us-east-1"  # Change region_name if needed
)
```

## Set Environment Variables

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export AWS_REGION=us-east-1
export CLUSTER_NAME=weather-agent-ecs-cluster
export SERVICE_NAME=weather-agent-ecs
```

## Building and Pushing Docker Image to ECR

Follow these steps to build the Docker image and push it to Amazon ECR:

1. Authenticate to Amazon ECR:
```bash
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

2. Create the ECR repository if it doesn't exist:
```bash
aws ecr create-repository --repository-name weather-agent-ecs --region ${AWS_REGION}
```

3. Build the Docker image:
```bash
docker build --platform linux/amd64 -t weather-agent-ecs:latest docker/
```

4. Tag the image for ECR:
```bash
docker tag weather-agent-ecs:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/weather-agent-ecs:latest
```

5. Push the image to ECR:
```bash
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/weather-agent-ecs:latest
```

## Deploy Complete ECS Stack

1. Create the CloudWatch log group and log stream:
```bash
aws logs create-log-group --log-group-name weather-agent-logs
aws logs create-log-stream --log-group-name weather-agent-logs --log-stream-name ecs
```

2. Deploy the complete stack (VPC, ECS cluster, task definition, and service):
```bash
aws cloudformation deploy \
  --template-file cloudformation/weather-agent-ecs.yaml \
  --stack-name weather-agent-ecs \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ClusterName=${CLUSTER_NAME} \
    ServiceName=${SERVICE_NAME} \
    ImageUri=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/weather-agent-ecs:latest
```

## Test the Agent

1. Get the running task ARN:
```bash
export TASK_ARN=$(aws ecs list-tasks --cluster ${CLUSTER_NAME} --service-name ${SERVICE_NAME} --query 'taskArns[0]' --output text)
```

2. Execute the CLI application:
```bash
aws ecs execute-command \
  --cluster ${CLUSTER_NAME} \
  --task ${TASK_ARN} \
  --container weather-agent-ecs \
  --interactive \
  --command "opentelemetry-instrument python app.py"
```

## Cleanup

Delete the CloudFormation stack:
```bash
aws cloudformation delete-stack --stack-name weather-agent-ecs
```

Wait for stack to be deleted:
```bash
aws cloudformation wait stack-delete-complete --stack-name weather-agent-ecs
```

Delete the ECR repository:
```bash
aws ecr delete-repository --repository-name weather-agent-ecs --force --region ${AWS_REGION}
```
