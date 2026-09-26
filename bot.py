TRIGGER_STRATEGIES = {
    "active_planning_intent": "planning",
    "appointment_tomorrow": "customer_reminder",

    "category_seasonal": "seasonal",
    "cde_opportunity": "research",
    "chronic_refill_due": "customer_reminder",

    "competitor_opened": "competitor",
    "curious_ask_due": "curiosity",

    "customer_lapsed_hard": "winback",
    "customer_lapsed_soft": "winback",

    "dormant_with_vera": "dormancy",

    "festival_upcoming": "festival",
    "gbp_unverified": "profile",

    "ipl_match_today": "event",

    "milestone_reached": "milestone",

    "perf_dip": "performance_dip",
    "perf_spike": "performance_spike",

    "recall_due": "customer_reminder",
    "regulation_change": "compliance",
    "renewal_due": "renewal",

    "research_digest": "research",

    "review_theme_emerged": "review_theme",

    "seasonal_perf_dip": "performance_dip",
    "supply_alert": "supply",

    "trial_followup": "followup",
    "wedding_package_followup": "followup",

    "winback_eligible": "winback",
}


def get_strategy(trigger):
    kind = trigger.get("kind", "")
    return TRIGGER_STRATEGIES.get(kind, "general")


def get_merchant_name(merchant):
    identity = merchant.get("identity", {})
    return identity.get("name") or merchant.get("name") or "your business"


def get_city(merchant):
    identity = merchant.get("identity", {})
    return identity.get("city", "")


def get_locality(merchant):
    identity = merchant.get("identity", {})
    return identity.get("locality", "")


def get_performance(merchant):
    return merchant.get("performance", {})


def get_offers(merchant):
    return merchant.get("offers", [])


def get_signals(merchant):
    return merchant.get("signals", [])


def get_customer_aggregate(merchant):
    return merchant.get("customer_aggregate", {})


def get_customer_name(customer):
    if not customer:
        return ""

    identity = customer.get("identity", {})
    return identity.get("name") or customer.get("name") or ""


def get_customer_state(customer):
    if not customer:
        return ""

    return customer.get("state", "")


def get_customer_preferences(customer):
    if not customer:
        return {}

    return customer.get("preferences", {})


def get_customer_consent(customer):
    if not customer:
        return {}

    return customer.get("consent", {})


def get_trigger_payload(trigger):
    return trigger.get("payload", {})

def compose_performance_dip(merchant, trigger=None):
    merchant_name = get_merchant_name(merchant)
    performance = get_performance(merchant)
    signals = get_signals(merchant)

    delta_7d = performance.get("delta_7d", {})

    calls_pct = delta_7d.get("calls_pct")
    views_pct = delta_7d.get("views_pct")

    if calls_pct is not None and calls_pct < 0:
        metric = "calls"
        change = abs(calls_pct * 100)
        body = (
            f"{merchant_name}, your {metric} are down "
            f"{change:.0f}% over the last 7 days."
        )

    elif views_pct is not None and views_pct < 0:
        metric = "views"
        change = abs(views_pct * 100)
        body = (
            f"{merchant_name}, your {metric} are down "
            f"{change:.0f}% over the last 7 days."
        )

    else:
        body = (
            f"{merchant_name}, I've spotted a recent performance dip "
            f"but the trigger doesn't include enough detail to say "
            f"which metric changed."
        )

    if signals:
        body += (
            " I can check the available listing signals and suggest "
            "one change to test. Want me to check?"
        )
    else:
        body += (
            " I can check the available performance signals and suggest "
            "one change to test. Want me to check?"
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": (
            trigger.get("suppression_key", "")
            if trigger
            else ""
        ),
        "rationale": (
            "Performance-dip message uses merchant performance data "
            "when available and avoids inventing a metric for incomplete "
            "triggers."
        ),
    }


