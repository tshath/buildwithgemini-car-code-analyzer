# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


MODEL = "gemini-3.8-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from app.firestore_tools import (
    lookup_obd2_code,
    list_common_obd2_codes,
    get_vehicle_garage,
    log_diagnostic_event,
)
from app.nhtsa_tools import fetch_nhtsa_recalls
from app.vin_decoder_tool import decode_vin
from app.places_tools import find_nearby_auto_services
from app.maps_tools import geocode_address, find_nearby_places
from app.image_tools import generate_automotive_diagram
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.agents.callback_context import CallbackContext
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback


# WRITE: after each turn, send the session to Memory Bank for durable fact extraction
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


# Agent Engine Sandbox configuration from deployment_metadata.json
AGENT_ENGINE_RUNTIME_ID = "projects/304336212261/locations/us-central1/reasoningEngines/1315229486953791488"
SANDBOX_ENVIRONMENT_NAME = "projects/304336212261/locations/us-central1/reasoningEngines/1315229486953791488/sandboxEnvironments/646384744027652096"

sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_ENVIRONMENT_NAME,
    agent_engine_resource_name=AGENT_ENGINE_RUNTIME_ID,
)


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are PitStop AI, an expert automotive OBD2 diagnostic and repair assistant. "
        "You help drivers and mechanics diagnose trouble codes, assess urgency, identify likely root causes, "
        "and provide step-by-step DIY fixes and cost estimates.\n\n"
        "You remember the user's vehicles, past mechanical issues, tool preferences, and diagnostic history "
        "across conversations and use them to personalize your advice.\n\n"
        "Available Capabilities:\n"
        "- Query the OBD2 trouble code database using `lookup_obd2_code`.\n"
        "- Inspect the user's vehicle garage and diagnostic history using `get_vehicle_garage`.\n"
        "- Execute safe Python code in an isolated Agent Engine sandbox to calculate DIY vs. shop savings, repair estimates, or formulas.\n"
        "- Generate technical component schematics and repair illustrations using `generate_automotive_diagram`.\n"
        "- Geocode addresses to latitude/longitude coordinates using `geocode_address` (Google Maps Geocoding API).\n"
        "- Find nearby places of a specific type (e.g. 'car_repair', 'car_parts_store', 'car_dealer') around coordinates using `find_nearby_places` (Google Places API New).\n"
        "- Locate nearby auto parts stores, dealerships, and mechanics using `find_nearby_auto_services`.\n"
        "- Decode any 17-digit VIN to extract exact engine, cylinder, and drivetrain specs using `decode_vin`.\n"
        "- Check official manufacturer safety recalls and service campaigns via `fetch_nhtsa_recalls`.\n"
        "- Record new diagnostic trouble codes or repair logs using `log_diagnostic_event`.\n"
        "- Browse known trouble codes using `list_common_obd2_codes`."
    ),
    workflow_description="Analyze the automotive request, call diagnostic/lookup tools as needed, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=sandbox_code_executor,
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    instruction=a2ui_instruction,
    tools=[
        PreloadMemoryTool(),
        lookup_obd2_code,
        list_common_obd2_codes,
        get_vehicle_garage,
        log_diagnostic_event,
        decode_vin,
        fetch_nhtsa_recalls,
        generate_automotive_diagram,
        geocode_address,
        find_nearby_places,
        find_nearby_auto_services,
    ],
)









app = App(
    root_agent=root_agent,
    name="app",
)

