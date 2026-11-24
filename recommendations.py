
"""Transparent, rule-based product matching and AM/PM routine generation."""

import math
import re
import unicodedata


INGREDIENT_ALIASES = {
    "niacinamide": {
        "niacinamide",
        "nicotinamide",
    },
    "vitamin c": {
        "vitamin c",
        "ascorbic acid",
        "l-ascorbic acid",
    },
    "fragrance": {
        "fragrance",
        "parfum",
        "perfume",
    },
    "retinal": {
        "retinal",
        "retinaldehyde",
    },
}


# --------------------------------------------------
# NORMALIZATION HELPERS
# --------------------------------------------------

def _normalize(value):
    """Normalize text for consistent comparisons."""

    value = unicodedata.normalize(
        "NFKC",
        str(value or "")
    ).casefold()

    value = value.replace("&", " and ")
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


def _split_values(value):
    """Split comma/semicolon/newline/pipe-separated values."""

    if value is None:
        return set()

    if isinstance(value, (list, tuple, set)):
        parts = value
    else:
        parts = re.split(r"[,;|\n]+", str(value))

    return {
        _normalize(part)
        for part in parts
        if _normalize(part)
    }


def _canonical_ingredient(value):
    """Convert known ingredient aliases to a common name."""

    normalized = _normalize(value)

    for canonical, aliases in INGREDIENT_ALIASES.items():
        normalized_aliases = {
            _normalize(alias)
            for alias in aliases
        }

        if normalized in normalized_aliases:
            return _normalize(canonical)

    return normalized


def _ingredient_set(value):
    """Return a normalized set of ingredients."""

    if value is None:
        return set()

    if isinstance(value, str) and _normalize(value) in {
        "",
        "none",
        "nil",
        "n a",
        "na",
        "no ingredients",
        "nothing",
    }:
        return set()

    return {
        _canonical_ingredient(item)
        for item in _split_values(value)
    }


def _safe_float(value, default=None):
    """Convert a value to a finite float."""

    try:
        number = float(value)

        if math.isfinite(number):
            return number

    except (TypeError, ValueError):
        pass

    return default


def _canonical_skin_type(value):
    """Normalize skin-type variations."""

    normalized = _normalize(value)

    if normalized == "all skin types":
        return "all"

    if normalized.endswith(" skin"):
        normalized = normalized[:-5].strip()

    return normalized


# --------------------------------------------------
# PRODUCT RECOMMENDATION
# --------------------------------------------------

def recommend_products(
    products,
    skin_type,
    skin_concerns,
    budget=None,
    avoid_ingredients=None,
):
    """Return ranked product, score and reason records."""

    selected_type = _canonical_skin_type(skin_type)
    selected_concerns = _split_values(skin_concerns)
    avoided = _ingredient_set(avoid_ingredients)

    # Empty budget means no budget restriction.
    # Invalid non-empty budgets must not remove the restriction.
    if budget is None or (
        isinstance(budget, str) and not budget.strip()
    ):
        max_budget = None
    else:
        max_budget = _safe_float(budget)

        if max_budget is None or max_budget <= 0:
            return []

    results = []

    for product in products or []:

        if not isinstance(product, dict):
            continue

        product_types = {
            _canonical_skin_type(item)
            for item in _split_values(product.get("skin_type"))
        }

        product_concerns = _split_values(
            product.get("skin_concerns")
        )

        ingredient_source = (
            product.get("ingredient_names")
            or product.get("ingredients")
        )

        product_ingredients = _ingredient_set(
            ingredient_source
        )

        # Unknown ingredient lists are excluded when
        # the user wants to avoid specific ingredients.
        if avoided and not product_ingredients:
            continue

        if avoided.intersection(product_ingredients):
            continue

        price = _safe_float(product.get("price"))

        if price is None or price <= 0:
            continue

        if max_budget is not None and price > max_budget:
            continue

        type_match = bool(selected_type) and (
            selected_type in product_types
            or "all" in product_types
        )

        matched_concerns = sorted(
            selected_concerns.intersection(product_concerns)
        )

        score = 0
        reasons = []

        if type_match:
            score += 35
            reasons.append(
                f"Suitable for {skin_type} skin"
            )

        if matched_concerns:
            score += min(45, 15 * len(matched_concerns))

            reasons.append(
                "Matches: "
                + ", ".join(
                    item.title()
                    for item in matched_concerns
                )
            )

        if score <= 0:
            continue

        results.append({
            "product": product,
            "score": score,
            "reason": "; ".join(reasons),
            "matched_concerns_count": len(matched_concerns),
            "skin_type_match": type_match,
        })

    results.sort(
        key=lambda item: (
            -item["score"],
            -item["matched_concerns_count"],
            -int(item["skin_type_match"]),
            _safe_float(
                item["product"].get("price"),
                float("inf")
            ),
            _normalize(
                item["product"].get("product_name")
            ),
        )
    )

    return results


