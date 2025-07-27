import re
import argparse
import os
import sys
import time
from pathlib import Path
from openai import OpenAI

"""
MinuteNinja: VTT Transcription Processor and Meeting Minutes Generator
========================================================

Author: Antonio Alisio de Meneses Cordeiro. alisio.meneses@gmail.com

This script processes transcription files (VTT or text) and generates meeting minutes
formatted using a large language model (LLM) through an OpenAI-compatible API.

Features:
- Cleaning and preprocessing of transcriptions
- Extraction of essential information (decisions, actions, conclusions)
- Generation of formatted meeting minutes
- Support for various LLM models compatible with OpenAI API
- Support for multiple languages for the generated minutes
- Configurable context size and text segmentation using a Map-Reduce strategy
- Customizable inference parameters (temperature, top_p, max_tokens)
- Automatic inference of meeting title and date when not provided
"""

# List of noises and patterns to remove
FILLERS = [
    r"\b(hmm+|ahn+|uh+|éé+|tipo assim|sabe\?|entende\?|certo\?)\b",
    r"\[inaudible\]", r"\[laughter\]", r"\[pause\]", r"\[.*?\]",  # annotations
]
SPEAKER_PATTERN = r"^([A-ZÁ-Ú][a-zá-ú]+):"  # Ex: John:

# --- PROMPT TEMPLATES (Re-structured for System/User roles) ---

# Prompts for the "Map" step (summarizing individual chunks)
MAP_PROMPTS = {
    "english": "You are an assistant that extracts key information. From the following segment of a meeting transcript, please summarize the main points, decisions made, and actions assigned. Be concise and factual. SEGMENT: \n\n",
    "portuguese": "Você é um assistente que extrai informações chave. Do segmento de transcrição de reunião a seguir, por favor, resuma os pontos principais, decisões tomadas e ações atribuídas. Seja conciso e factual. SEGMENTO: \n\n",
    "spanish": "Eres un asistente que extrae información clave. Del siguiente segmento de una transcripción de reunión, por favor, resume los puntos principales, las decisiones tomadas y las acciones asignadas. Sé conciso y fáctico. SEGMENTO: \n\n",
    "french": "Vous êtes un assistant qui extrait des informations clés. À partir du segment suivant d'une transcription de réunion, veuillez résumer les points principaux, les décisions prises et les actions attribuées. Soyez concis et factuel. SEGMENT: \n\n",
    "german": "Sie sind ein Assistent, der wichtige Informationen extrahiert. Fassen Sie aus dem folgenden Abschnitt eines Besprechungsprotokolls die wichtigsten Punkte, getroffenen Entscheidungen und zugewiesenen Maßnahmen zusammen. Seien Sie prägnant und sachlich. SEGMENT: \n\n"
}

# Prompts for the "Reduce" step (creating the final minutes from summaries)
REDUCE_PROMPTS = {
    "english": {
        "system": "You are a highly skilled AI assistant specializing in creating neutral, objective, and factual meeting minutes in English. Your primary goal is to accurately synthesize a final document from a series of summaries.",
        "user": """**Task:** Based on the collection of meeting summaries provided below, generate a single, consolidated, and formal meeting minutes document.

**Instructions and Constraints:**
1.  **Synthesize, Don't Repeat:** Combine the information from the summaries into a coherent final document. Remove redundancies.
2.  **Neutrality and Objectivity:** Adhere strictly to the explicit information. Do not infer emotions or hierarchy. Avoid subjective language (e.g., "heated debate," "brilliant idea").
3.  **Participant Identification:** List all participants whose names are mentioned across the summaries.
4.  **Decisions vs. Discussions:** Consolidate all decisions into the "Decisions Made" section. All other points go into "Main Points Discussed".
5.  **Structure:** Generate the output in the following format:
    *   **Meeting Title:** {title}
    *   **Date:** {date}
    *   **Participants:** (Bulleted list)
    *   **Agenda:** (If explicitly stated)
    *   **Main Points Discussed:** (Neutral summary)
    *   **Decisions Made:** (List of explicit agreements)
    *   **Actions to be Taken:** (List with assigned owner)
    *   **Conclusions:** (Summarize only if a conclusion is present in the summaries. Otherwise, state "No formal conclusion stated.")

**Input Summaries:**
{input_text}
"""
    },
    "portuguese": {
        "system": "Você é um assistente de IA altamente qualificado, especializado em criar atas de reunião neutras, objetivas e factuais em Português. Seu objetivo principal é sintetizar com precisão um documento final a partir de uma série de resumos.",
        "user": """**Tarefa:** Com base na coleção de resumos de reunião fornecida abaixo, gere um único documento de ata de reunião, consolidado e formal.

**Instruções e Restrições:**
1.  **Sintetize, Não Repita:** Combine as informações dos resumos em um documento final coerente. Remova redundâncias.
2.  **Neutralidade e Objetividade:** Atenha-se estritamente à informação explícita. Não infira emoções ou hierarquia. Evite linguagem subjetiva (ex: "debate acalorado", "ideia brilhante").
3.  **Identificação de Participantes:** Liste todos os participantes cujos nomes são mencionados nos resumos.
4.  **Decisões vs. Discussões:** Consolide todas as decisões na seção "Decisões Tomadas". Todos os outros pontos vão para "Principais Pontos Discutidos".
5.  **Estrutura:** Gere a saída no seguinte formato:
    *   **Título da Reunião:** {title}
    *   **Data:** {date}
    *   **Participantes:** (Lista com marcadores)
    *   **Pauta:** (Se explicitamente declarada)
    *   **Principais Pontos Discutidos:** (Resumo neutro)
    *   **Decisões Tomadas:** (Lista de acordos explícitos)
    *   **Ações a Serem Realizadas:** (Lista com responsável atribuído)
    *   **Conclusões:** (Resuma apenas se uma conclusão estiver presente nos resumos. Caso contrário, indique "Nenhuma conclusão formal declarada.")

**Resumos de Entrada:**
{input_text}
"""
    },
    # Spanish, French, German prompts would follow the same structure
    # For brevity, they are omitted here but would be translated and added in a real implementation.
}
# Fallback to English if a language is not fully defined
REDUCE_PROMPTS.setdefault("spanish", REDUCE_PROMPTS["english"])
REDUCE_PROMPTS.setdefault("french", REDUCE_PROMPTS["english"])
REDUCE_PROMPTS.setdefault("german", REDUCE_PROMPTS["english"])


