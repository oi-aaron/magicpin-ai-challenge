# Vera AI — Magicpin Challenge

## Overview

This project implements Vera, a deterministic AI message composer for merchant and customer communication over WhatsApp.

The core interface is:

    compose(category, merchant, trigger, customer=None) -> dict

The composer takes category, merchant, trigger, and optional customer context and returns a structured message containing:

- body
- cta
- send_as
- suppression_key
- rationale

The implementation is designed to produce concise, specific, context-aware messages without inventing information that is not present in the supplied context.

## Architecture

The implementation consists of four main layers:

1. Context ingestion
2. Trigger routing
3. Specialized message composition
4. FastAPI API and conversation handling

The core composer is deterministic. The same category, merchant, trigger, and customer inputs produce the same output.

Application state is maintained in memory for the evaluation lifecycle.

## Core Composer

The main function is:

    compose(category, merchant, trigger, customer=None) -> dict

The composer routes triggers to specialized composition strategies.

Supported trigger types include:

- active_planning_intent
- appointment_tomorrow
- category_seasonal
- cde_opportunity
- chronic_refill_due
- competitor_opened
- curious_ask_due
- customer_lapsed_hard
- customer_lapsed_soft
- dormant_with_vera
- festival_upcoming
- gbp_unverified
- ipl_match_today
- milestone_reached
- perf_dip
- perf_spike
- recall_due
- regulation_change
- renewal_due
- research_digest
- review_theme_emerged
- seasonal_perf_dip
- supply_alert
- trial_followup
- wedding_package_followup
- winback_eligible

## Message Contract

Each composed message contains:

    body
    cta
    send_as
    suppression_key
    rationale

### body

The WhatsApp message sent to the recipient.

Messages prioritize concrete information from the supplied context and are kept concise.

### cta

The primary action suggested to the recipient.

The implementation avoids unnecessary multiple calls to action.

For informational situations, the CTA can be open-ended or omitted according to the trigger.

### send_as

The sender identity.

The implementation uses:

    vera

for Vera/merchant-facing messages and:

    merchant_on_behalf

for messages sent on behalf of a merchant to a customer.

### suppression_key

A trigger-specific key used to identify proactive messages and help prevent repetitive outreach.

### rationale

A short explanation of why the message was composed from the supplied context.

## Context-First Design

The composer prioritizes information provided by:

- category context
- merchant context
- customer context
- trigger context

The implementation avoids fabricating missing information.

It does not invent:

- prices
- offers
- appointment slots
- competitor information
- performance metrics
- customer details
- business statistics
- deadlines
- inventory information

When a trigger does not provide enough detail, the composer avoids guessing.

For example, if a competitor trigger does not contain competitor details, the system can acknowledge the competitor signal without inventing an offer or price.

## Merchant and Customer Specificity

Merchant-facing messages use merchant-specific information where available.

Customer-facing messages can use:

- customer name
- merchant name
- appointment information
- recall information
- customer-specific timing
- relevant customer context

Merchant-facing messages can use:

- merchant name
- performance metrics
- demand signals
- competitor information
- category research
- milestones
- compliance information
- seasonal opportunities

The system therefore prefers specific context over generic promotional messaging.

## Language and Voice

The implementation supports English and Hindi-English mixed messaging where appropriate context is available.

Customer-facing messages can use natural Hindi-English phrasing while preserving the factual information supplied by the context.

The message style is designed for WhatsApp communication rather than long formal messages.

## Conversation Handling

The API maintains in-memory conversation state.

Each proactive conversation receives a new conversation ID.

Conversation state contains:

- merchant ID
- customer ID
- trigger ID
- trigger kind
- initial result
- conversation turns

The reply handler supports:

- affirmative intent
- negative or opt-out intent
- repeated-message detection
- waiting when no clear action intent is present
- safe termination when conversation state is unavailable

Explicit negative responses such as:

- no
- nope
- nah
- stop
- not interested
- not now
- cancel
- later

terminate the interaction.

Affirmative responses such as:

- yes
- yeah
- yep
- sure
- okay
- ok
- please
- go ahead
- do it
- let's do it
- sounds good

advance the interaction.

If a message does not contain clear action intent, the system waits rather than inventing an action.

Repeated messages are detected to avoid repetitive conversations.

## FastAPI API

The FastAPI application is implemented in:

    bot.py

The required endpoints are:

    POST /v1/context
    POST /v1/tick
    POST /v1/reply
    GET  /v1/healthz
    GET  /v1/metadata

The API accepts and returns JSON.

## POST /v1/context

This endpoint receives category, merchant, customer, and trigger context.

Request fields:

- scope
- context_id
- version
- payload
- delivered_at

Supported scopes are:

- category
- merchant
- customer
- trigger

Contexts are stored using the combination of scope and context ID.

### Version Handling

The implementation supports versioned context updates.

A higher version replaces the existing version.

A duplicate or lower version is rejected as stale.