def compose_competitor(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    competitor = payload.get("competitor_name")
    distance = payload.get("distance_km")
    their_offer = payload.get("their_offer")

    if competitor:
        body = (
            f"{merchant_name}, a new competitor, {competitor}, "
            f"has opened"
        )

        if distance is not None:
            body += f" {distance} km away"

        if their_offer:
            body += f" with {their_offer}"

        body += (
            ". I can compare that offer with your current positioning "
            "and suggest one response. Want me to check?"
        )
    else:
        body = (
            f"{merchant_name}, I spotted a new competitor signal "
            "nearby. I don't have the competitor details yet, so I "
            "won't guess at the offer or pricing. I can check the "
            "signal and compare it with your current positioning. "
            "Want me to check?"
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Competitor message uses supplied competitor, distance, "
            "and offer details and avoids inventing details for "
            "placeholder triggers."
        ),
    }


def compose_milestone(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    metric = payload.get("metric")
    value_now = payload.get("value_now")
    milestone_value = payload.get("milestone_value")

    if (
        metric == "review_count"
        and value_now is not None
        and milestone_value is not None
    ):
        remaining = milestone_value - value_now

        if remaining > 0:
            body = (
                f"{merchant_name}, you're at {value_now} reviews "
                f"and only {remaining} away from {milestone_value}. "
                f"That's a good moment to plan the next push. "
                f"Want me to suggest one?"
            )
        elif remaining == 0:
            body = (
                f"{merchant_name}, you've reached {milestone_value} "
                f"reviews. That's a good moment to plan the next "
                f"push. Want me to suggest one?"
            )
        else:
            body = (
                f"{merchant_name}, you've passed the "
                f"{milestone_value}-review milestone and are now at "
                f"{value_now}. Want me to suggest one way to build "
                f"on it?"
            )

    elif metric and value_now is not None:
        body = (
            f"{merchant_name}, you've reached {value_now} "
            f"on {metric.replace('_', ' ')}."
            f" I can suggest one simple way to build on the "
            f"milestone. Want me to suggest one?"
        )

    else:
        body = (
            f"{merchant_name}, there's a new milestone signal for "
            f"your business. I don't have the milestone details yet, "
            f"so I won't guess at the number. I can check it and "
            f"suggest one way to build on it. Want me to check?"
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Milestone message uses supplied milestone values when "
            "available and avoids inventing the achievement for "
            "incomplete triggers."
        ),
    }


def compose_customer_reminder(merchant, trigger, customer):
    merchant_name = get_merchant_name(merchant)
    customer_name = get_customer_name(customer)
    payload = get_trigger_payload(trigger)

    service_due = payload.get("service_due")
    due_date = payload.get("due_date")
    available_slots = payload.get("available_slots", [])

    if service_due:
        service_map = {
            "6_month_cleaning": "6-month cleaning recall",
            "chronic_refill": "regular refill",
        }

        service_text = service_map.get(
            service_due,
            service_due.replace("_", " ")
        )

        body = (
            f"Hi {customer_name}, {merchant_name} here. "
            f"Your {service_text} is due"
        )

        if due_date:
            body += f" on {due_date}"

        body += "."

        if available_slots:
            slot_labels = [
                slot.get("label")
                for slot in available_slots[:2]
                if slot.get("label")
            ]

            if slot_labels:
                if len(slot_labels) == 1:
                    body += (
                        f" Aapke liye {slot_labels[0]} available hai. "
                        f"Jo slot convenient ho, bata dijiye."
                    )
                else:
                    body += (
                        f" Aapke liye {slot_labels[0]} ya "
                        f"{slot_labels[1]} available hai. "
                        f"Jo slot convenient ho, bata dijiye."
                    )
            else:
                body += (
                    " Reply here if you'd like to book or "
                    "confirm a convenient time."
                )
        else:
            body += (
                " Reply here if you'd like to book or "
                "confirm a convenient time."
            )

    else:
        body = (
            f"Hi {customer_name}, {merchant_name} here. "
            f"Your recall reminder is due. "
            f"Reply here if you'd like to book a convenient time."
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "merchant_on_behalf",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Customer reminder uses supplied service, due date, and "
            "available appointment slots when present, while "
            "placeholder triggers receive a generic reminder."
        ),
    }


