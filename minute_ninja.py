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

Requirements:
- Python 3.7+
- OpenAI Library
- Access to an LLM service (local Ollama, OpenAI, etc.)

Usage:
    python minute_ninja.py path/to/transcript.txt --model "model-name"

    # With optional parameters
    python minute_ninja.py path/to/transcript.vtt --model "gpt-4" --api-base "https://api.openai.com/v1" --api-key "your-api-key" --language "portuguese"

    # Using environment variables
    # export LLM_CHAT="gpt-3.5-turbo"
    # export OPENAI_API_BASE="https://api.openai.com/v1"
    # export OPENAI_API_KEY="your-api-key"
    python minute_ninja.py path/to/transcript.txt --language "spanish"

Output:
    A file with the same name as the original transcript and '_ata' suffix will be generated
    in the same folder as the input file.

Example:
    Input:  meeting_15_jun.txt
    Output: meeting_15_jun_ata.txt
"""

# List of noises and patterns to remove
FILLERS = [
    r"\b(hmm+|ahn+|uh+|éé+|tipo assim|sabe\?|entende\?|certo\?)\b",
    r"\[inaudible\]", r"\[laughter\]", r"\[pause\]", r"\[.*?\]",  # annotations
]
SPEAKER_PATTERN = r"^([A-ZÁ-Ú][a-zá-ú]+):"  # Ex: John:

def clean_vtt_text(vtt_content):
    """
    Cleans and normalizes VTT transcription text by removing metadata, noise, and speaker identifiers.

    Args:
        vtt_content (str): The raw content of a VTT transcription file.

    Returns:
        str: The cleaned and normalized transcription text, ready for further processing.
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
    Joins fragmented speech from the same speaker into a single segment.

    Args:
        text (str): The transcription text with possible fragmented speaker lines.

    Returns:
        str: The text with speaker fragments consolidated.
    """
    # Simple example: can be expanded to keep speaker names if needed
    return re.sub(r"\s*\n\s*", " ", text)

def segment_by_semantics(text, max_tokens=400):
    """
    Segments text into chunks based on sentence boundaries and a maximum token limit.

    Args:
        text (str): The input text to segment.
        max_tokens (int, optional): Maximum number of tokens per segment. Defaults to 400.

    Returns:
        list of str: List of text segments, each within the token limit.
    """
    # Split by sentences and try to group up to max_tokens (approx. 4 chars/token)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""
    for sent in sentences:
        if len((current + " " + sent).split()) > max_tokens:
            chunks.append(current.strip())
            current = sent
        else:
            current += " " + sent
    if current.strip():
        chunks.append(current.strip())
    return chunks

def extract_essential_info(text):
    """
    Extracts essential meeting information such as decisions, actions, and conclusions from the text.

    Args:
        text (str): The input text to analyze.

    Returns:
        dict: Dictionary with keys 'decisions', 'actions', and 'conclusions', each containing a list of extracted strings.
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
    Complete preprocessing pipeline for VTT content, preparing it for summarization.

    Args:
        vtt_content (str): The raw VTT transcription content.
        max_tokens (int, optional): Maximum number of tokens per segment. Defaults to 400.

    Returns:
        tuple: (segments, essentials)
            segments (list of str): Segmented and cleaned text.
            essentials (list of dict): List of dictionaries with extracted essential info for each segment.
    """
    cleaned = clean_vtt_text(vtt_content)
    consolidated = consolidate_speaker_fragments(cleaned)
    segments = segment_by_semantics(consolidated, max_tokens=max_tokens)
    essentials = [extract_essential_info(seg) for seg in segments]
    return segments, essentials

def parse_arguments():
    """
    Parses and validates command line arguments for the script.

    Returns:
        argparse.Namespace: Parsed arguments with attributes for file path, model, API base, API key, and language.

    Raises:
        SystemExit: If required arguments are missing or invalid.
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
    Reads the transcript file from the given path.

    Args:
        file_path (str): Path to the transcript file.

    Returns:
        str: The content of the transcript file.

    Raises:
        SystemExit: If the file cannot be read.
    """
    print(f"[STATUS] Reading transcript file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def generate_summary(transcript, model, api_base, api_key, language="english"):
    """
    Generates meeting minutes from a transcript using a specified LLM model via OpenAI-compatible API.

    Args:
        transcript (str): The cleaned transcript text.
        model (str): The LLM model name to use.
        api_base (str): The base URL for the OpenAI-compatible API.
        api_key (str): The API key for authentication.
        language (str, optional): Language for the generated minutes. Defaults to "english".

    Returns:
        str: The generated meeting minutes as returned by the LLM.

    Raises:
        SystemExit: If the API call fails.
    """
    print(f"[STATUS] Starting transcript processing...")
    start_time = time.time()

    # Process the transcript
    print("[STATUS] Cleaning and segmenting text...")
    # Segment with a very conservative max_tokens to avoid API limits (1500 words ~ 3000 tokens)
    max_tokens_per_segment = 1500
    segments, essentials = preprocess_vtt_for_summarization(transcript, max_tokens=max_tokens_per_segment)

    # Prepare prompt templates
    lang_prompts = {
        "english": """
