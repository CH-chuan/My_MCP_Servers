# MCP DALL-E Server

A FastMCP server that generates images using OpenAI's DALL-E models (DALL-E 2 and DALL-E 3) based on text prompts.

## Features

- Generate images from text prompts using DALL-E 3 or DALL-E 2
- Customize image generation with parameters like size, quality, style, and model
- Control whether DALL-E revises your prompts
- Automatically saves generated images locally with metadata
- Return image URLs and metadata in a structured format
- Built with FastMCP for easy integration with other MCP clients

## Setup

### Prerequisites

- Python 3.12 or higher
- Azure OpenAI API access with DALL-E deployment

### Installation

First, clone the repository.
```bash
# if you only want this folder under repo
# 1. Clone with minimal data
git clone --filter=blob:none --no-checkout https://github.com/CH-chuan/My_MCP_Servers.git
cd My_MCP_Servers

# 2. Initialize sparse-checkout in cone mode (for easier folder selection)
git sparse-checkout init --cone

# 3. Set the specific folder you want
git sparse-checkout set mcp-dalle-server

# 4. Checkout the branch (usually 'main')
git checkout main

# 5. Go to the folder
cd mcp-dalle-server
```

Now, you are to install the dependencies.
```bash
# Create a new project with UV
uv init mcp-dalle-server --python=python3.12
cd mcp-dalle-server

# Create and activate a virtual environment
uv venv --python=python3.12
source .venv/bin/activate

# Install dependencies
uv pip install -e .
# Or install dependencies individually
uv pip install "mcp[cli]>=1.6.0" openai>=1.0.0 python-dotenv>=1.0.0
```

#### Troubleshooting UV Installation

If you don't have UV installed, you can install it with:

```bash
# Install UV using the official installer
curl -sSf https://install.ultraviolet.rs | sh

# Or using pip
pip install uv
```

Make sure UV is in your PATH after installation. You can verify the installation with:

```bash
uv --version
```

### Environment Configuration

Create a `.env` file in the project root with the following variables (you can copy from the provided `.env.example` file):

```
# Azure OpenAI API credentials
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here

# Optional: Specify the DALL-E model deployment name if different from 'dalle3'
# AZURE_OPENAI_DALLE_DEPLOYMENT=your_deployment_name
```

You can copy the example file with:

```bash
cp .env.example .env
# Then edit .env with your actual credentials
```

## Usage

### Starting the Server

Run the server with:

```bash
mcp dev server.py
```

### Using the Image Generation Tool

The server exposes a `generate_image` tool that accepts the following parameters:

- `prompt` (required): The text prompt to generate the image from
- `size` (optional): The size of the generated image (1024x1024, 1792x1024, or 1024x1792). Default: "1024x1024"
- `quality` (optional): The quality of the generated image (standard or hd). Default: "standard"
- `n` (optional): The number of images to generate (1-10). Default: 1
- `style` (optional): The style of the generated image (natural or vivid). Default: None
- `model` (optional): The DALL-E model to use (dalle3 or dalle2). Default: "dalle3"
- `revise_prompt` (optional): Whether to allow DALL-E to revise the prompt (True) or not (False). Default: True

### Image Storage

Generated images are automatically saved locally in an `images` directory with the following structure:

```
images/
  YYYYMMDD_HHMMSS/  # Timestamp-based folder for each generation
    generated_image.png
    metadata.json
```

The metadata.json file contains all parameters used for generation along with the original and revised prompts.

### Example Response

```json
{
  "success": true,
  "revised_prompt": "A detailed revised version of your prompt",
  "url": "https://example.com/image.png",
  "model": "dalle3",
  "size": "1024x1024",
  "quality": "standard",
  "style": "vivid",
  "timestamp": 1678901234,
  "local_image_path": "/path/to/images/timestamp/generated_image.png",
  "local_metadata_path": "/path/to/images/timestamp/metadata.json"
}
```

## Error Handling

If an error occurs during image generation, the server will return a response with `success: false` and an error message:

```json
{
  "success": false,
  "error": "Error message here"
}
```

## License

See the LICENSE file for details.