def compose_performance_spike(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    metric = payload.get("metric")
    delta_pct = payload.get("delta_pct")
    window = payload.get("window")
    baseline = payload.get("vs_baseline")
    likely_driver = payload.get("likely_driver")

    if metric and delta_pct is not None:
        direction = "up" if delta_pct >= 0 else "down"
        change = abs(delta_pct * 100)

        body = (
            f"{merchant_name}, your {metric} are "
            f"{change:g}% {direction}"
        )

        if window:
            body += f" over {window}"

        if baseline is not None:
            body += f". The baseline was {baseline}"

        if likely_driver:
            driver = likely_driver.replace("_", " ")
            body += f". The likely driver is your {driver}"

        body += (
            ". Want me to help you build on what worked?"
        )

    else:
        body = (
            f"{merchant_name}, I've spotted a recent performance "
            f"spike, but the trigger doesn't include enough detail "
            f"to say which metric changed. I can check what changed "
            f"and suggest the next action. Want me to check?"
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Performance-spike message uses supplied metric, change, "
            "baseline, and driver information when available and "
            "avoids inventing details for incomplete triggers."
        ),
    }



def compose_planning(merchant, trigger):
    name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    topic = payload.get("intent_topic", "your idea")
    last_message = payload.get("merchant_last_message", "")

    topic_text = topic.replace("_", " ")

    body = (
        f"{name}, picking up from your earlier note on {topic_text}. "
        f"I can turn that into a concrete plan with the key steps, offer structure, "
        f"and what to test first."
    )

    if last_message:
        body += " Shall I draft it?"

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get("suppression_key", ""),
        "rationale": (
            "Planning message continues the merchant's explicit intent "
            "using the trigger topic and prior message."
        ),
    }


def compose_seasonal(merchant, trigger):
    name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    season = payload.get("season", "")
    trends = payload.get("trends", [])
    shelf_action = payload.get("shelf_action_recommended", False)

    season_text = season.replace("_", " ")

    trend_text = []
    for trend in trends[:3]:
        trend_text.append(trend.replace("_", " "))

    body = f"{name}, for {season_text}, the strongest demand signals are"

    if trend_text:
        body += " " + ", ".join(trend_text) + "."
    else:
        body += " showing up in your category."

    if shelf_action:
        body += (
            " A shelf/listing refresh could help you respond to the demand shift. "
            "Want me to suggest the changes?"
        )
    else:
        body += " Want me to turn these signals into a simple action plan?"

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get("suppression_key", ""),
        "rationale": (
            "Seasonal message uses the supplied demand trends and "
            "recommended action without inventing category data."
        ),
    }


def compose_research(merchant, trigger):
    name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    digest_id = payload.get("digest_item_id")
    credits = payload.get("credits")
    fee = payload.get("fee")

    body = f"{name}, there is a new research item relevant to your practice"

    if digest_id:
        body += f" ({digest_id})"

    body += "."

    if credits is not None:
        body += f" You have {credits} credit(s) available"

    if fee:
        body += f", and this item is {fee}"

    body += (
        ". I can give you the key takeaway and explain "
        "how it could apply to your practice. Want me to open it?"
    )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get("suppression_key", ""),
        "rationale": (
            "Research message is grounded in the supplied digest reference, "
            "credits, and fee."
        ),
    }


