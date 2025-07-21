
![Project Banner](assets/banner.png)

# MinuteNinja

**VTT Transcription Processor and Meeting Minutes Generator**

---

## Table of Contents
- [Project Description](#project-description)
- [Features](#features)
- [Performance Analysis](#performance-analysis)
- [Installation](#installation)
- [Usage](#usage)
- [Advanced Configuration](#advanced-configuration)
- [Examples](#examples)
- [Output](#output)
- [Supported Languages](#supported-languages)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Project Description
MinuteNinja is a tool for processing meeting transcriptions in VTT (or text) format and generating formal minutes using OpenAI-compatible language models. The goal is to automate the creation of meeting minutes by extracting essential information and presenting it in a clear and structured way.

## Features
- Cleans and preprocesses transcripts (removes timestamps, noise, repeated speaker labels)
- Consolidates speech fragments from the same participant
- Topic segmentation with configurable token limits
- Extracts essential information (decisions, actions, conclusions)
- Generates formal minutes in multiple languages
- **Configurable context size and text segmentation parameters**
- **Customizable inference parameters (temperature, top_p, max_tokens)**
- **Automatic inference of meeting title and date when not provided**
- **Fine-tuned control over model behavior and output quality**
- **Custom output file paths with automatic directory creation**
- **Model name inclusion in output filenames with cross-platform sanitization**

## Performance Analysis
We conducted a comprehensive evaluation of 13 different LLM models across two endpoints (DeepInfra API and Ollama Local) to optimize MinuteNinja's performance. Key findings:

### 🏆 **Top Performing Models**
- **Best Overall**: `meta-llama/Llama-4-Scout-17B` (DeepInfra) - 33.77s, exceptional speed + quality
- **Best Local**: `deepseek-r1:1.5b` (Ollama) - 61.61s, zero cost + good quality
- **Best Quality**: `Qwen/Qwen3-32B` (DeepInfra) - 583 lines, maximum detail + analysis

### 📊 **Key Insights**
- **Local models can compete**: Ollama local execution was only 1.8x slower than best API
- **Size ≠ Performance**: 1.5B parameter model outperformed 27B+ models
- **Cost-effectiveness**: Local models offer zero operational cost with acceptable quality
- **Instruction-tuned models**: Essential for structured output like meeting minutes

📋 **[View Complete Performance Analysis](LLM_Performance_Analysis_EN.md)** - Detailed comparison of 13 models with benchmarks, recommendations, and technical specifications.

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/alisio/Minute-Ninja.git
   cd Minute-Ninja
   ```
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   > Requires Python 3.7+

## Usage
Run the main script, providing the path to the transcript file and the desired model:
```bash
python minute_ninja.py path/to/transcript.vtt --model "gpt-4"
```

### Basic Parameters:
- `--model`: LLM model to use
- `--api-base`: OpenAI API base URL (e.g., https://api.openai.com/v1)
- `--api-key`: API key
- `--language`: Language for the generated minutes (english, portuguese, spanish, etc.)

### Advanced Parameters:
- `--context-size`: Model context size in tokens (default: 32000)
- `--segment-size`: Text segment size in tokens for processing (default: 400)
- `--temperature`: Temperature for text generation 0.0-2.0 (default: 0.3)
- `--top-p`: Top-p value for nucleus sampling 0.0-1.0 (default: 1.0)
- `--max-tokens`: Maximum tokens to generate in response
- `--title`: Meeting title (if not provided, will be inferred automatically)
- `--date`: Meeting date (if not provided, will be inferred automatically)
- `--output`: Custom output file path (if not provided, will be generated automatically)

## Advanced Configuration

### Recommended Models by Use Case
Based on our comprehensive testing, here are the optimal model selections:

#### 🚀 **Production/Daily Use**
```bash
# Best overall performance (API)
python minute_ninja.py transcript.vtt --model "meta-llama/Llama-4-Scout-17B-16E-Instruct"

# Best local option (zero cost)
python minute_ninja.py transcript.vtt --model "deepseek-r1:1.5b" --api-base "http://localhost:11434/v1"
```

#### 📋 **Critical Documentation**
```bash
# Maximum quality and detail (API)
python minute_ninja.py transcript.vtt --model "Qwen/Qwen3-32B"

# Quality with privacy (local)
python minute_ninja.py transcript.vtt --model "qwen3:14b" --api-base "http://localhost:11434/v1"
```

#### ⚡ **Fast Prototyping**
```bash
# Quick testing (local)
python minute_ninja.py transcript.vtt --model "gemma3:4b" --api-base "http://localhost:11434/v1"
```

### Advanced Parameter Configuration

#### **Model Behavior Control**
```bash
# Conservative, formal output
python minute_ninja.py transcript.vtt --model "gpt-4" --temperature 0.1 --top-p 0.8

# Creative, detailed output  
python minute_ninja.py transcript.vtt --model "gpt-4" --temperature 0.7 --top-p 1.0

# Concise output with token limit
python minute_ninja.py transcript.vtt --model "gpt-4" --max-tokens 500
```

#### **Custom Output Path**
```bash
# Specify custom output location
python minute_ninja.py transcript.vtt --model "gpt-4" --output "/custom/path/meeting_minutes.txt"

# Organize outputs by date
python minute_ninja.py transcript.vtt --model "gpt-4" --output "./minutes/2025-07-21/team_meeting.txt"

# Different formats for different purposes
python minute_ninja.py transcript.vtt --model "gpt-4" --output "./reports/executive_summary.md"
```
#### **Processing Optimization**
```bash
# Large files with small context models
python minute_ninja.py large_transcript.vtt --context-size 8000 --segment-size 200

# Detailed processing for complex meetings
python minute_ninja.py complex_meeting.vtt --context-size 32000 --segment-size 800

# Meeting with known details
python minute_ninja.py transcript.vtt \
  --title "Q4 Planning Meeting" \
  --date "2025-07-21" \
  --language "portuguese"

# Custom output with all parameters
python minute_ninja.py transcript.vtt \
  --model "gpt-4" \
  --title "Board Meeting" \
  --date "2025-07-21" \
  --language "english" \
  --temperature 0.2 \
  --output "./board_meetings/july_2025_minutes.txt"
```

### Environment Variables
For convenience, set these environment variables:
```bash
# For OpenAI API
export OPENAI_API_BASE="https://api.openai.com/v1"
export OPENAI_API_KEY="your-api-key"
export LLM_CHAT="gpt-4"

# For DeepInfra API
export OPENAI_API_BASE="https://api.deepinfra.com/v1/openai/"
export OPENAI_API_KEY="your-deepinfra-key"
export LLM_CHAT="meta-llama/Llama-4-Scout-17B-16E-Instruct"

# For Ollama Local
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_API_KEY=""
export LLM_CHAT="gemma3:4b"
```

Then you can run simply:
```bash
python minute_ninja.py transcript.vtt --language "portuguese" --temperature 0.5

# Or with custom output
python minute_ninja.py transcript.vtt --language "portuguese" --output "./meeting_notes/$(date +%Y-%m-%d)_summary.txt"
```

## Examples
### Basic usage
```bash
python minute_ninja.py path/to/transcript.vtt --model "gpt-4"
```

### Using top-performing models with advanced configuration
```bash
# Fastest overall with custom parameters (DeepInfra API)
python minute_ninja.py transcript.vtt \
  --model "meta-llama/Llama-4-Scout-17B-16E-Instruct" \
  --api-base "https://api.deepinfra.com/v1/openai/" \
  --api-key "YOUR_DEEPINFRA_KEY" \
  --temperature 0.5 \
  --context-size 16000 \
  --segment-size 300

# Best local model with title and date inference (zero cost)
python minute_ninja.py transcript.vtt \
  --model "deepseek-r1:1.5b" \
  --api-base "http://localhost:11434/v1" \
  --language "english" \
  --title "Weekly Team Meeting" \
  --date "2025-07-21"

# High-quality output with fine-tuned parameters and custom output
python minute_ninja.py transcript.vtt \
  --model "gemma3:4b" \
  --api-base "http://localhost:11434/v1" \
  --language "portuguese" \
  --temperature 0.3 \
  --top-p 0.9 \
  --max-tokens 1000 \
  --segment-size 500 \
  --output "./atas/reuniao_detalhada.txt"
```

### Traditional OpenAI API
```bash
python minute_ninja.py path/to/transcript.vtt \
  --model "gpt-4" \
  --api-base "https://api.openai.com/v1" \
  --api-key "YOUR_API_KEY" \
```

### Using Ollama (local OpenAI-compatible server) with language parameter
```bash
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_API_KEY=""
python minute_ninja.py path/to/transcript.vtt \
  --model "gemma3:12b-it-qat" \
  --language "portuguese"
```

## Output
The output file will be saved with the format `{input_filename}_summary_{language}_{model_name}.txt` in the same directory as the input file, unless a custom output path is specified with `--output`.

**Output File Naming:**
- **Default**: `meeting_transcript_summary_english_gpt-4.txt`
- **With Custom Output**: Uses the exact path specified in `--output` parameter
- **Model Name Sanitization**: Special characters in model names are replaced with underscores for filesystem compatibility

**Examples:**
```
Input: board_meeting.vtt
Model: gpt-4
Language: portuguese
Output: board_meeting_summary_portuguese_gpt-4.txt

Input: team_sync.vtt  
Model: meta-llama/Llama-4-Scout-17B
Language: english
Output: team_sync_summary_english_meta-llama_Llama-4-Scout-17B.txt

With --output parameter:
Input: any_meeting.vtt
Output: /custom/path/executive_minutes.txt
```

## Supported Languages
The tool supports generating meeting minutes in the following languages:
- **English** - Formal meeting minutes with structured sections
- **Portuguese** - Atas de reunião formais (Brazilian Portuguese)
- **Spanish** - Actas de reunión formales
- **French** - Comptes-rendus de réunion formels
- **German** - Formelle Sitzungsprotokolle

### Prompt Templates
MinuteNinja uses optimized prompt templates for each language. The English template structure includes automatic title and date inference:

```
Based on the transcript below, generate a formal meeting minutes document in English containing:
0. Meeting title and date (if not provided below, infer from context and mark as "Inferred")
1. List of participants identified in the transcript
2. Meeting agenda
3. Main points discussed
4. Decisions made
5. Actions to be taken
6. Conclusions

Meeting Title: [if provided]
Meeting Date: [if provided]
Transcript: {transcript}
```

Similar structured templates are used for all supported languages, ensuring consistent formal output across different linguistic contexts. When title and date are not explicitly provided, the AI will analyze the transcript content and infer appropriate values, clearly marking them as "Inferred" in the output.

## Documentation

## Limitações e Uso Responsável

## Limitations and Responsible Use

- MinuteNinja uses AI to infer information and generate summaries.
- AI may present biases or errors; human review is recommended.
- Sensitive data is processed in accordance with privacy guidelines (LGPD/GDPR).
- Do not use the system for critical decisions without additional validation.

**For suggestions or corrections, please contribute via Pull Request.**

📚 **[Complete Documentation Index](DOCS.md)** - Navigate all project documentation including performance analysis, technical specifications, and usage examples.

## Contributing
Contributions are welcome! To contribute:
1. Open an issue to discuss improvements or report bugs.
2. Fork the project and create a branch for your feature/fix.
3. Submit a pull request detailing your changes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact
Author: Antonio Alisio de Meneses Cordeiro  
Email: alisio.meneses@gmail.com
