# Investigation playbook

## Source boundaries
- **Supplied evidence:** facts observable within user-provided files/messages.
- **Independent verification:** official career pages, verified employer representatives, relevant government guidance, established reporting platforms.
- **Public complaints:** leads or corroboration, *not* adjudicated proof of criminal conduct.
- **Analysis:** reasoned inference explicitly marked as such.

## Safe open-source checks
1. Normalize indicators for searching but preserve the exact original string and its source.
2. Search quoted phrases of unusual recruiting text, exact sender address, Telegram handle, phone and domain separately.
3. Check whether identical pitches appear with different company or recruiter names. Note dates and direct links.
4. Navigate to employer and staffing company websites independently (not using supplied recruitment links), compare job IDs and publicly documented recruiting practices.
5. Check whether the specific role, office, agency partnership or course is independently confirmed. If not, write “not independently verified,” not “does not exist.”
6. Review email sender headers (SPF/DKIM/DMARC/Received) **only if original raw headers are available**. Passing checks authenticate a sending domain, not the truth of the employment offer.
7. Keep evidence table: indicator, observed text, source, independent corroboration, confidence, caveat.

## Safety limits
Never interact with a suspect, probe infrastructure, download executable attachments, visit suspicious short links, bypass access controls, or perform intrusive OSINT. Ask before publishing or forwarding any data. Prioritize Brazilian context when relevant (official company careers, consumidor.gov.br, CERT.br guidance, police reporting if financial loss).