def compose_winback(merchant, trigger, customer):
    customer_name = get_customer_name(customer)
    payload = get_trigger_payload(trigger)

    days_since_visit = payload.get("days_since_last_visit")
    previous_focus = payload.get("previous_focus")

    merchant_name = get_merchant_name(merchant)

    if days_since_visit is not None and previous_focus:
        focus_text = previous_focus.replace("_", " ")

        body = (
            f"Hi {customer_name}, {merchant_name} here. "
            f"We haven't seen you in {days_since_visit} days. "
            f"Last time you were working on {focus_text}. "
            f"If you'd like to get back to it, reply here and we'll help you plan your next visit."
        )
    else:
        body = (
            f"Hi {customer_name}, {merchant_name} here. "
            f"We haven't seen you in a while. "
            f"If you'd like to come back, reply here and we'll help you plan your next visit."
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "merchant_on_behalf",
        "suppression_key": trigger.get("suppression_key", ""),
        "rationale": (
            "Winback message uses available customer recency and "
            "previous focus without inventing an offer."
        ),
    }


def compose_appointment_reminder(merchant, trigger, customer):
    customer_name = get_customer_name(customer)
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    appointment_time = payload.get("appointment_time")
    service = payload.get("service")
    location = payload.get("location")

    body = f"Hi {customer_name}, {merchant_name} here. Your appointment is tomorrow"

    if appointment_time:
        body += f" at {appointment_time}"

    if service:
        body += f" for {service}"

    if location:
        body += f" at {location}"

    body += ". Reply here if you need to confirm or reschedule."

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "merchant_on_behalf",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Appointment reminder uses only appointment details "
            "present in the trigger payload."
        ),
    }


def compose_supply_alert(merchant, trigger, customer=None):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    molecule = payload.get("molecule")
    affected_batches = payload.get("affected_batches", [])
    manufacturer = payload.get("manufacturer")

    greeting = f"{merchant_name}, "

    body = f"{greeting}there is a supply alert for {molecule or 'a medicine'}."

    if manufacturer:
        body += f" The affected manufacturer is {manufacturer}."

    if affected_batches:
        batch_text = ", ".join(affected_batches)
        body += f" Affected batches: {batch_text}."

    body += " Please check your stock and take the required action."

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Supply alert uses the medicine, manufacturer, and affected "
            "batches explicitly provided by the merchant-scoped trigger."
        ),
    }

def compose_chronic_refill(merchant, trigger, customer):
    customer_name = get_customer_name(customer)
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    molecules = payload.get("molecule_list", [])
    stock_runs_out = payload.get("stock_runs_out_iso")
    delivery_saved = payload.get("delivery_address_saved", False)

    if customer_name:
        body = f"Hi {customer_name}, {merchant_name} here. "
    else:
        body = f"Hi, {merchant_name} here. "

    if molecules:
        medicine_text = ", ".join(molecules)
        body += f"Your regular refill for {medicine_text} is coming due."
    else:
        body += "Your refill reminder is due."

    if stock_runs_out:
        date_text = stock_runs_out.split("T")[0]
        body += f" Current stock is expected to run out around {date_text}."

    if delivery_saved:
        body += " We have your saved delivery details."

    body += " Reply here if you'd like us to arrange it."

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "merchant_on_behalf",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Chronic refill message uses the customer's refill trigger, "
            "medicine list, stock timing, and saved delivery information."
        ),
    }

def compose_curiosity(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    if payload.get("ask_template") == "what_service_in_demand_this_week":
        body = (
            f"{merchant_name}, want to know which services are seeing "
            f"the strongest demand this week? I can pull the relevant "
            f"demand signal and turn it into one action to test."
        )
    else:
        body = (
            f"{merchant_name}, I can pull the latest demand signal "
            f"relevant to your business and turn it into one action "
            f"to test. Want me to check?"
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Curiosity trigger asks Vera to surface a relevant "
            "demand signal without inventing a metric when the "
            "trigger payload is only a placeholder."
        ),
    }

