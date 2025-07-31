# Image Batch Tagger

A Gradio application for batch tagging images with captions using language models.

## Features

1. Set input directory for images
2. Set output directory for tagged images and captions
3. Rename images with custom numbering and prefixes/suffixes
4. Use custom prompts for caption generation
5. Choose between API models (LM Studio) and local GGUF models
6. Test with single images or batch process entire directories
7. Support for different quantizations (F16, Q4_K, Q8_0) for local models

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. For local model inference, you need to install llama.cpp:
   ```
   git clone https://github.com/ggerganov/llama.cpp.git
   cd llama.cpp
   make
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```

2. Open your browser and go to the URL displayed in the terminal (typically http://localhost:7860)

## Model Options

### API Models
- Connects to LM Studio API at http://localhost:1234
- Click "Refresh Models" to fetch available models

### Local Models
- Download GGUF models from Hugging Face (or HF Mirror)
- Support for different quantizations:
  - F16 (16.1 GB) - Highest quality, largest size
  - Q4_K (4.92 GB) - Good balance of quality and size (default)
  - Q8_0 (8.54 GB) - High quality, moderate size
- Models are cached locally to avoid re-downloading
- Uses llama.cpp for inference

## Batch Processing Options

1. Select input and output directories
2. Optionally add a custom prompt for all images
3. Enable image renaming with:
   - Custom prefix
   - Custom suffix
   - Starting number for numbering

## Single Image Testing

Upload a single image to test the caption generation without saving results to disk.

## Testing

A test image is provided in the `examples` directory. You can use this to test the application.

You can also download model files directly using the provided script:
```
python download_model.py --quantization Q4_K
```

## Notes

- Supported image formats: PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP
- When renaming images, the original file extension is preserved
- Captions are saved as TXT files with the same name (or renamed name) as the image
- Local model inference requires llama.cpp to be installed and built