# Brittle HTML Selector Audit & Fix Summary

## Problem Identified

The code stopped working because it relied on **randomly generated CSS class names** that change every time the website is redeployed. When Lindblad Expeditions updated their site, class names like `drDbhx` changed to `fFpROU`, breaking the selectors.

## Critical Fix Applied

### departure_parser.py (LINE 42-43) - **FIXED** ✅

**Old brittle code:**

```python
date_range_locator = departure.locator("p[class*='drDbhx']")
```

**New robust code:**

```python
# Use robust selector: find all <p> tags, filter for date-like content
# Old brittle selector was: p[class*='drDbhx'] (class names change on redeploy)
date_range_locator = departure.locator("p")
# Then filter out prices containing "$"
date_texts = [text.strip() for text in all_p_texts if text.strip() and "$" not in text]
```

**Why this works:** Instead of relying on random CSS class names, we:

1. Select all `<p>` tags in the departure element
2. Filter out non-date content (prices with "$")
3. Extract the first two remaining items as start/end dates

## Remaining Brittle Selectors

### High Risk (Using randomly generated class patterns)

#### trip_parser.py

1. **Line 47, 58:** `[class^='hit_container__']` - Trip container
2. **Line 70:** `[class^='card_name__']` - Trip name link
3. **Line 84:** `[class^='card_image__']` - Trip image
4. **Line 88:** `[class^='card_list__']` and `[class^='card_destination__']` - Destinations
5. **Line 97:** `[class^='card_displayNone']` - Hidden trip indicator

#### departure_parser.py

1. **Line 22:** `[class^='hits_departureHitsContainer__']` - Departure container

#### category_parser.py

1. **Line 95:** `[class*='pax-icons_']` - Occupancy icons

### Medium Risk (Using data attributes - more stable)

These are **less likely to break** as they appear to be intentional identifiers:

- `[data-testid='departure-hit-year']` ✅
- `[data-testid='cabin-card']` ✅
- `[data-testid='category-card']` ✅
- `[data-land-expedition='true']` ✅
- `button[data-style='button']` ⚠️
- `button[data-variant='text'][data-style='link']` ⚠️

### Low Risk (Stable selectors)

- `has_text="..."` filters ✅
- Standard HTML tags: `button`, `p`, `h2`, `h3`, `span`, `li`, `ul` ✅

## Recommendations for Future Robustness

### Priority 1: Replace all `[class^=...]` selectors

Instead of class-based selectors, use:

1. **Semantic HTML structure** - traverse from parent to child by tag names
2. **Text content matching** - `has_text` filters
3. **Data attributes** - prefer `data-testid` when available
4. **Multiple fallback strategies** - try several approaches

### Priority 2: Add defensive code

```python
# Example defensive pattern:
try:
    # Try primary selector
    element = page.locator("[data-testid='element']")
    if element.count() == 0:
        # Fallback to structural selector
        element = page.locator("div > p")
except Exception:
    # Ultimate fallback
    element = page.locator("p")
```

### Priority 3: Regular testing

Set up automated tests that run against the live website to detect breakages immediately after site updates.

## Testing Results

✅ **Fixed departure parser tested successfully:**

- Correctly extracted 4 departures from Panama Canal trip
- Dates parsed accurately: Dec 7, Dec 14, Jan 9, Jan 16
- Ship names and booking URLs captured correctly

## Next Steps

1. ✅ **DONE:** Fixed critical `p[class*='drDbhx']` selector in departure_parser.py
2. **RECOMMENDED:** Replace remaining `[class^=...]` selectors in trip_parser.py
3. **RECOMMENDED:** Add fallback logic for departure container selector
4. **RECOMMENDED:** Implement monitoring/alerting for scraper failures
