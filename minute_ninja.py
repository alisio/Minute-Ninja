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
- Configurable context size and text segmentation
- Customizable inference parameters (temperature, top_p, max_tokens)
- Automatic inference of meeting title and date when not provided

Requirements:
- Python 3.7+
- OpenAI Library
- Access to an LLM service (local Ollama, OpenAI, etc.)

Usage:
    python minute_ninja.py path/to/transcript.txt --model "model-name"

    # With optional parameters
    python minute_ninja.py path/to/transcript.vtt --model "gpt-4" --api-base "https://api.openai.com/v1" --api-key "your-api-key" --language "portuguese" --context-size 32000 --segment-size 400 --temperature 0.3 --top-p 1.0 --title "Weekly Team Meeting" --date "2025-07-21"

    # Using environment variables
    # export LLM_CHAT="gpt-3.5-turbo"
    # export OPENAI_API_BASE="https://api.openai.com/v1"
    # export OPENAI_API_KEY="your-api-key"
    python minute_ninja.py path/to/transcript.txt --language "spanish" --temperature 0.5

Output:
    A file with the same name as the original transcript and '_summary_{language}' suffix will be generated
    in the same folder as the input file.

Example:
    Input:  meeting_15_jun.txt
    Output: meeting_15_jun_summary_english.txt
"""

# List of noises and patterns to remove
FILLERS = [
    r"\b(hmm+|ahn+|uh+|éé+|tipo assim|sabe\?|entende\?|certo\?)\b",
    r"\[inaudible\]", r"\[laughter\]", r"\[pause\]", r"\[.*?\]",  # annotations
]
SPEAKER_PATTERN = r"^([A-ZÁ-Ú][a-zá-ú]+):"  # Ex: John:

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

def segment_by_semantics(text, max_tokens=400):
    """
    Segment text by topics using natural punctuation and token limits.
    """
    # Split by sentences and try to group up to max_tokens (approx. 4 chars/token)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""
    for sent in sentences:
        if len((current + " " + sent).split()) > max_tokens:
            if current.strip():
                chunks.append(current.strip())
            current = sent
        else:
            current += " " + sent
    if current.strip():
        chunks.append(current.strip())
    return chunks

def extract_essential_info(text):
    """
    Identify decisions, action points, conclusions and deadlines.
    """
    # Search for common patterns (can be expanded)
    decisions = re.findall(r"(it was decided that.*?\.|we decided to.*?\.)", text, re.IGNORECASE)
    actions = re.findall(r"(action:.*?\.|responsible:.*?\.|deadline:.*?\.)", text, re.IGNORECASE)
    conclusions = re.findall(r"(we conclude that.*?\.|in summary.*?\.)", text, re.IGNORECASE)
    return {
    "decisions": decisions,
        "actions": actions,
        "conclusions": conclusions
    }

def preprocess_vtt_for_summarization(vtt_content, max_tokens=400):
    """
    Complete preprocessing pipeline for efficient summarization.
    """
    cleaned = clean_vtt_text(vtt_content)
    consolidated = consolidate_speaker_fragments(cleaned)
    segments = segment_by_semantics(consolidated, max_tokens=max_tokens)
    essentials = [extract_essential_info(seg) for seg in segments]
    return segments, essentials

def parse_arguments():
    """
    Process command line arguments.
    """
    parser = argparse.ArgumentParser(description='Generate meeting minutes from a transcript.')
    parser.add_argument('file_path', help='Path to the transcript file')
    parser.add_argument('--model', help='LLM model to use', 
                        default=os.environ.get('LLM_CHAT'))
    parser.add_argument('--api-base', help='OpenAI compatible API base URL', 
                        default=os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1'))
    parser.add_argument('--api-key', help='OpenAI API key', 
                        default=os.environ.get('OPENAI_API_KEY', ''))
    parser.add_argument('--language', help='Language for the generated minutes (english, portuguese, spanish, etc.)', 
                        default='english')
    parser.add_argument('--context-size', type=int, help='Model context size in tokens', 
                        default=32000)
    parser.add_argument('--segment-size', type=int, help='Text segment size in tokens for processing', 
                        default=400)
    parser.add_argument('--temperature', type=float, help='Temperature for text generation (0.0-2.0)', 
                        default=0.3)
    parser.add_argument('--top-p', type=float, help='Top-p value for nucleus sampling (0.0-1.0)', 
                        default=1.0)
    parser.add_argument('--max-tokens', type=int, help='Maximum tokens to generate in response', 
                        default=None)
    parser.add_argument('--title', help='Meeting title (if not provided, will be inferred)', 
                        default=None)
    parser.add_argument('--date', help='Meeting date (if not provided, will be inferred)', 
                        default=None)
    
    args = parser.parse_args()
    
    # File validation
    if not os.path.isfile(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        sys.exit(1)
        
    # Model validation
    if not args.model:
        print("Error: Model not specified. Provide a model via --model argument or set the LLM_CHAT environment variable.")
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
                    segment_size=400, temperature=0.3, top_p=1.0, max_tokens=None, 
                    title=None, date=None):
    """
    Generate minutes from the transcript using the specified LLM model.
    """
    print(f"[STATUS] Starting transcript processing...")
    start_time = time.time()
    
    # Process the transcript
    print("[STATUS] Cleaning and segmenting text...")
    segments, essentials = preprocess_vtt_for_summarization(transcript, max_tokens=segment_size)
    
    # Prepare the prompt with extracted essential information
    print("[STATUS] Extracting essential information...")
    decisions = [item for segment in essentials for item in segment["decisions"]]
    actions = [item for segment in essentials for item in segment["actions"]]
    conclusions = [item for segment in essentials for item in segment["conclusions"]]
    
    # Configure API client
    print(f"[STATUS] Connecting to API ({api_base})...")
    client = OpenAI(
        base_url=api_base,
        api_key=api_key
    )
    
    # Prompt templates 100% no idioma de saída
    lang_prompts = {
        "english": """
