![Project Banner](assets/banner.png)

# MinuteNinja

**VTT Transcription Processor and Meeting Minutes Generator**

---

## Overview
MinuteNinja automates the creation of meeting minutes from transcription files (VTT or text) using OpenAI-compatible language models. It extracts key information such as decisions, actions, and conclusions, presenting them in a clear and structured format.

---

## Features
- Cleans and preprocesses transcripts (removes noise, timestamps, etc.)
- Extracts essential information (decisions, actions, conclusions)
- Generates formal meeting minutes in multiple languages
- Supports OpenAI-compatible APIs and local models
- Configurable parameters for text segmentation and model behavior
- Customizable output file paths

---

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/alisio/Minute-Ninja.git
   cd Minute-Ninja
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   > Requires Python 3.7+

---

## Usage
Run the main script with the path to the transcript file and desired parameters:
```bash
python minute_ninja.py path/to/transcript.vtt --model "gpt-4"
```

### Common Parameters:
- `--model`: LLM model to use (e.g., `gpt-4`)
- `--api-base`: API base URL (e.g., `https://api.openai.com/v1`)
- `--api-key`: API key
- `--language`: Language for the minutes (e.g., `english`, `portuguese`)
- `--output`: Custom output file path

### Example:
```bash
python minute_ninja.py transcript.vtt --model "gpt-4" --language "english" --output "./meeting_minutes.txt"
```

---

## Environment Variables
Set these environment variables for convenience:
```bash
# OpenAI API
export OPENAI_API_BASE="https://api.openai.com/v1"
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4"

# Local ollama API Example 
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_API_KEY=""
export OPENAI_MODEL="gemma3:4b"
```

---

## Output
The output file will be saved in the same directory as the input file unless a custom path is specified. The default format is:
```
{input_filename}_summary_{language}_{model_name}.txt
```

---

## Supported Languages
- English
- Portuguese
- Spanish
- French
- German

---

## License
This project is licensed under the MIT License.

---

## Contact
Author: Antonio Alisio de Meneses Cordeiro  
Email: alisio.meneses@gmail.com
