# Security policy

Security fixes are applied to the latest release and the current `main` branch.
Report vulnerabilities privately through the repository's
[security advisory form](https://github.com/Erfouni/solidworks-GPT-plugin/security/advisories/new).
Do not open a public issue until a fix or coordinated disclosure is ready.

Remove API keys, proprietary CAD documents, customer data, and other secrets
from reports. Feedback stays local unless the user explicitly submits it or has
saved the `always` preference. Treat a custom `SW_KB_HOST` as trusted
infrastructure, and validate generated CAD macros and models before production
use.