def clean_vtt_text(vtt_content):
    """
    Remove metadata, noise and normalize VTT text.
    """
    # Remove timestamps, cue numbers and headers
    lines = vtt_content.splitlines()
    text_lines = []
    for line in lines:
        if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} -->", line):
            continue
        if re.match(r"^\d+$", line):
            continue
        if line.strip().lower().startswith("webvtt"):
            continue
        text_lines.append(line)
    text = "\n".join(text_lines)

    # Remove noise
    for pattern in FILLERS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove repetitive speaker identifiers
    text = re.sub(SPEAKER_PATTERN, r"\1:", text, flags=re.MULTILINE)
    text = re.sub(r"^([A-ZÁ-Ú][a-zá-ú]+):\s*", "", text, flags=re.MULTILINE)

    # Normalize spaces and capitalization
    text = re.sub(r"\s+", " ", text)
    text = text.strip().capitalize()
    return text

def consolidate_speaker_fragments(text):
    """
    Join fragmented speech from the same speaker.
    """
    # Simple example: can be expanded to keep speaker names if needed
    return re.sub(r"\s*\n\s*", " ", text)
    
def chunk_text(text, chunk_size=400):
    """
    Splits text into chunks of a specified size based on word count.
    """
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def parse_arguments():
    """
    Process command line arguments.
    """
    parser = argparse.ArgumentParser(description='Generate meeting minutes from a transcript.')
    parser.add_argument('file_path', help='Path to the transcript file')
    parser.add_argument('--model', help='LLM model to use', 
                        default=os.environ.get('OPENAI_MODEL'))
    parser.add_argument('--api-base', help='OpenAI compatible API base URL', 
                        default=os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1'))
    parser.add_argument('--api-key', help='OpenAI API key', 
                        default=os.environ.get('OPENAI_API_KEY', ''))
    parser.add_argument('--language', help='Language for the generated minutes (english, portuguese, spanish, etc.)', 
                        default='english')
    parser.add_argument('--context-size', type=int, help='Model context size in tokens (for reference)', 
                        default=32000)
    parser.add_argument('--segment-size', type=int, help='Word count for each text chunk in the Map-Reduce process', 
                        default=2000)  # Default segment size for chunking
    parser.add_argument('--temperature', type=float, help='Temperature for text generation (0.0-2.0)', 
                        default=0.2)
    parser.add_argument('--top-p', type=float, help='Top-p value for nucleus sampling (0.0-1.0)', 
                        default=1.0)
    parser.add_argument('--max-tokens', type=int, help='Maximum tokens to generate in the final response', 
                        default=2048)
    parser.add_argument('--title', help='Meeting title (if not provided, will be inferred)', 
                        default=None)
    parser.add_argument('--date', help='Meeting date (if not provided, will be inferred)', 
                        default=None)
    parser.add_argument('--output', help='Custom output file path (if not provided, will be generated automatically)', 
                        default=None)
    
    args = parser.parse_args()
    
    # File validation
    if not os.path.isfile(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        sys.exit(1)
        
    # Model validation
    if not args.model:
        print("Error: Model not specified. Provide a model via --model argument or set the OPENAI_MODEL environment variable.")
        sys.exit(1)
        
    return args

def read_transcript(file_path):
    """
    Read the transcript file.
    """
    print(f"[STATUS] Reading transcript file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def generate_summary(transcript, model, api_base, api_key, language="english", 
                    segment_size=500, temperature=0.2, top_p=1.0, max_tokens=2048, 
                    title=None, date=None):
    """
    Generate minutes using a Map-Reduce strategy to handle long transcripts.
    """
    print(f"[STATUS] Starting transcript processing with Map-Reduce strategy...")
    start_time = time.time()
    
    # The original script's preprocessing is kept as requested.
    cleaned_transcript = clean_vtt_text(transcript)
    full_text = consolidate_speaker_fragments(cleaned_transcript)

    # Configure API client
    print(f"[STATUS] Connecting to API ({api_base})...")
    client = OpenAI(
        base_url=api_base,
        api_key=api_key
    )

    # --- MAP STEP ---
    print(f"[STATUS] MAP: Splitting transcript into chunks of ~{segment_size} words.")
    chunks = chunk_text(full_text, chunk_size=segment_size)
    
    chunk_summaries = []
    map_prompt_template = MAP_PROMPTS.get(language.lower(), MAP_PROMPTS["english"])
    
    for i, chunk in enumerate(chunks):
        print(f"[STATUS] MAP: Processing chunk {i+1}/{len(chunks)}...")
        map_prompt = map_prompt_template + chunk
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": map_prompt}],
                temperature=temperature,
            )
            summary = response.choices[0].message.content
            chunk_summaries.append(summary)
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            chunk_summaries.append(f"[Error summarizing chunk {i+1}]")

    # --- REDUCE STEP ---
    print(f"[STATUS] REDUCE: Consolidating {len(chunk_summaries)} summaries into final minutes...")
    combined_summaries = "\n\n---\n\n".join(chunk_summaries)
    
    prompt_data = REDUCE_PROMPTS.get(language.lower(), REDUCE_PROMPTS["english"])
    system_message = prompt_data["system"]
    user_prompt_template = prompt_data["user"]

    # Fill in the final template
    final_user_prompt = user_prompt_template.format(
        title=title if title else "To be inferred",
        date=date if date else "To be inferred",
        input_text=combined_summaries
    )
    
    try:
        print(f"[STATUS] REDUCE: Sending final request to model {model}...")
        api_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": final_user_prompt}
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
        
        response = client.chat.completions.create(**api_params)
        elapsed_time = time.time() - start_time
        print(f"[STATUS] Summary generated successfully! (Time: {elapsed_time:.2f}s)")
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during final generation: {e}")
        sys.exit(1)


def sanitize_filename(filename):
    """
    Sanitize a string to be safe for use as a filename on Linux, Windows, and macOS.
    """
    # Replace invalid characters with underscores
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Handle reserved names on Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    if sanitized.upper() in reserved_names:
        sanitized = f"{sanitized}_model"
    
    # Limit length to prevent filesystem issues
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    # Ensure we don't end with a dot (Windows issue)
    sanitized = sanitized.rstrip('.')
    
    return sanitized if sanitized else "unknown_model"

def save_summary(summary, input_file_path, language="english", model_name="", custom_output_path=None):
    """
    Save the generated minutes to a file with '_summary_{language}_{model}.txt' suffix.
    If custom_output_path is provided, use that instead of generating the filename.
    """
    if custom_output_path:
        # Use custom output path
        output_file = Path(custom_output_path)
        # Ensure the directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Generate filename automatically
        input_path = Path(input_file_path)
        sanitized_model = sanitize_filename(model_name) if model_name else "unknown_model"
        output_file = input_path.parent / f"{input_path.stem}_summary_{language}_{sanitized_model}.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"[STATUS] Minutes saved successfully to: {output_file}")
    except Exception as e:
        print(f"Error saving minutes: {e}")
        sys.exit(1)

def main():
    """
    Main function that coordinates the execution flow.
    """
    print("[STATUS] Starting processing...")
    
    # Process arguments
    args = parse_arguments()
    print(f"[STATUS] Settings: model={args.model}, language={args.language}, API={args.api_base}")
    print(f"[STATUS] Context size: {args.context_size}, Segment word count: {args.segment_size}")
    print(f"[STATUS] Temperature: {args.temperature}, Top-p: {args.top_p}")
    
    # Read the transcript
    transcript = read_transcript(args.file_path)
    
    # Generate the minutes
    summary = generate_summary(
        transcript=transcript, 
        model=args.model, 
        api_base=args.api_base, 
        api_key=args.api_key, 
        language=args.language,
        segment_size=args.segment_size,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        title=args.title,
        date=args.date
    )
    
    # Save the minutes
    save_summary(summary, args.file_path, args.language, args.model, args.output)
    
    print("[STATUS] Processing completed!")

if __name__ == "__main__":
    main()