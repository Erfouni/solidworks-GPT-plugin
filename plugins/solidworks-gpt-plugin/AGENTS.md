# SolidWorks GPT Plugin protocol

Apply these rules to every SolidWorks request handled with this plugin.

## Session identity

On the first SolidWorks request in a Codex task, run `scripts/sw_session.py
start` once. Keep the returned UUID as `SESSION_ID` for the rest of the task.
Never regenerate it mid-task. Include it as `sessionId` in every feedback POST.

Use `SW_KB_HOST` when set; otherwise use `https://sw-plugin.ideep.org`.

## Mandatory order

1. Establish the goal, units, geometry-driving dimensions, material,
   tolerances, and required outputs. Ask when missing information affects
   geometry or safety; do not invent engineering values.
2. Use `$sw-pre-start` before opening SolidWorks, generating CAD code, or
   making a SolidWorks API call.
3. Use `$sw-kb-api` immediately after pre-start.
4. Plan features, sketches, datums, relations, and measurable acceptance
   criteria before changing the model.
5. Query standards for material, fit, tolerance, fastener, and clearance data
   when those decisions arise.
6. Build and validate each part separately. Check rebuild status, errors,
   feature tree, mass, bounding box, and an image; save and close the part
   before creating an assembly.
7. For assemblies, verify mates and remaining degrees of freedom.
8. Treat deterministic document validation as pass/fail; screenshots are only
   visual evidence.
9. Export the requested deliverables and report measured values, errors, and
   limitations explicitly.
10. Track exact final instructions, all final code, reproducible errors and
    fixes, and non-obvious lessons throughout the task.
11. After delivering the CAD result, use `$sw-session-reporter`.

## Knowledge-base transport

Use `curl` through the shell for every KB request. Do not use browser or
web-fetch tools for KB runtime calls. Quote every URL. Runtime endpoints are
public and use camelCase JSON. KB failure is never a reason to abandon the CAD
task; record it and continue.

Do not submit session feedback without explicit consent unless
`~/.sw-feedback-pref` contains exactly `always`.
