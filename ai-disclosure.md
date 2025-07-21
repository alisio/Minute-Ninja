# AI Disclosure

This document describes the use of Artificial Intelligence (AI) in the MinuteNinja project, providing transparency and guidance for users and contributors.

## Where AI Is Used
- Meeting minutes are generated using OpenAI-compatible language models (e.g., GPT-4, Llama, DeepSeek, Qwen, Gemma).
- AI is responsible for summarizing, inferring meeting titles and dates, and extracting key information from transcripts.

## Models and Providers
- The system supports multiple LLM providers: OpenAI, DeepInfra, Ollama (local), and others.
- Model selection is configurable by the user.

## Data Processing and Privacy
- Transcripts provided by users are processed by AI models to generate summaries.
- Sensitive data is handled in accordance with privacy guidelines (LGPD/GDPR).
- No user data is stored or shared by MinuteNinja itself; check provider policies for API usage.

## Limitations and Risks
- AI-generated content may contain errors, omissions, or biases.
- Human review is strongly recommended before using generated minutes for critical decisions.
- The system may infer information (e.g., meeting title/date) that is not explicitly present in the transcript.

## Responsible Use
- Do not rely solely on AI-generated content for legal, financial, or other critical decisions.
- Always validate and review outputs before publication or distribution.

## Updates and Monitoring
- Models and prompts may be updated to improve quality and reduce bias.
- Feedback and contributions are welcome via Pull Request.

## Contact
For questions or concerns about AI usage in MinuteNinja, contact the project author:
- Antonio Alisio de Meneses Cordeiro
- Email: alisio.meneses@gmail.com