def compose_dormancy(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    days = payload.get("days_since_last_merchant_message")
    last_topic = payload.get("last_topic")

    if days is not None and last_topic:
        body = (
            f"{merchant_name}, it's been {days} days since our last "
            f"conversation about {last_topic.replace('_', ' ')}. "
            f"If you'd like to pick that back up, I can help with the "
            f"next step."
        )
    else:
        body = (
            f"{merchant_name}, it's been a while since we last "
            f"connected. If there's something you'd like to pick back "
            f"up, I can help with the next step."
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Dormancy message uses the available conversation history "
            "when present and avoids inventing a previous topic when "
            "the trigger is only a placeholder."
        ),
    }

def compose_festival(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    festival = payload.get("festival")
    date = payload.get("date")
    days_until = payload.get("days_until")
    category_relevance = payload.get("category_relevance", [])

    if festival and date:
        relevance = ""

        if category_relevance:
            category = (
                merchant.get("category")
                or merchant.get("business", {}).get("category")
                or ""
            )

            if category in category_relevance:
                relevance = (
                    f" It is relevant to {category} businesses."
                )

        timing = ""
        if days_until is not None:
            timing = f" It is {days_until} days away."

        body = (
            f"{merchant_name}, {festival} is coming up on {date}."
            f"{timing}{relevance} "
            f"I can help you plan one relevant offer or listing update."
        )
    else:
        body = (
            f"{merchant_name}, there's an upcoming seasonal opportunity "
            f"worth planning for. I can help identify one relevant offer "
            f"or listing update to test."
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Festival message uses the supplied festival timing and "
            "relevance data when available, and stays generic for "
            "placeholder triggers."
        ),
    }

def compose_profile(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    verified = payload.get("verified")
    verification_path = payload.get("verification_path")
    uplift = payload.get("estimated_uplift_pct")

    if verified is False:
        path_text = ""

        if verification_path:
            path_text = (
                f" Verification is available via "
                f"{verification_path.replace('_', ' ')}."
            )

        uplift_text = ""
        if uplift is not None:
            uplift_pct = uplift * 100
            uplift_text = (
                f" The trigger estimates up to {uplift_pct:.0f}% "
                f"potential uplift, but that is not guaranteed."
            )

        body = (
            f"{merchant_name}, your Google Business Profile is still "
            f"unverified.{path_text}{uplift_text} "
            f"I can walk you through the verification step."
        )
    else:
        body = (
            f"{merchant_name}, your Google Business Profile is "
            f"verified. I can help you review the listing for the "
            f"next improvement."
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Profile message uses the verification status and supplied "
            "verification path, while qualifying the estimated uplift "
            "rather than presenting it as guaranteed."
        ),
    }

def compose_event(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    match = payload.get("match")
    venue = payload.get("venue")
    city = payload.get("city")
    match_time = payload.get("match_time_iso")

    if match and venue:
        time_text = ""

        if match_time:
            time_part = match_time.split("T")[-1]
            time_part = time_part.split("+")[0]
            time_text = f" at {time_part}"

        location_text = ""
        if city:
            location_text = f" in {city}"

        body = (
            f"{merchant_name}, {match} is being played at {venue}"
            f"{location_text}{time_text}. "
            f"I can help you plan one match-day offer or listing "
            f"update to capture nearby demand. Want me to suggest one?"
        )
    else:
        body = (
            f"{merchant_name}, there's a match-day opportunity today. "
            f"I can help you plan one relevant offer or listing update. "
            f"Want me to suggest one?"
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Event message uses the supplied match, venue, city, and "
            "timing data without inventing a promotion."
        ),
    }

def compose_compliance(merchant, trigger):
    merchant_name = get_merchant_name(merchant)
    payload = get_trigger_payload(trigger)

    item_id = payload.get("top_item_id")
    deadline = payload.get("deadline_iso")

    if item_id and deadline:
        body = (
            f"{merchant_name}, there is a new compliance item "
            f"relevant to your category ({item_id}), with a deadline "
            f"of {deadline}. I can open the item and help you review "
            f"what needs attention."
        )
    else:
        body = (
            f"{merchant_name}, there is a new compliance update "
            f"relevant to your business. I can open the item and "
            f"help you review what needs attention."
        )

    return {
        "body": body,
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            "Compliance message uses only the supplied compliance "
            "item and deadline and does not invent the underlying "
            "regulatory requirement."
        ),
    }

