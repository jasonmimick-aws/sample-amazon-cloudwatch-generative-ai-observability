# AWS Bedrock AgentCore Observability Example

A demonstration project showing how to build and deploy a generative AI agent using AWS Bedrock AgentCore with comprehensive CloudWatch observability. This agent uses the Strands framework and includes OpenTelemetry tracing for complete monitoring and observability.

## Prerequisites

- An AWS account with AWS Identity and Access Management (IAM) permissions for Amazon Bedrock, Amazon CloudWatch, AWS X-Ray, and AWS Bedrock AgentCore
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- Python 3.10 or later
- Container runtime (Docker/Finch/Podman) for agent deployment
- Amazon [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) enabled for **Claude Sonnet 4** in your AWS environment
- Enable [Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html) in the CloudWatch console

## Project Structure

```
agentcore_observability/
├── agent.py              # Main agent implementation
├── requirements.txt      # Python dependencies
├── invoke.py            # Test script for deployed agent
├── __init__.py          # Python package initialization
└── README.md            # This file
```

## Configuration

Before deployment, review and update these configuration values in `agent.py`:

```python
# Update model_id and region_name if necessary before deployment
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",  # Change model_id if needed
    region_name="us-east-1"  # Change region_name if needed
)
```

After deployment, update the agent runtime ARN and region in `invoke.py`:

```python
# Update region if needed
agent_client = boto3.client(
    'bedrock-agentcore',
    region_name='us-east-1'  # Change if needed
)

# Replace with your actual agent runtime ARN after deployment
agentRuntimeArn="arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:runtime/AGENT_NAME",  # Update this ARN
```

## Getting Started

### Step 1: Set up the project structure

Create a new project directory and initialize the basic files:

```bash
mkdir my-strands-agent && cd my-strands-agent
touch agent.py
touch requirements.txt
touch __init__.py
```

### Step 2: Prepare agent code and dependencies

#### Create the agent code

Copy the code from `agent.py` in this folder. **Important**: Update `region_name` with the AWS region where you have Claude Sonnet 4 model access enabled.

The agent includes:

- Claude Sonnet 4 model integration
- Weather tool
- OpenTelemetry tracing with custom attributes
- User tracking and tagging for observability

#### Set up dependencies

Copy the dependencies from `requirements.txt` in this folder, which includes all necessary packages for the agent and observability features.

### Step 3: Configure and deploy the agent

#### 1. Create virtual environment and install toolkit

```bash
# Create and activate virtual environment
python -m venv myenv
source myenv/bin/activate

# Install starter toolkit in virtual environment
pip install bedrock-agentcore-starter-toolkit
```

#### 2. Create IAM Role

Create the [AgentCore Runtime Execution Role](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html) and note down the ARN. You'll need this for the deployment step.

#### 3. Configure and deploy to AWS

```bash
# Configure your agent
agentcore configure --entrypoint agent.py -n strands_agentcore -r <AWS_REGION> -er <YOUR_IAM_ROLE_ARN>

# Deploy to AWS
agentcore launch
```

**Replace the placeholders:**

- `<AWS_REGION>` with your region name (e.g., `us-east-1`)
- `<YOUR_IAM_ROLE_ARN>` with the ARN of the IAM role you created

### Step 4: Test your deployment

Once deployed, you can test your agent using the provided test script:

```bash
# Run the test script
python invoke.py
```

You can also invoke directly using the agentcore CLI:

```bash
# Direct CLI invocation
agentcore invoke '{"prompt": "Will it rain tomorrow in seattle?"}'
```

## Observability Features

This project includes comprehensive observability through:

- **OpenTelemetry Tracing**: Automatic trace generation for all agent interactions
- **CloudWatch Integration**: Traces and metrics sent to AWS CloudWatch
- **Custom Attributes**: User ID and custom tags for better filtering and analysis
- **Performance Monitoring**: Latency and error tracking for agent operations

### Trace Attributes

The agent automatically includes these trace attributes:

- `user.id`: User identifier for tracking individual sessions
- `tags`: Custom tags for categorization and filtering

## Troubleshooting

### Common Issues

1. **Model Access**: Ensure you have access to Claude Sonnet 4 in your specified region
2. **IAM Permissions**: Verify your IAM role has the necessary permissions for Bedrock and Lambda
3. **Region Configuration**: Make sure the region in `agent.py` matches your deployment region

## Support

For issues related to:

- **AgentCore**: Check the [AWS Bedrock AgentCore documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html)
- **Strands Framework**: Refer to the [Strands agents documentation](https://strandsagents.com/latest/documentation/docs/)
- **OpenTelemetry**: See the [AWS OpenTelemetry documentation](https://opentelemetry.io/docs/)

## Clean Up

If you no longer want to host the agent in the AgentCore Runtime, use the AgentCore console or the [DeleteAgentRuntime](https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_DeleteAgentRuntime.html) AWS SDK operation to delete the AgentCore Runtime.
