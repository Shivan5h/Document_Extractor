import json
import httpx
import os
import base64
import io
from PIL import Image
import fitz  # PyMuPDF

class AnthropicDirectClient:
    """Simple client to directly call the Anthropic API without using the official SDK."""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    
    def create_message(self, system, messages, model="claude-3-7-sonnet-20250219", max_tokens=4000, temperature=0):
        """Create a message directly using the API."""
        url = f"{self.base_url}/messages"
        
        payload = {
            "model": model,
            "system": system,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
            return response.json()

def pdf_to_images(pdf_data, max_pages=10):
    """Convert PDF bytes to a list of PNG images encoded as base64 strings."""
    images = []
    
    # Create a temporary file-like object
    pdf_stream = io.BytesIO(base64.b64decode(pdf_data))
    
    # Open the PDF
    try:
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        # Process each page (up to max_pages)
        for page_num in range(min(len(doc), max_pages)):
            page = doc.load_page(page_num)
            
            # Render page to an image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better resolution
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Save as PNG in memory
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Convert to base64
            base64_encoded = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            images.append(base64_encoded)
        
        return images
    except Exception as e:
        raise Exception(f"Error converting PDF to images: {str(e)}")

# Function to use in main application
def extract_data_with_direct_client(pdf_base64, api_key, prompt):
    """Extract data using a direct API call to Anthropic."""
    try:
        client = AnthropicDirectClient(api_key)
        
        # Convert PDF to images
        pdf_images = pdf_to_images(pdf_base64)
        
        # Create content array with images
        content = []
        for img_base64 in pdf_images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })
        
        # Add text prompt at the end
        content.append({
            "type": "text",
            "text": "Extract the purchase order information as specified in your instructions. This is a PDF document converted to images."
        })
        
        # Make the API call
        response = client.create_message(
            system=prompt,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
        
        # Process the response
        if "content" in response and len(response["content"]) > 0:
            response_text = response["content"][0]["text"]
            
            # Find JSON content (it might be wrapped in code blocks)
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            # Parse JSON
            extracted_data = json.loads(json_str)
            return extracted_data, None
        else:
            return None, "No content in response"
    except Exception as e:
        return None, f"Error with direct Anthropic API call: {str(e)}" 