def compose(category, merchant, trigger, customer=None):
    strategy = get_strategy(trigger)

    if trigger.get("kind") == "appointment_tomorrow" and customer is not None:
        return compose_appointment_reminder(
            merchant,
            trigger,
            customer
        )

    if strategy == "supply":
        return compose_supply_alert(
            merchant,
            trigger,
            customer
        )

    if trigger.get("kind") == "chronic_refill_due" and customer is not None:
        return compose_chronic_refill(
            merchant,
            trigger,
            customer
        )

    if strategy == "winback" and customer is not None:
        return compose_winback(
            merchant,
            trigger,
            customer
        )

    if strategy == "customer_reminder" and customer is not None:
        return compose_customer_reminder(
            merchant,
            trigger,
            customer
        )

    if strategy == "performance_dip":
        return compose_performance_dip(
            merchant,
            trigger
        )

    if strategy == "performance_spike":
        return compose_performance_spike(
            merchant,
            trigger
        )

    if strategy == "competitor":
        return compose_competitor(
            merchant,
            trigger
        )

    if strategy == "milestone":
        return compose_milestone(
            merchant,
            trigger
        )

    if strategy == "planning":
        return compose_planning(
            merchant,
            trigger
        )

    if strategy == "seasonal":
        return compose_seasonal(
            merchant,
            trigger
        )

    if strategy == "research":
        return compose_research(
            merchant,
            trigger
        )

    if strategy == "curiosity":
        return compose_curiosity(
            merchant,
            trigger
        )

    if strategy == "dormancy":
        return compose_dormancy(
            merchant,
            trigger
        )

    if trigger.get("kind") == "festival_upcoming":
        return compose_festival(
            merchant,
            trigger
        )

    if trigger.get("kind") == "gbp_unverified":
        return compose_profile(
            merchant,
            trigger
        )

    if trigger.get("kind") == "ipl_match_today":
        return compose_event(
            merchant,
            trigger
        )

    if trigger.get("kind") == "regulation_change":
        return compose_compliance(
            merchant,
            trigger
        )

    merchant_name = get_merchant_name(merchant)
    trigger_kind = trigger.get(
        "kind",
        "update"
    )

    return {
        "body": (
            f"Hi {merchant_name}, I have an update related to "
            f"{trigger_kind}."
        ),
        "cta": "open_ended",
        "send_as": "vera",
        "suppression_key": trigger.get(
            "suppression_key",
            ""
        ),
        "rationale": (
            f"Strategy '{strategy}' selected for trigger "
            f"'{trigger_kind}'."
        ),
    }
# ============================================================
# FastAPI layer for Magicpin Vera challenge
# ============================================================

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Vera AI")


# ------------------------------------------------------------
# Runtime state
# ------------------------------------------------------------

START_TIME = time.time()

# (scope, context_id) -> {"version": int, "payload": dict}
contexts: Dict[Tuple[str, str], Dict[str, Any]] = {}

# conversation_id -> conversation state
conversations: Dict[str, Dict[str, Any]] = {}


# ------------------------------------------------------------
# Request models
# ------------------------------------------------------------

