import json
import uuid
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-03-3ff306ba56bc"
BUCKET_NAME = "pitstop-car-analyzer-assets-qwiklabs-gcp-03-3ff306ba56bc"

async def generate_automotive_diagram(
    prompt: str,
    component_name: str,
    tool_context: ToolContext
) -> str:
    """Generate an automotive technical diagram, component schematic, or repair illustration
    using the gemini-3.1-flash-lite-image model in the global region.

    The generated image is:
    1. Saved as an ADK session artifact via tool_context.save_artifact so it shows up in the Playground's Artifacts panel.
    2. Uploaded directly from memory (without writing to a local file) to the public Cloud Storage bucket.

    Args:
        prompt: Detailed description of the automotive illustration or diagram to generate
                (e.g., 'Clear technical schematic showing how to locate and inspect the spark plugs and ignition coils on an inline-4 engine').
        component_name: Short identifier for the component (e.g., 'spark_plug', 'catalytic_converter', 'o2_sensor').

    Returns:
        A JSON string containing the public HTTPS URL (https://storage.googleapis.com/<bucket>/<object>)
        and artifact filename.
    """
    clean_name = component_name.strip().lower().replace(" ", "_")
    image_filename = f"{clean_name}_{uuid.uuid4().hex[:8]}.jpg"

    # 1. Generate image using gemini-3.1-flash-lite-image in the global region
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global"
    )

    full_prompt = (
        f"Automotive technical illustration or repair diagram: {prompt}. "
        "Clear, clean, informative engineering diagram style, labeled automotive components."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=[full_prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="1:1",
                    image_size="1K"
                )
            )
        )
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to generate image with gemini-3.1-flash-lite-image: {str(e)}"
        })

    # Extract raw image bytes
    image_bytes = None
    mime_type = "image/jpeg"
    for part in response.parts:
        if part.inline_data and part.inline_data.data:
            image_bytes = part.inline_data.data
            mime_type = part.inline_data.mime_type or "image/jpeg"
            break

    if not image_bytes:
        return json.dumps({
            "status": "error",
            "message": "No image data returned by gemini-3.1-flash-lite-image."
        })

    # 2. Save artifact in ADK session via await tool_context.save_artifact
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    try:
        await tool_context.save_artifact(filename=image_filename, artifact=artifact_part)
    except Exception as e:
        pass

    # 3. Upload bytes directly to public Cloud Storage bucket in memory (no local file path)
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(image_filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to upload image bytes to GCS: {str(e)}"
        })

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{image_filename}"

    return json.dumps({
        "status": "success",
        "component": component_name,
        "artifact_filename": image_filename,
        "public_image_url": public_url,
        "message": f"Generated technical illustration and published to {public_url}"
    }, indent=2)