Based on the transcript below, generate a formal meeting minutes document in English containing:
1. List of participants identified in the transcript
2. Meeting agenda
3. Main points discussed
4. Decisions made
5. Actions to be taken
6. Conclusions
""",
        "portuguese": """
Com base na transcrição abaixo, gere uma ata de reunião formal em Português contendo:
1. Lista de participantes identificados na transcrição
2. Pauta da reunião
3. Principais pontos discutidos
4. Decisões tomadas
5. Ações a serem realizadas
6. Conclusões
""",
        "spanish": """
Con base en la transcripción a continuación, genere un acta de reunião formal en Español que contenga:
1. Lista de participantes identificados en la transcripción
2. Agenda de la reunión
3. Puntos principales discutidos
4. Decisiones tomadas
5. Acciones a realizar
6. Conclusiones
""",
        "french": """
À partir de la transcription ci-dessous, générez un compte-rendu formel de réunion en Français contenant :
1. Liste des participants identifiés dans la transcription
2. Ordre du jour de la réunion
3. Principaux points discutés
4. Décisions prises
5. Actions à entreprendre
6. Conclusions
""",
        "german": """
Basierend auf dem untenstehenden Transkript erstellen Sie ein formelles Sitzungsprotokoll auf Deutsch mit:
1. Liste der im Transkript identifizierten Teilnehmer
2. Tagesordnung der Sitzung
3. Wichtigste besprochene Punkte
4. Getroffene Entscheidungen
5. Zu ergreifende Maßnahmen
6. Schlussfolgerungen
"""
    }
    prompt_template = lang_prompts.get(language.lower(), lang_prompts["english"])

    # Configure API client
    print(f"[STATUS] Connecting to API ({api_base})...")
    client = OpenAI(
        base_url=api_base,
        api_key=api_key
    )

    all_summaries = []
    for idx, segment in enumerate(segments):
        print(f"[STATUS] Sending request to model {model} for segment {idx+1}/{len(segments)}...")
        # Extract essentials for this segment
        essentials_seg = extract_essential_info(segment)
        decisions = essentials_seg["decisions"]
        actions = essentials_seg["actions"]
        conclusions = essentials_seg["conclusions"]
        prompt = (
            prompt_template
            + f"\n\nTranscript:\n{segment}\n\n"
            + (
                f"{'Identified decisions:' if language.lower() == 'english' else ''} {' '.join(decisions)}\n"
                f"{'Identified actions:' if language.lower() == 'english' else ''} {' '.join(actions)}\n"
                f"{'Identified conclusions:' if language.lower() == 'english' else ''} {' '.join(conclusions)}\n"
            )
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"You are an assistant specialized in creating precise and well-formatted meeting minutes in {language}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            all_summaries.append(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating minutes for segment {idx+1}: {e}")
            sys.exit(1)

    elapsed_time = time.time() - start_time
    print(f"[STATUS] Summary generated successfully! (Time: {elapsed_time:.2f}s)")
    # Join all summaries with clear separation
    return '\n\n---\n\n'.join(all_summaries)
def save_summary(summary, input_file_path, language="english"):
    """
    Saves the generated meeting minutes to a file with a language-specific suffix.

    Args:
        summary (str): The generated meeting minutes.
        input_file_path (str): Path to the original transcript file.
        language (str, optional): Language of the minutes, used in the output filename. Defaults to "english".

    Raises:
        SystemExit: If the file cannot be saved.
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
    Main function that coordinates the execution flow of the script.

    Steps:
        1. Parses command line arguments.
        2. Reads the transcript file.
        3. Generates meeting minutes using an LLM.
        4. Saves the generated minutes to a file.
    """
    print("[STATUS] Starting processing...")
    
    # Process arguments
    args = parse_arguments()
    print(f"[STATUS] Settings: model={args.model}, language={args.language}, API={args.api_base}")
    
    # Read the transcript
    transcript = read_transcript(args.file_path)
    
    # Generate the minutes
    summary = generate_summary(transcript, args.model, args.api_base, args.api_key, args.language)
    
    # Save the minutes
    save_summary(summary, args.file_path, args.language)
    
    print("[STATUS] Processing completed!")

if __name__ == "__main__":
    main()
