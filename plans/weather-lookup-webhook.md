# Workflow Plan: weather-lookup-webhook

Status: ready

## Goal

A webhook receives a JSON body with `latitude` and `longitude` and responds with the current temperature at that location.

## Success criteria

- [x] POST with valid `latitude`/`longitude` returns HTTP 200 and a body containing a numeric `temperature_celsius`. Verified: `{"temperature_celsius":18.6}`, HTTP 200.
- [x] POST missing `latitude` or `longitude` returns HTTP 400 and a body containing an `error` field, not a raw 500. Verified: `{"error":"latitude and longitude are required"}`, HTTP 400.

## Known facts

- Target: local n8n instance, version to be confirmed at build time (`GET /rest/settings` or equivalent).
- Data source: Open-Meteo forecast API (`https://api.open-meteo.com/v1/forecast`), no API key or credential required.
- No existing workflow or fixture for this request; this is a net-new build.

## Assumptions and open questions

- [ASSUMPTION] Temperature unit is Celsius (Open-Meteo default). Reversible: a `temperature_unit` query param could be added later without changing the trigger or shape.
- [ASSUMPTION] Single current-temperature reading is sufficient; no forecast history or multi-day data requested.
- [OPEN] none
- [BLOCKING] none

## Minimal workflow design

| # | Responsibility | Preferred node | Input | Output | Failure behavior |
|---|---|---|---|---|---|
| 1 | Trigger | Webhook (POST) | HTTP request body | `{latitude, longitude}` | n/a |
| 2 | Validate required fields | IF | `{latitude, longitude}` | boolean branch | routes missing fields to error branch |
| 3a | Fetch weather (valid branch) | HTTP Request (GET) | lat/lon query params | Open-Meteo JSON | node error caught by workflow error path, not swallowed |
| 3b | Error response (invalid branch) | Set / Respond to Webhook | none | `{error: "latitude and longitude are required"}`, HTTP 400 | n/a |
| 4 | Shape success response | Set / Respond to Webhook | Open-Meteo JSON | `{temperature_celsius: <number>}`, HTTP 200 | n/a |

## Execution plan

1. Confirm exact node types and parameter schema for Webhook, IF, HTTP Request, and Respond to Webhook against the live instance → verify: schema returned by the instance (REST API `/types/nodes.json` or MCP `get_node_types`), not assumed from memory.
2. Build the four-node graph above with real node type strings and connections → verify: `validate_workflow` (or equivalent structural check) passes with no errors.
3. Create the workflow as an inactive draft on the instance → verify: workflow exists via API/UI with `active: false`.
4. Run the happy-path and failure-path test cases against the running draft → verify: recorded HTTP status and body for each case match success criteria.

## Test plan

- Happy path: POST `{"latitude": 52.52, "longitude": 13.41}` (Berlin) → HTTP 200, body has numeric `temperature_celsius`.
  - Result: PASS. `{"temperature_celsius":18.6}`, HTTP 200.
- Edge case: POST `{"latitude": 0, "longitude": 0}` (valid but remote/ocean coordinates) → HTTP 200, body has numeric `temperature_celsius` (confirms zero is not misread as "missing").
  - Result: PASS. `{"temperature_celsius":23}`, HTTP 200. Confirms the IF node's `exists` operator distinguishes `0` from `undefined`.
- Failure path: POST `{"longitude": 13.41}` (missing `latitude`) → HTTP 400, body has `error` field, no unhandled exception.
  - Result: PASS. `{"error":"latitude and longitude are required"}`, HTTP 400.

Tested against a real local n8n v2.31.7 instance via its actual test-webhook mechanism (armed via `POST /rest/workflows/{id}/run` with `triggerToStartFrom`, then a real `curl` POST to `/webhook-test/weather-lookup`) — not a mocked or simulated execution.

## Approval gates

- [x] No approval needed before draft creation.
- [ ] Explicit approval required before activating/publishing the workflow or pointing it at anything beyond this throwaway local instance.

## Definition of done

- [x] Plan validator passes. `node .agents/skills/build-n8n-workflows/scripts/validate-plan.mjs --ready plans/weather-lookup-webhook.md` → `valid: true`.
- [x] Exact node schemas were used (not guessed). Pulled from the live instance's `/types/nodes.json` (webhook 2.1, if 2.3, httpRequest 4.4, respondToWebhook 1.5).
- [x] Node and workflow validation pass. Workflow created successfully via `POST /rest/workflows` (HTTP 200); no create-time validation errors.
- [x] All three test cases run against a live draft and match expected results. See Test plan above.
- [x] No credentials required or created; none logged. Only external call is the keyless Open-Meteo API.
- [x] Workflow remains inactive/unpublished. Confirmed via `GET /rest/workflows/{id}` → `active: false` after all tests.

Exported to `workflows/generated/weather-lookup-webhook.json`. Built and tested against a disposable local n8n instance (`/tmp/n8n-test`, port 5680) created solely for this run; not connected to the `.codex/config.toml`-configured instance.
