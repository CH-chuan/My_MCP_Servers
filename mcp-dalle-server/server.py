from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Optional, Literal, Dict, List, Any
import os
import json
import requests
import datetime
from dotenv import load_dotenv

from mcp.server.fastmcp import Context, FastMCP
from openai import AzureOpenAI

# Load environment variables from .env file
load_dotenv()

# Ensure required environment variables are set
required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please create a .env file with these variables or set them in your environment.")
    exit(1)

# Check for optional environment variables
dalle_deployment = os.getenv("AZURE_OPENAI_DALLE_DEPLOYMENT", "dalle3")
print(f"Using DALL-E deployment: {dalle_deployment}")

# Create a named server
mcp = FastMCP("MCP DALL-E Server", dependencies=["openai", "python-dotenv"])


@dataclass
class AppContext:
    client: AzureOpenAI
    # Store generated images for reference
    generated_images: List[Dict[str, Any]] = field(default_factory=list)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize OpenAI client on startup
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not api_key or not api_base:
        raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables must be set")
    
    client = AzureOpenAI(
        api_version="2024-02-01",
        api_key=api_key,
        azure_endpoint=api_base
    )
    
    # Log successful initialization
    print(f"Successfully initialized Azure OpenAI client with endpoint: {api_base}")
    
    try:
        # Initialize with empty list for storing generated images
        yield AppContext(client=client, generated_images=[])
    finally:
        # No specific cleanup needed for the OpenAI client
        pass


# Pass lifespan to server
mcp = FastMCP("MCP DALL-E Server", lifespan=app_lifespan)


@mcp.tool()
def generate_image(
    ctx: Context,
    prompt: str,
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024",
    quality: Literal["standard", "hd"] = "standard",
    n: int = 1,
    style: Optional[Literal["natural", "vivid"]] = None,
    model: Literal["dalle3", "dalle2"] = "dalle3",
    revise_prompt: bool = True,
) -> dict:
    """Generate an image based on the provided prompt and return the image URL
    
    Args:
        prompt: The text prompt to generate the image from
        size: The size of the generated image (1024x1024, 1792x1024, or 1024x1792)
        quality: The quality of the generated image (standard or hd)
        n: The number of images to generate (1-10)
        style: The style of the generated image (natural or vivid)
        model: The DALL-E model to use (dalle3 or dalle2)
        revise_prompt: Whether to allow DALL-E to revise the prompt (True) or not (False)
        
    Returns:
        A dictionary containing the generated image URLs and other metadata
    """
    client = ctx.request_context.lifespan_context.client
    
    # Validate parameters
    if n < 1 or n > 10:
        raise ValueError("Number of images (n) must be between 1 and 10")
    
    # Validate model parameter
    if model not in ["dalle3", "dalle2"]:
        raise ValueError("Model must be either 'dalle3' or 'dalle2'")
    
    # Prepare parameters for the API call
    # If revise_prompt is False, append instruction to prevent prompt modification
    modified_prompt = prompt
    if not revise_prompt:
        modified_prompt = f"{prompt} do not modify my prompt"
        
    params = {
        "model": model,
        "prompt": modified_prompt,
        "n": n,
        "size": size,
        "quality": quality,
    }
    
    # Add optional parameters if provided
    if style:
        params["style"] = style
    
    try:
        # Call the OpenAI API to generate the image
        result = client.images.generate(**params)
        
        # Convert the response to a dictionary
        response_dict = json.loads(result.model_dump_json())
        
        # Extract timestamp for folder naming
        timestamp = response_dict.get("created")
        timestamp_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
        
        # Prepare response with success flag, revised prompt and URL
        response = {
            "success": True,
            "revised_prompt": response_dict.get("data", [{}])[0].get("revised_prompt", prompt),
            "url": result.data[0].url if result.data else None,
            "model": model,
            "size": size,
            "quality": quality,
            "style": style,
            "timestamp": timestamp
        }
        
        # Download and save the image locally
        if response["url"]:
            try:
                # Create images directory if it doesn't exist
                images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
                if not os.path.isdir(images_dir):
                    os.makedirs(images_dir)
                
                # Create timestamp-based folder for this specific image
                image_folder = os.path.join(images_dir, timestamp_str)
                if not os.path.exists(image_folder):
                    os.makedirs(image_folder)
                
                # Download the image
                image_url = response["url"]
                image_path = os.path.join(image_folder, f"generated_image.png")
                generated_image = requests.get(image_url).content
                
                # Save the image
                with open(image_path, "wb") as image_file:
                    image_file.write(generated_image)
                
                # Save metadata as JSON
                metadata = {
                    "prompt": prompt,
                    "revised_prompt": response["revised_prompt"],
                    "model": model,
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "timestamp": timestamp,
                    "image_path": image_path
                }
                
                metadata_path = os.path.join(image_folder, "metadata.json")
                with open(metadata_path, "w") as metadata_file:
                    json.dump(metadata, metadata_file, indent=2)
                
                # Add local paths to response
                response["local_image_path"] = image_path
                response["local_metadata_path"] = metadata_path
                
                print(f"Image saved to {image_path}")
                print(f"Metadata saved to {metadata_path}")
                
            except Exception as download_error:
                print(f"Error saving image locally: {str(download_error)}")
                # Continue even if local saving fails
        
        # Store the generated image in the context for history
        ctx.request_context.lifespan_context.generated_images.append(response)
        
        # Return the response
        return response
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Only keeping the generate_image tool as requested

# Run the server
if __name__ == "__main__":
    print("Starting MCP DALL-E Server...")
    mcp.run(transport='stdio')