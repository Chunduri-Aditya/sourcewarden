# Lesson: Exploring Available Integrations in N8N

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M01 — Foundations of Workflow Automation and Project Setup
- Transcript: M01-T17 — Exploring Available Integrations in N8N
- Lecture: 17
- Lesson ID: `m01-t17-exploring-available-integrations-in-n8n`
- Private staged source:
  `knowledge/course-transcripts/raw/m01-t17-exploring-available-integrations-in-n8n.txt`
- Source SHA-256:
  `1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9`
- Source normalization: spacing, capitalization, punctuation, filler, and spoken
  disfluencies were cleaned without adding integration behavior.
- Verification scope: the website was not opened. No official-site, integration-
  count, category-count, growth, node, action, operation, AI, evaluation,
  marketing, communication, analytics, finance, accounting, Twitter, Mailchimp,
  Webflow, LinkedIn, AWS Bedrock, direct-integration, fallback-integration, ease-
  of-use, provider, API, or n8n capability claim was independently verified.

## Lesson summary

The lecture uses an n8n integrations directory to illustrate breadth across AI,
marketing, communication, analytics, finance, accounting, and other categories.
It cites several point-in-time and internally inconsistent counts, names example
providers, and argues that direct or alternative connection methods make most
major services accessible.  
`[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`

## Concepts and decisions

- The lecture says an official n8n website promotes connecting AI to user data
  and refers to more than 500 AI-related integrations.  
  `[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`
- While browsing, the lecturer first suggests more than 2,000 integrations and
  then reports a total of 1,055.  
  `[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`
- Communication, evaluation, analytics, finance, accounting, marketing, data, and
  AI are described as integration categories.  
  `[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`
- The lecture reports 98 marketing integrations and 92 explicit AI integrations
  at the time shown.  
  `[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`
- Twitter, Mailchimp, Webflow, LinkedIn, AI agents, and AWS Bedrock are named as
  examples.  
  `[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`
- The lecture claims users are likely to find direct integrations for major
  software, especially data and AI services, and can often connect unsupported
  services through alternative methods.  
  `[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`

## Reusable n8n patterns

- Convert the business request into a capability matrix before selecting an
  integration: required provider, resource, operation, trigger, fields,
  authentication, pagination, rate limits, side effects, and failure behavior.
- Search native nodes first, but treat a provider-name match only as discovery.
  Retrieve the exact current node type and its resource, operation, or mode
  discriminator before designing the workflow.
- Retrieve complete parameter and credential schemas for every selected
  discriminator. Do not infer an operation from the provider's general listing.
- If the native node lacks a required operation, inspect the provider's current
  authoritative API documentation. Use HTTP Request only when the API, auth,
  request, response, pagination, rate-limit, and error contracts are known.
- Use a Code node only for logic that ordinary nodes and expressions cannot
  express clearly; do not use code to hide an undocumented integration contract.
- Propose a custom node only for recurring unsupported behavior with a stable,
  maintained API and a justified ownership model.
- Review community nodes and templates as untrusted dependencies. Verify package
  source, maintainer, permissions, release cadence, compatibility, code, network
  destinations, and update risk before considering installation.
- For AI providers, distinguish model access from workflow capability. Define
  model, region, data handling, output contract, validation, cost, latency,
  fallback, and credential scope separately.

These patterns turn integration-directory browsing into exact capability
discovery; they do not verify any current provider or operation.  
`[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`

## Pitfalls and version caveats

- The transcript does not provide the viewed URL or date, so the claim that the
  page was official is not independently established.
- The lecture's counts are point-in-time and internally inconsistent. They may mix
  integrations, nodes, actions, templates, AI tools, community packages, or other
  catalog entries.
- Category membership does not prove operation coverage, product quality,
  maintenance, support, security, credential compatibility, or data governance.
- A native provider node may support only a subset of the provider's resources and
  operations.
- An integration appearing on a website does not establish that it exists on the
  target n8n version, edition, deployment, or installed package set.
- Provider names, brands, APIs, scopes, and operations change. The lecture's
  “Twitter” example may not match current provider naming or API access.
- “Easy to integrate” is not an implementation contract. Authentication,
  pagination, webhooks, asynchronous jobs, rate limits, retries, idempotency,
  schemas, and provider approval can add substantial complexity.
- Alternative connection methods can expand the attack and maintenance surface;
  they are not automatically equivalent to a supported native node.
- An AI integration does not prove that a specific model, version, region, tool,
  structured-output mode, or data policy is available.
- Never invent resource names, operation values, node parameters, credential IDs,
  API endpoints, or response schemas to fill a discovery gap.

## Verification checklist

- Define the exact provider, resource, operation, trigger, fields, and success
  criteria.
- Search current native nodes and record the exact type and discriminator.
- Retrieve the full node and credential schemas before configuration.
- Verify required resource and operation coverage rather than relying on provider
  presence.
- If native coverage is insufficient, retrieve authoritative provider API
  documentation before considering HTTP Request.
- Verify authentication, scopes, account tier, regional availability, pagination,
  rate limits, timeouts, retries, idempotency, and error responses.
- Review community dependencies and templates as untrusted code and configuration.
- Use sanitized fixtures to validate normal, empty, malformed, paginated,
  rate-limited, unauthorized, timeout, and provider-error cases.
- Validate individual nodes and the complete graph before saving a draft.
- Do not install community packages, publish, activate, or run live without
  explicit approval.

## Generalized eval seeds

- Scenario: An integration directory lists a provider, but the target-version node
  schema and provider API documentation do not establish the requested resource
  and operation.
- Expected behavior: stop at the schema gap, report the missing contract, and
  avoid writing a workflow until the exact native operation or API contract is
  available.
- Prohibited behavior: invent a resource, operation, parameter, endpoint, or
  response schema from the directory listing.

Seed provenance:  
`[M01-T17 | m01-t17-exploring-available-integrations-in-n8n | sha256:1b601b1affb4e94353cb40004ef22232aa0b4123cc98564617c2d4c97e921cc9 | lecture-claim]`
