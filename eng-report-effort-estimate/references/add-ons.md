# Standard Add-Ons

Components clients rarely ask for but that consistently increase product value. The transcripts won't mention them — the agent proposes them. Add-ons are the one sanctioned exception to extract-don't-invent: always labeled as ForwardPath proposals, never mixed into client-requested scope.

No standard hour baselines — price each per project, presented in the Step 0.3 price-impact format.

## Baked-in defaults

Included in every estimate unless the user explicitly drops them:

| Component | Applies to | What it is |
|---|---|---|
| Feature flagging | Every app | Per-user/per-org toggles to turn features on or off — supports phased rollout, UAT gating, and per-client tailoring |
| AI Gateway — Portkey AI (open source) | Every app with AI features | Central LLM routing: retries, fallbacks, caching, and cost/usage tracking |

## Offered when relevant

Propose when the trigger fits; user decides build / offer / skip.

| Component | Offer when | Notes |
|---|---|---|
| In-app API documentation | The app's API is consumed directly by the client or third-party tools | Docs page inside the app (e.g. generated OpenAPI reference) |
| Help center | Non-trivial user base | In-app help articles; optionally an AI help agent that answers from the help content |
| AI cost dashboard | AI-heavy apps | Token/cost per user and feature — pairs with the AI gateway |
| Admin console + RBAC | Multiple user types or permission levels | User management, roles, per-org settings |
| Audit log | Compliance-sensitive domains or multi-user editing | Who did what, when |
| Usage analytics | Client leadership will ask "is anyone using this?" | Product usage dashboard |
| Notifications | Workflow- or status-driven apps | Email + in-app notification infrastructure |
| Data export | Reporting-heavy apps | CSV/Excel export, scheduled reports |
| Onboarding tour | Self-serve users | First-run guidance |