class ContextBody(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str


class TickBody(BaseModel):
    now: str
    available_triggers: List[str] = []


class ReplyBody(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str
    message: str
    received_at: str
    turn_number: int


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

VALID_SCOPES = {
    "category",
    "merchant",
    "customer",
    "trigger",
}


def get_context(scope: str, context_id: Optional[str]):
    if not context_id:
        return None

    entry = contexts.get((scope, context_id))
    if not entry:
        return None

    return entry["payload"]


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_conversation_id(merchant_id: str, trigger_id: str):
    return (
        f"conv_{merchant_id}_{trigger_id}_"
        f"{uuid.uuid4().hex[:8]}"
    )


def get_template_name(result: dict, trigger: dict):
    send_as = result.get("send_as", "vera")
    kind = trigger.get("kind", "generic")

    if send_as == "merchant_on_behalf":
        return f"merchant_{kind}_v1"

    return f"vera_{kind}_v1"


def get_template_params(
    merchant: dict,
    trigger: dict,
    result: dict,
):
    merchant_name = (
        merchant.get("identity", {}).get("name")
        or merchant.get("name")
        or ""
    )

    return [
        merchant_name,
        trigger.get("kind", ""),
        result.get("body", ""),
    ]


# ------------------------------------------------------------
# GET /v1/healthz
# ------------------------------------------------------------

@app.get("/v1/healthz")
async def healthz():
    counts = {
        "category": 0,
        "merchant": 0,
        "customer": 0,
        "trigger": 0,
    }

    for (scope, _), _entry in contexts.items():
        if scope in counts:
            counts[scope] += 1

    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
        "contexts_loaded": counts,
    }


# ------------------------------------------------------------
# GET /v1/metadata
# ------------------------------------------------------------

@app.get("/v1/metadata")
async def metadata():
    return {
        "team_name": "Aaron Singh",
        "team_members": ["Aaron Singh"],
        "model": "deterministic-rule-based",
        "approach": (
            "trigger-routed deterministic composer "
            "with conversation state"
        ),
        "contact_email": "",
        "version": "1.0.0",
        "submitted_at": utc_now(),
    }


# ------------------------------------------------------------
# POST /v1/context
# ------------------------------------------------------------

@app.post("/v1/context")
async def push_context(body: ContextBody):

    if body.scope not in VALID_SCOPES:
        return {
            "accepted": False,
            "reason": "invalid_scope",
            "details": f"Unsupported scope: {body.scope}",
        }

    key = (body.scope, body.context_id)

    current = contexts.get(key)

    # Existing version is equal or newer.
    # This makes repeated delivery idempotent.
    if current and current["version"] >= body.version:
        return {
            "accepted": False,
            "reason": "stale_version",
            "current_version": current["version"],
        }

    contexts[key] = {
        "version": body.version,
        "payload": body.payload,
    }

    return {
        "accepted": True,
        "ack_id": (
            f"ack_{body.scope}_{body.context_id}"
            f"_v{body.version}"
        ),
        "stored_at": utc_now(),
    }


# ------------------------------------------------------------
# POST /v1/tick
# ------------------------------------------------------------

@app.post("/v1/tick")
async def tick(body: TickBody):

    actions = []

    for trigger_id in body.available_triggers:

        trigger = get_context("trigger", trigger_id)

        if not trigger:
            continue

        merchant_id = trigger.get("merchant_id")

        if not merchant_id:
            continue

        merchant = get_context(
            "merchant",
            merchant_id,
        )

        if not merchant:
            continue

        category_slug = (
            merchant.get("category_slug")
            or merchant.get("category")
        )

        category = get_context(
            "category",
            category_slug,
        )

        if not category:
            continue

        customer_id = trigger.get("customer_id")

        customer = None

        if customer_id:
            customer = get_context(
                "customer",
                customer_id,
            )

        try:
            result = compose(
                category,
                merchant,
                trigger,
                customer,
            )
        except Exception as exc:
            # Never allow one malformed trigger to break
            # the entire tick.
            continue

        if not result or not result.get("body"):
            continue

        conversation_id = make_conversation_id(
            merchant_id,
            trigger_id,
        )

        send_as = result.get(
            "send_as",
            "vera",
        )

        conversations[conversation_id] = {
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "trigger_id": trigger_id,
            "trigger_kind": trigger.get("kind"),
            "initial_result": result,
            "turns": [],
        }

        actions.append({
            "conversation_id": conversation_id,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "send_as": send_as,
            "trigger_id": trigger_id,
            "template_name": get_template_name(
                result,
                trigger,
            ),
            "template_params": get_template_params(
                merchant,
                trigger,
                result,
            ),
            "body": result.get("body", ""),
            "cta": result.get(
                "cta",
                "open_ended",
            ),
            "suppression_key": result.get(
                "suppression_key",
                trigger.get(
                    "suppression_key",
                    "",
                ),
            ),
            "rationale": result.get(
                "rationale",
                "Composed from supplied context.",
            ),
        })

        if len(actions) >= 20:
            break

    return {
        "actions": actions,
    }


# ------------------------------------------------------------
# POST /v1/reply
# ------------------------------------------------------------

@app.post("/v1/reply")
async def reply(body: ReplyBody):

    conversation = conversations.get(body.conversation_id)

    message = body.message.strip()
    message_lower = message.lower()

    # --------------------------------------------------------
    # Detect explicit negative responses
    # --------------------------------------------------------

    negative_tokens = {
        "no",
        "nope",
        "nah",
        "stop",
        "not interested",
        "not now",
        "don't",
        "do not",
        "cancel",
        "later",
    }

    if any(token in message_lower for token in negative_tokens):
        return {
            "action": "end",
            "rationale": (
                "User declined or requested no further follow-up."
            ),
        }

    # --------------------------------------------------------
    # Detect affirmative responses
    # --------------------------------------------------------

    affirmative_tokens = {
        "yes",
        "yeah",
        "yep",
        "sure",
        "okay",
        "ok",
        "please",
        "go ahead",
        "do it",
        "let's do it",
        "lets do it",
        "sounds good",
    }

    if any(token in message_lower for token in affirmative_tokens):
        return {
            "action": "send",
            "body": (
                "Done - I'll take this forward. "
                "Next, we'll proceed with the option we discussed."
            ),
            "cta": "open_ended",
            "rationale": (
                "Clear affirmative intent detected; "
                "advanced to the next action."
            ),
        }

    # --------------------------------------------------------
    # Unknown conversation
    # --------------------------------------------------------

    if not conversation:
        return {
            "action": "end",
            "rationale": (
                "Conversation state was not found and "
                "no clear action intent was detected."
            ),
        }

    # --------------------------------------------------------
    # Store conversation turn
    # --------------------------------------------------------

    conversation["turns"].append({
        "from": body.from_role,
        "message": body.message,
        "turn_number": body.turn_number,
    })

    # --------------------------------------------------------
    # Detect repeated messages
    # --------------------------------------------------------

    previous_messages = [
        turn["message"].strip().lower()
        for turn in conversation["turns"][:-1]
        if turn.get("message")
    ]

    if message_lower in previous_messages:
        return {
            "action": "end",
            "rationale": (
                "Repeated message detected; "
                "ending to avoid repetitive conversation."
            ),
        }

    # --------------------------------------------------------
    # No clear intent
    # --------------------------------------------------------

    return {
        "action": "wait",
        "wait_seconds": 300,
        "rationale": (
            "Response did not contain a clear action intent; "
            "waiting rather than inventing additional information."
        ),
    }    # --------------------------------------------------------
    # Detect repeated canned / auto-reply messages
    # --------------------------------------------------------

    previous_messages = [
        turn["message"].strip().lower()
        for turn in conversation["turns"][:-1]
        if turn.get("message")
    ]

    if message_lower in previous_messages:
        return {
            "action": "end",
            "rationale": (
                "Repeated message detected; ending "
                "to avoid repetitive conversation."
            ),
        }

    # --------------------------------------------------------
    # Default: acknowledge and wait
    # --------------------------------------------------------

    return {
        "action": "wait",
        "wait_seconds": 300,
        "rationale": (
            "Response did not contain a clear action "
            "intent; waiting rather than inventing "
            "additional information."
        ),
    }


# ------------------------------------------------------------
# Local entry point
# ------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "bot:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
    )
