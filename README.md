# MinuteNinja — VTT Transcription Processor and Meeting Minutes Generator

Processing VTT (or text) transcriptions and generating formatted meeting minutes using an OpenAI-compatible language model.

## Features
- Cleaning and preprocessing transcripts (removal of timestamps, noise, repeated speaker labels)
- Consolidation of fragmented speech segments from the same participant
- Topic segmentation with token limits
- Extraction of essential information (decisions, actions, conclusions)
- Generation of formal minutes in multiple languages

## Requirements
- Python 3.7+
- OpenAI Library (`pip install openai`)
- API key and URL for an OpenAI-compatible endpoint

## Usage
```bash
# Basic usage
python minute_ninja.py path/to/transcript.vtt --model "gpt-4"

# Specifying API parameters
python minute_ninja.py path/to/transcript.vtt \
  --model "gpt-4" \
  --api-base "https://api.openai.com/v1" \
  --api-key "YOUR_API_KEY" \
  --language "portuguese"
```

## Ollama Usage Example
```bash
# Configure environment for a local Ollama server (OpenAI-compatible)
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_API_KEY=""

# Run the script using Ollama as the LLM service
python minute_ninja.py path/to/transcript.vtt \
  --model "gemma3:12b-it-qat" \
  --language "portuguese"
```

The output will be saved in the same directory as the input file, with the suffix `_summary_<language>`.

## Supported Languages
- English
- Portuguese
- Spanish
- French
- German

## Author
Antonio Alisio de Meneses Cordeiro  
alisio.meneses@gmail.com
