# Job Scam Investigator

Assess potentially fraudulent job advertisements, recruiter messages, and hiring processes using supplied evidence and independent public sources. Separate observations from hypotheses, classify risk and confidence independently, and recommend actions proportionate to the candidate's exposure.

## When to use it
Use screenshots, messages, emails, documents, or public indicators to assess a job offer. Findings are risk assessments, not legal determinations of fraud. Web research and PDF/image reading depend on the host's available tools; unavailable checks must be disclosed.

## Workflow and boundaries
Preserve provenance, extract indicators, compare the recruiting pitch with contextual risk signals, independently verify official channels, and report evidence strength and unresolved gaps. Triage exposure such as shared resumes, identity documents, payments, credentials, verification codes, or installed software.

Do not contact suspects, execute attachments, probe infrastructure, submit forms, make payments, or publish personal evidence. Messaging apps and consumer email addresses alone do not prove fraud. Keep real evidence and non-anonymized reports out of this public repository.

## Optional offline helper
Python 3 is required only for the standard-library text extractor. From the skill folder:

```bash
python scripts/extract_indicators.py input.txt
python scripts/extract_indicators.py --redact < input.txt
python -m unittest discover -s tests -v
```

On Windows PowerShell, use `Get-Content -Raw input.txt | python scripts/extract_indicators.py --redact` for stdin input. The helper extracts email addresses, HTTP(S) URLs, handles, and Brazilian phone numbers; it never opens links or sends data. Phone recognition is heuristic. Redaction masks extracted values for display and does not anonymize the input or guarantee complete removal of personal data.

## Packaging and portability
The security plugin is version 0.1.1. The skill retains its references, offline helper, unit tests, and a fictional example. Version and author metadata live in the plugin manifest. The source package's nested Git history, bytecode caches, standalone README, and standalone CI are excluded.

Claude Code discovers skills within the plugin. Other compatible hosts can use this self-contained skill folder through their supported discovery mechanism; generic hosts can load SKILL.md and its references manually. Reports should use the user's language.
