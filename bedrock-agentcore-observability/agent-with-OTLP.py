#!/usr/bin/env python3

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands_tools import http_request
from strands.models import BedrockModel
import logging

# Configure the strands logger
strands_logger = logging.getLogger("strands")
strands_logger.setLevel(logging.INFO)  # Set to INFO or DEBUG to see more logs

# Define a weather-focused system prompt
WEATHER_SYSTEM_PROMPT = """You are a weather assistant with HTTP capabilities. You can:

1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States

When retrieving weather information:
1. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
2. IMPORTANT: Always convert latitude and longitude values to strings before using them in URLs
3. Then use the returned forecast URL to get the actual forecast

When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.

EXAMPLE URL FORMAT:
For coordinates: https://api.weather.gov/points/47.6062,-122.3321
Note that both values are converted to strings and separated by a comma with no space.
Always explain the weather conditions clearly and provide context for the forecast.
"""

# Create a Bedrock model
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",  # Change model_id if needed
    region_name="us-east-1"  # Change region_name if needed
)

# Create an agent with HTTP capabilities (tracing will be enabled automatically)
weather_agent = Agent(
    model=bedrock_model,
    system_prompt=WEATHER_SYSTEM_PROMPT,
    tools=[http_request],
    # Add custom attributes for tracking
    trace_attributes={
        "user.email": "demo@example.com",
        "user.id": "demo-123",
        "tags": [
            "Python-AgentSDK",
            "Observability-Tags",
            "CloudWatch-Demo"
        ]
    },  
)

# Create the Bedrock AgentCore App
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """Process user input and return a weather forecast response"""
    user_message = payload.get("prompt")
    result = weather_agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