A successful context update returns:

    accepted: true
    ack_id
    stored_at

A stale update returns:

    accepted: false
    reason: stale_version
    current_version

This provides idempotent context ingestion.

## POST /v1/tick

The tick endpoint receives:

- now
- available_triggers

For each available trigger, the application:

1. Loads the trigger context.
2. Identifies the merchant.
3. Loads the merchant context.
4. Identifies the merchant category.
5. Loads the category context.
6. Loads the customer context when available.
7. Calls compose().
8. Creates a new conversation ID.
9. Stores conversation state.
10. Returns the outbound action.

Each returned action contains:

- conversation_id
- merchant_id
- customer_id
- send_as
- trigger_id
- template_name
- template_params
- body
- cta
- suppression_key
- rationale

The implementation limits a single tick response to a maximum of 20 actions.

## Conversation IDs

Proactive conversations receive a newly generated conversation ID based on the merchant ID, trigger ID, and a unique suffix.

This allows subsequent /v1/reply requests to reference the correct conversation.

## Templates

The API provides a template name for each proactive action.

For merchant-on-behalf messages, the template follows:

    merchant_<trigger_kind>_v1

For Vera messages, the template follows:

    vera_<trigger_kind>_v1

Template parameters include the merchant name, trigger kind, and generated message body.

## POST /v1/reply

The reply endpoint receives:

- conversation_id
- merchant_id
- customer_id
- from_role
- message
- received_at
- turn_number

Possible response actions are:

- send
- wait
- end

A send response contains:

- action
- body
- cta
- rationale

A wait response contains:

- action
- wait_seconds
- rationale

An end response contains:

- action
- rationale

The handler analyzes explicit affirmative and negative intent before requiring existing conversation state.

This allows clear intent to be handled safely even when conversation state is unavailable.

## GET /v1/healthz

The health endpoint returns:

- status
- uptime_seconds
- contexts_loaded

The contexts_loaded object reports the number of loaded contexts for:

- category
- merchant
- customer
- trigger

Example structure:

    {
        "status": "ok",
        "uptime_seconds": 123,
        "contexts_loaded": {
            "category": 5,
            "merchant": 10,
            "customer": 25,
            "trigger": 25
        }
    }

## GET /v1/metadata

The metadata endpoint returns:

- team_name
- team_members
- model
- approach
- contact_email
- version
- submitted_at

The current implementation identifies the model as:

    deterministic-rule-based

The approach is:

    trigger-routed deterministic composer with conversation state

## In-Memory State

The application stores context state and conversation state in memory.

The main in-memory structures are:

    contexts
    conversations

No persistent database is required for the evaluation service.

## Dataset

The project includes deterministic dataset generation.

The dataset generator uses the seed:

    20260426

The generated dataset contains:

- 5 categories
- 50 merchants
- 200 customers
- 100 triggers
- 30 canonical pairs

The generated contexts are used to test the composer and API lifecycle.

## Canonical Test Suite

The canonical test runner is:

    test_all.py

It executes 30 canonical test pairs.

The canonical tests cover trigger types including:

- active_planning_intent
- appointment_tomorrow
- category_seasonal
- cde_opportunity
- chronic_refill_due
- competitor_opened
- curious_ask_due
- customer_lapsed_hard
- customer_lapsed_soft
- dormant_with_vera
- festival_upcoming
- gbp_unverified
- ipl_match_today
- milestone_reached
- perf_dip
- perf_spike
- recall_due
- regulation_change

All 30 canonical tests T01 through T30 have been executed successfully.

## Determinism Testing

The canonical test suite was executed twice.

The outputs from both runs were compared.

The comparison produced:

    FC: no differences encountered

This confirms deterministic output for repeated identical inputs.

## Local Judge Simulator

The project contains:

    judge_simulator.py

The simulator reproduces the API evaluation lifecycle locally.

It tests:

- health checks
- metadata
- category context ingestion
- merchant context ingestion
- customer context ingestion
- trigger context ingestion
- warmup
- proactive ticks
- conversational replies
- intent transitions
- hostile or off-topic messages

The simulator was successfully executed using Gemini 2.5 Flash Lite.

The tested scenarios included:

- auto-reply handling
- intent transition
- hostile/off-topic handling

The intent transition test successfully handled affirmative input such as:

    Ok lets do it. Whats next?

without incorrectly ending the conversation.

## Running Locally

Python 3.11+ is recommended.

Install dependencies:

    python -m pip install -r requirements.txt

Start the FastAPI application:

    python -m uvicorn bot:app --host 0.0.0.0 --port 8080

The application is then available locally at:

    http://localhost:8080

## Running Canonical Tests

From the project directory:

    python test_all.py

This executes T01 through T30.

## Running the Local Judge Simulator

Run:

    python judge_simulator.py

The simulator requires an LLM API key for simulated merchant/customer interactions.

The Vera API itself does not require an external LLM call for the deterministic composer.

## Requirements

The main API dependencies are pinned in:

    requirements.txt

