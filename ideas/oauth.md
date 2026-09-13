[ User Browser ]          [ Your SaaS App ]          [ Meta Authorization Server ]
       │                          │                               │
       │─── 1. Click "Connect" ──>│                               │
       │                          │─── 2. Redirect to Meta Auth ─>│
       │<── 3. Show Permission Prompt (Allow App to Access IG) ───│
       │                          │                               │
       │─── 4. User Clicks Allow ────────────────────────────────>│
       │                          │                               │
       │<── 5. Redirect with Temp Auth Code (?code=XYZ123) ───────│
       │                          │                               │
       │─── 6. Send Auth Code ───>│                               │
       │                          │─── 7. Exchange Code for Token ─>│
       │                          │<── 8. Return Page Access Token │
       │                          │                               │
       │                          │─── 9. Save Token in DB ──┐    │
       │                          │<── 10. Connection Success┘    │
       │<── 11. Dashboard Ready ──│                               │