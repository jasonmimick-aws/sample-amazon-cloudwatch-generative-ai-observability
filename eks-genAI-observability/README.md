# Amazon EKS GenAI Observability Example

## Introduction

This example demonstrates how to deploy a generative AI application to Amazon EKS with comprehensive CloudWatch observability.

The example deploys a weather forecaster CLI application that runs as a containerized service in Amazon EKS with OpenTelemetry tracing.

## Prerequisites

- An AWS account with AWS Identity and Access Management (IAM) permissions for Amazon Bedrock, Amazon CloudWatch, AWS X-Ray, and Amazon EKS
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- Python 3.10 or later
- Amazon [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled for **Claude Sonnet 4** in your AWS environment
- Enable [Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html) in the CloudWatch console
- [eksctl](https://eksctl.io/installation/) (v0.208.x or later) installed
- [Helm](https://helm.sh/) (v3 or later) installed
- [kubectl](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html) installed
- Either:
  - [Podman](https://podman.io/) installed and running
  - (or) [Docker](https://www.docker.com/) installed and running

## Configuration

Before deployment, review and update these configuration values in `docker/app/app.py`:

```python
# Update model_id and region_name if necessary before deployment
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",  # Change model_id if needed
    region_name="us-east-1"  # Change region_name if needed
)
```

## Project Structure

- `chart/` - Contains the Helm chart
  - `values.yaml` - Helm chart default values
- `docker/` - Contains the Dockerfile and application code for the container:
  - `Dockerfile` - Docker image definition
  - `app/` - Application code
  - `requirements.txt` - Python dependencies for the container & local development

## Create EKS Auto Mode cluster

Set environment variables

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export AWS_REGION=us-east-1
export CLUSTER_NAME=eks-strands-agents-demo
```

Create EKS Auto Mode cluster

```bash
eksctl create cluster --name $CLUSTER_NAME --enable-auto-mode
```

Configure kubeconfig context

```bash
aws eks update-kubeconfig --name $CLUSTER_NAME
```

## Building and Pushing Docker Image to ECR

Follow these steps to build the Docker image and push it to Amazon ECR:

1. Authenticate to Amazon ECR:

```bash
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

2. Create the ECR repository if it doesn't exist:

```bash
aws ecr create-repository --repository-name strands-agents-weather --region ${AWS_REGION}
```

3. Build the Docker image:

```bash
docker build --platform linux/amd64 -t strands-agents-weather:latest docker/
```

4. Tag the image for ECR:

```bash
docker tag strands-agents-weather:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/strands-agents-weather:latest
```

5. Push the image to ECR:

```bash
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/strands-agents-weather:latest
```

## Configure EKS Pod Identity to access Amazon Bedrock

Create an IAM policy to allow InvokeModel & InvokeModelWithResponseStream to all Amazon Bedrock models

> **Note:** Replace `<YOUR_REGION>` and `<YOUR_ACCOUNT_ID>` with your actual AWS region and account ID before executing.

```bash
cat > bedrock-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockModelInvocation",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/*",
        "arn:aws:bedrock:<YOUR_REGION>:<YOUR_ACCOUNT_ID>:*"
      ]
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name strands-agents-weather-bedrock-policy \
  --policy-document file://bedrock-policy.json
rm -f bedrock-policy.json
```

Create EKS Pod Identity Agent addon

```bash
eksctl create addon --cluster $CLUSTER_NAME --name eks-pod-identity-agent
```

Create an EKS Pod Identity association with permission for both Bedrock access and sending telemetry to Cloudwatch

```bash
eksctl create podidentityassociation --cluster $CLUSTER_NAME \
  --namespace default \
  --service-account-name strands-agents-weather \
  --permission-policy-arns arn:aws:iam::$AWS_ACCOUNT_ID:policy/strands-agents-weather-bedrock-policy,arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy \
  --role-name eks-strands-agents-weather
```

Create the CloudWatch log group and log stream:

```bash
aws logs create-log-group --log-group-name weather-agent-logs
aws logs create-log-stream --log-group-name weather-agent-logs --log-stream-name eks
```

## Deploy strands-agents-weather application

The Helm chart includes OpenTelemetry environment variables configured in `values.yaml` for agent observability.

```
  - name: AWS_REGION
    value: "us-east-1"
  - name: AWS_DEFAULT_REGION
    value: "us-east-1"
  - name: OTEL_PYTHON_DISTRO
    value: "aws_distro"
  - name: OTEL_PYTHON_CONFIGURATOR
    value: "aws_configurator"
  - name: OTEL_EXPORTER_OTLP_PROTOCOL
    value: "http/protobuf"
  - name: OTEL_TRACES_EXPORTER
    value: "otlp"
  - name: OTEL_EXPORTER_OTLP_LOGS_HEADERS
    value: "x-aws-log-group=weather-agent-logs,x-aws-log-stream=eks,x-aws-metric-namespace=weather-agent-eks"
  - name: OTEL_RESOURCE_ATTRIBUTES
    value: "service.name=weather-agent-eks,aws.log.group.names=weather-agent-logs"
  - name: AGENT_OBSERVABILITY_ENABLED
    value: "true"
```

Deploy the helm chart with the image from ECR

```bash
helm install strands-agents-weather ./chart \
  --set image.repository=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/strands-agents-weather --set image.tag=latest
```

Wait for Deployment to be available (Pods Running)

```bash
kubectl wait --for=condition=available deployments strands-agents-weather --all
```

## Test the Agent

Get a running pod name:

```bash
export POD_NAME=$(kubectl get pods -l app.kubernetes.io/name=strands-agents-weather -o jsonpath='{.items[0].metadata.name}')
```

Execute the CLI application:

```bash
kubectl exec -it $POD_NAME -- opentelemetry-instrument python app.py
```

## Cleanup

Uninstall helm chart

```bash
helm uninstall strands-agents-weather
```

Delete EKS Auto Mode cluster

```bash
eksctl delete cluster --name $CLUSTER_NAME --wait
```

Delete IAM policy

```bash
aws iam delete-policy --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/strands-agents-weather-bedrock-policy
```