Current dependencies:

    fastapi==0.95.2
    pydantic==1.10.15
    uvicorn==0.34.0

## Project Structure

The main project files are:

    magicpin-ai-challenge/
    ├── bot.py
    ├── submission.jsonl
    ├── test_all.py
    ├── judge_simulator.py
    ├── requirements.txt
    ├── README.md
    ├── challenge-brief.md
    ├── challenge-testing-brief.md
    ├── engagement-design.md
    ├── engagement-research.md
    ├── dataset/
    │   └── generate_dataset.py
    ├── examples/
    └── expanded/

## Important Files

### bot.py

Main Vera implementation containing:

- compose()
- trigger routing
- specialized message strategies
- FastAPI application
- context management
- tick handling
- reply handling
- health endpoint
- metadata endpoint

### submission.jsonl

Contains the 30 canonical submission records.

### test_all.py

Runs the canonical deterministic test suite.

### judge_simulator.py

Runs the local LLM-powered API evaluation simulator.

### requirements.txt

Contains the Python dependencies required by the API.

### challenge-brief.md

Contains the challenge requirements.

### challenge-testing-brief.md

Contains the API and evaluation requirements.

### engagement-design.md

Contains engagement design material.

### engagement-research.md

Contains engagement research material.

### dataset/generate_dataset.py

Generates the deterministic expanded dataset.

## Submission JSONL

The file:

    submission.jsonl

contains 30 canonical records corresponding to T01 through T30.

Each record contains the canonical input and generated output used for evaluation.

The outputs are generated by the deterministic composer.

## Evaluation API Contract

The public evaluation service must expose:

    POST /v1/context
    POST /v1/tick
    POST /v1/reply
    GET  /v1/healthz
    GET  /v1/metadata

The production service must be publicly reachable over HTTPS.

Local HTTP is supported for development and testing.

## Evaluation Lifecycle

The expected evaluation lifecycle is:

1. Start the service.
2. Perform health checks.
3. Push category contexts.
4. Push merchant contexts.
5. Push customer contexts.
6. Push trigger contexts.
7. Call /v1/tick with available triggers.
8. Receive proactive actions.
9. Simulate merchant or customer responses.
10. Call /v1/reply.
11. Continue the conversation when required.
12. Inject updated contexts or new triggers when required.
13. Continue ticking and replying.

The application therefore supports context updates after startup through versioned context ingestion.

## Security and Data Handling

The API keeps evaluation contexts and conversations in memory.

The deterministic API does not require an external merchant/customer database.

The application does not require external non-LLM services for message composition.

LLM API keys used by local testing tools should be supplied securely and must not be committed to source control.

Production secrets should be stored as environment variables or deployment secrets.

## Deployment

The application can be deployed to a Python-compatible hosting provider capable of running FastAPI and exposing a public HTTPS endpoint.

The server should listen on:

    0.0.0.0

The application can be started with:

    python -m uvicorn bot:app --host 0.0.0.0 --port 8080

The production deployment must expose the following routes:

    POST /v1/context
    POST /v1/tick
    POST /v1/reply
    GET  /v1/healthz
    GET  /v1/metadata

The public URL must support HTTPS.

## Determinism

The core compose() implementation is deterministic.

Given the same:

- category
- merchant
- trigger
- customer

the same structured output is produced.

The dataset generation process also uses a fixed seed.

This allows the canonical tests and submission outputs to be reproduced consistently.

## Design Principles

The implementation follows these principles:

1. Use supplied context rather than assumptions.
2. Prefer specific information over generic promotional copy.
3. Keep WhatsApp messages concise.
4. Use one primary CTA.
5. Avoid fabricated facts.
6. Match the message to the trigger.
7. Match the message to the merchant.
8. Use customer context when available.
9. Respect language and communication context.
10. Avoid repetitive proactive messaging.
11. Respect explicit negative intent.
12. Wait rather than invent information when intent is unclear.
13. Keep the core composer deterministic.
14. Keep evaluation state in memory.
15. Support context updates through versioned ingestion.
16. Maintain conversation state for proactive interactions.

## Validation Status

The implementation has been locally validated for:

- Core composer
- T01–T30 canonical tests
- Determinism across repeated runs
- POST /v1/context
- POST /v1/tick
- POST /v1/reply
- GET /v1/healthz
- GET /v1/metadata
- Context version handling
- Proactive conversation creation
- Affirmative intent handling
- Negative intent handling
- Repeated message handling
- Wait behavior
- Judge simulator scenarios

All of the above have passed local validation.

## Final Submission Components

The main submission components are:

    bot.py
    submission.jsonl
    README.md
    requirements.txt

Supporting files include:

    test_all.py
    judge_simulator.py
    challenge-brief.md
    challenge-testing-brief.md
    engagement-design.md
    engagement-research.md
    dataset/generate_dataset.py

The FastAPI application in bot.py provides the evaluation interface, while submission.jsonl provides the canonical test outputs.