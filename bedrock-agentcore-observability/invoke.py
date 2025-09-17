import boto3
import json

agent_client = boto3.client(
    "bedrock-agentcore", 
    region_name="us-east-1"  # Change if needed
)

input_text = "Hello, how is weather in Miami?"

# Replace with your actual agent runtime ARN after deployment
response = agent_client.invoke_agent_runtime(
    agentRuntimeArn="arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:runtime/AGENT_NAME",  # Update this ARN
    qualifier="DEFAULT",
    payload=json.dumps({"prompt": input_text}),
)

# Extract the actual response content from the StreamingBody
response_body = response["response"].read().decode("utf-8")

print(
    "Full Response Metadata:",
    {
        "RequestId": response["ResponseMetadata"]["RequestId"],
        "StatusCode": response["statusCode"],
        "TraceId": response["traceId"],
        "SessionId": response["runtimeSessionId"],
    },
)

print("\nAgent Response:", response_body)