Based on the transcript below, generate a formal meeting minutes document in English containing:
0. Meeting title and date (if not provided below, infer from context and mark as "Inferred")
1. List of participants identified in the transcript
2. Meeting agenda
3. Main points discussed
4. Decisions made
5. Actions to be taken
6. Conclusions
""",
        "portuguese": """
Com base na transcrição abaixo, gere uma ata de reunião formal em Português contendo:
0. Título e data da reunião (se não fornecidos abaixo, inferir do contexto e marcar como "Inferido")
1. Lista de participantes identificados na transcrição
2. Pauta da reunião
3. Principais pontos discutidos
4. Decisões tomadas
5. Ações a serem realizadas
6. Conclusões
""",
        "spanish": """
Con base en la transcripción a continuación, genere un acta de reunião formal en Español que contenga:
0. Título y fecha de la reunión (si no se proporcionan a continuación, inferir del contexto y marcar como "Inferido")
1. Lista de participantes identificados en la transcripción
2. Agenda de la reunión
3. Puntos principales discutidos
4. Decisiones tomadas
5. Acciones a realizar
6. Conclusiones
""",
        "french": """
À partir de la transcription ci-dessous, générez un compte-rendu formel de réunion en Français contenant :
0. Titre et date de la réunion (si non fournis ci-dessous, inférer du contexte et marquer comme "Inféré")
1. Liste des participants identifiés dans la transcription
2. Ordre du jour de la réunion
3. Principaux points discutés
4. Décisions prises
5. Actions à entreprendre
6. Conclusions
""",
        "german": """
Basierend auf dem untenstehenden Transkript erstellen Sie ein formelles Sitzungsprotokoll auf Deutsch mit:
0. Titel und Datum der Sitzung (falls nicht unten angegeben, aus dem Kontext ableiten und als "Abgeleitet" markieren)
1. Liste der im Transkript identifizierten Teilnehmer
2. Tagesordnung der Sitzung
3. Wichtigste besprochene Punkte
4. Getroffene Entscheidungen
5. Zu ergreifende Maßnahmen
6. Schlussfolgerungen
""",
    }
    prompt_template = lang_prompts.get(language.lower(), lang_prompts["english"])
    
    # Add title and date information if provided
    title_date_info = ""
    if title and date:
        title_date_info = f"\n\nMeeting Title: {title}\nMeeting Date: {date}\n"
    elif title:
        title_date_info = f"\n\nMeeting Title: {title}\n"
    elif date:
        title_date_info = f"\n\nMeeting Date: {date}\n"
    
    prompt = (
        prompt_template
        + title_date_info
        + f"\n\nTranscript:\n{''.join(segments)}\n\n"
        + (
            f"{'Identified decisions:' if language.lower() == 'english' else ''} {' '.join(decisions)}\n"
            f"{'Identified actions:' if language.lower() == 'english' else ''} {' '.join(actions)}\n"
            f"{'Identified conclusions:' if language.lower() == 'english' else ''} {' '.join(conclusions)}\n"
        )
    )
    
    try:
        print(f"[STATUS] Sending request to model {model}...")
        
        # Prepare API call parameters
        api_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are an assistant specialized in creating precise and well-formatted meeting minutes in {language}."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "top_p": top_p
        }
        
        # Add max_tokens if specified
        if max_tokens:
            api_params["max_tokens"] = max_tokens
        
        response = client.chat.completions.create(**api_params)
        elapsed_time = time.time() - start_time
        print(f"[STATUS] Summary generated successfully! (Time: {elapsed_time:.2f}s)")
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating minutes: {e}")
        sys.exit(1)

def save_summary(summary, input_file_path, language="english"):
    """
    Save the generated minutes to a file with '_summary_{language}.txt' suffix.
    """
    input_path = Path(input_file_path)
    output_file = input_path.parent / f"{input_path.stem}_summary_{language}.txt"
    
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
    print(f"[STATUS] Context size: {getattr(args, 'context_size')}, Segment size: {getattr(args, 'segment_size')}")
    print(f"[STATUS] Temperature: {args.temperature}, Top-p: {getattr(args, 'top_p')}")
    
    # Read the transcript
    transcript = read_transcript(args.file_path)
    
    # Generate the minutes
    summary = generate_summary(
        transcript=transcript, 
        model=args.model, 
        api_base=getattr(args, 'api_base'), 
        api_key=getattr(args, 'api_key'), 
        language=args.language,
        segment_size=getattr(args, 'segment_size'),
        temperature=args.temperature,
        top_p=getattr(args, 'top_p'),
        max_tokens=getattr(args, 'max_tokens'),
        title=args.title,
        date=args.date
    )
    
    # Save the minutes
    save_summary(summary, args.file_path, args.language)
    
    print("[STATUS] Processing completed!")

if __name__ == "__main__":
    main()
