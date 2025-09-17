#!/usr/bin/env python3

from strands import Agent
from strands_tools import http_request
from strands.models import BedrockModel
import logging
import uuid

# OpenTelemetry imports for custom span creation and baggage
from opentelemetry import trace, baggage, context
from opentelemetry.trace import Status, StatusCode

# Get the tracer
tracer = trace.get_tracer(__name__)

# Configure the strands logger
strands_logger = logging.getLogger("strands")
strands_logger.setLevel(logging.INFO)

# Generate a unique session ID
session_id = str(uuid.uuid4())

def set_session_context(session_id):
    """Set the session ID in OpenTelemetry baggage for trace correlation"""
    ctx = baggage.set_baggage("session.id", session_id)
    token = context.attach(ctx)
    logging.info(f"Session ID '{session_id}' attached to telemetry context")
    return token

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

# Create an agent with HTTP capabilities
weather_agent = Agent(
    model=bedrock_model,
    system_prompt=WEATHER_SYSTEM_PROMPT,
    tools=[http_request],
    trace_attributes={
        "session.id": session_id,
        "user.email": "demo@example.com",
        "user.id": "demo-123",
        "tags": [
            "Python-AgentSDK",
            "Observability-Tags",
            "CloudWatch-Demo"
        ]
    },  
)

def extract_location(user_input: str) -> str:
    """Extract location from user query"""
    with tracer.start_as_current_span("location_extraction") as span:
        # Simple location extraction
        cities = ["seattle", "miami", "san francisco", "new york", "chicago", "boston", "denver", "atlanta"]
        location = "other"
        
        for city in cities:
            if city in user_input.lower():
                location = city.title()
                break
        
        span.set_attribute("extracted.location", location)
        span.set_attribute("query.length", len(user_input))
        
        if location != "other":
            span.add_event("location_found", {"location": location})
            span.set_status(Status(StatusCode.OK))
        else:
            span.add_event("location_not_found")
            span.set_status(Status(StatusCode.OK))
        
        return location

def process_weather_query(user_input: str) -> str:
    """Process weather query with custom spans"""
    with tracer.start_as_current_span("weather_query_processing") as span:
        try:
            # Extract location first
            location = extract_location(user_input)
            
            span.set_attribute("query.location", location)
            span.set_attribute("query.type", "weather_forecast")
            span.add_event("query_analysis_complete")
            
            # Call the weather agent
            response = weather_agent(user_input)
            
            span.set_attribute("response.success", True)
            span.set_attribute("response.length", len(str(response)))
            span.add_event("weather_response_generated")
            
            span.set_status(Status(StatusCode.OK))
            return str(response)
            
        except Exception as e:
            span.set_attribute("error.type", type(e).__name__)
            span.add_event("processing_error", {"error": str(e)})
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise

# Example usage
if __name__ == "__main__":
    # Set session context in baggage for trace correlation
    context_token = set_session_context(session_id)
    
    try:
        # Create a custom span for the weather application
        with tracer.start_as_current_span("weather_agent_session") as session_span:
            session_span.set_attribute("application.name", "weather-agent")
            session_span.set_attribute("application.version", "1.0")
            session_span.set_attribute("session.id", session_id)
            session_span.add_event("session_started")
            
            print(f"\nWeather Forecaster Agent (Session: {session_id})\n")
            print("Ask about weather in any US city:")
            print("• 'What's the weather like in Seattle?'")
            print("• 'Will it rain tomorrow in Miami?'")
            print("• Type 'exit' to quit\n")

            query_count = 0
            
            # Interactive loop
            while True:
                try:
                    with tracer.start_as_current_span("user_interaction") as interaction_span:
                        query_count += 1
                        interaction_span.set_attribute("interaction.number", query_count)
                        interaction_span.add_event("user_prompt_displayed")
                        
                        user_input = input(f"Query #{query_count} > ")
                        
                        if user_input.lower() == "exit":
                            interaction_span.add_event("session_ended_by_user")
                            print("\nGoodbye! 👋")
                            break
                        
                        interaction_span.set_attribute("user.query", user_input[:100])  # Truncate for privacy
                        interaction_span.add_event("user_input_received")
                        
                        # Process the weather query
                        response = process_weather_query(user_input)
                        print(f"\n{response}\n")
                        
                        interaction_span.add_event("response_delivered")
                        interaction_span.set_status(Status(StatusCode.OK))
                        
                        # Log for trace correlation
                        strands_logger.info(f"Query {query_count} processed successfully")
                         
                except KeyboardInterrupt:
                    session_span.add_event("session_interrupted")
                    print("\n\nSession interrupted. Exiting...")
                    break
                except Exception as e:
                    session_span.add_event("session_error", {"error": str(e)})
                    print(f"\nError: {str(e)}")
            
            session_span.set_attribute("total.queries", query_count)
            session_span.add_event("session_completed")
    
    finally:
        # Detach context when done
        context.detach(context_token)
        logging.info(f"Session context for '{session_id}' detached")