# --------------------------------------------------
# ROUTINE GENERATION
# --------------------------------------------------

def _serum_schedule(product):
    """Determine serum timing from its usage instructions."""

    instructions = _normalize(
        product.get("usage_instructions")
    )

    if not instructions:
        return "unspecified"

    # Avoid assigning a time when instructions contain
    # a negative or restrictive usage statement.
    negative_phrases = (
        "do not use",
        "don t use",
        "avoid",
        "not recommended",
        "not use",
    )

    if any(phrase in instructions for phrase in negative_phrases):
        return "unspecified"

    words = set(instructions.split())

    morning = bool(
        words.intersection({"morning", "am", "daytime"})
    )

    evening = bool(
        words.intersection({"evening", "night", "pm", "nighttime"})
    )

    twice_daily = (
        "twice daily" in instructions
        or "twice a day" in instructions
        or "morning and evening" in instructions
        or "morning and night" in instructions
        or "am and pm" in instructions
    )

    if twice_daily or (morning and evening):
        return "both"

    if morning:
        return "AM"

    if evening:
        return "PM"

    return "unspecified"

def generate_skincare_routine(recommendations):
    """Generate a basic AM/PM routine from recommended products."""

    selected = {}

    for item in recommendations or []:

        if not isinstance(item, dict):
            continue

        product = item.get("product", item)

        if not isinstance(product, dict):
            continue

        category = _normalize(product.get("category"))

        if not category:
            continue

        if "cleanser" in category or "face wash" in category:
            selected.setdefault("cleanser", product)

        elif "toner" in category:
            selected.setdefault("toner", product)

        elif "serum" in category:
            selected.setdefault("serum", product)

        elif "moistur" in category:
            selected.setdefault("moisturizer", product)

        elif "sunscreen" in category or "sun screen" in category:
            selected.setdefault("sunscreen", product)

    def step(label, product):
        name = product.get("product_name") or "Selected product"
        return f"{label}: {name}"

    morning = []
    evening = []

    if "cleanser" in selected:
        morning.append(step("Cleanse", selected["cleanser"]))
        evening.append(step("Cleanse", selected["cleanser"]))

    if "toner" in selected:
        morning.append(step("Tone", selected["toner"]))
        evening.append(step("Tone", selected["toner"]))

    if "serum" in selected:
        serum = selected["serum"]
        schedule = _serum_schedule(serum)

        serum_step = (
            step("Apply serum", serum)
            + " (follow the product label)"
        )

        if schedule in {"AM", "both"}:
            morning.append(serum_step)

        if schedule in {"PM", "both"}:
            evening.append(serum_step)

        if schedule == "unspecified":
            reminder = (
                "Check the product label for serum timing: "
                + (
                    serum.get("product_name")
                    or "Selected serum"
                )
            )
            morning.append(reminder)

    if "moisturizer" in selected:
        morning.append(
            step("Moisturize", selected["moisturizer"])
        )
        evening.append(
            step("Moisturize", selected["moisturizer"])
        )

    if "sunscreen" in selected:
        morning.append(
            step("Apply sunscreen", selected["sunscreen"])
            + " (last step; reapply as directed)"
        )

    if not morning:
        morning.append(
            "No matching products are available "
            "for a morning routine yet."
        )

    if not evening:
        evening.append(
            "No matching products are available "
            "for an evening routine yet."
        )

    return {
        "AM": morning,
        "PM": evening,
    }
