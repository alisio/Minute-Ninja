
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
- Topic segmentation with token limits
- Extracts essential information (decisions, actions, conclusions)
- Generates formal minutes in multiple languages

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
Additional parameters:
- `--api-base`: OpenAI API base URL (e.g., https://api.openai.com/v1)
- `--api-key`: API key
- `--language`: Language for the generated minutes (english, portuguese, spanish, etc.)

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

### Environment Variables
For convenience, set these environment variables:
```bash
# For OpenAI API
export OPENAI_API_BASE="https://api.openai.com/v1"
export OPENAI_API_KEY="your-api-key"

# For DeepInfra API
export OPENAI_API_BASE="https://api.deepinfra.com/v1/openai/"
export OPENAI_API_KEY="your-deepinfra-key"

# For Ollama Local
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_API_KEY=""
```

## Examples
### Basic usage
```bash
python minute_ninja.py path/to/transcript.vtt --model "gpt-4"
```

### Using top-performing models
```bash
# Fastest overall (DeepInfra API)
python minute_ninja.py transcript.vtt \
  --model "meta-llama/Llama-4-Scout-17B-16E-Instruct" \
  --api-base "https://api.deepinfra.com/v1/openai/" \
  --api-key "YOUR_DEEPINFRA_KEY"

# Best local model (zero cost)
python minute_ninja.py transcript.vtt \
  --model "deepseek-r1:1.5b" \
  --api-base "http://localhost:11434/v1" \
  --language "english"
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
The output file will be saved in the same directory as the input file, with the suffix `_summary_<language>.txt`.

## Supported Languages
The tool supports generating meeting minutes in the following languages:
- **English** - Formal meeting minutes with structured sections
- **Portuguese** - Atas de reunião formais (Brazilian Portuguese)
- **Spanish** - Actas de reunión formales
- **French** - Comptes-rendus de réunion formels
- **German** - Formelle Sitzungsprotokolle

### Prompt Templates
MinuteNinja uses optimized prompt templates for each language. The English template structure is:

```
Based on the transcript below, generate a formal meeting minutes document in English containing:
1. List of participants identified in the transcript
2. Meeting agenda
3. Main points discussed
4. Decisions made
5. Actions to be taken
6. Conclusions

Transcript: {transcript}
```

Similar structured templates are used for all supported languages, ensuring consistent formal output across different linguistic contexts.

## Documentation
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
