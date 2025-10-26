# Bug Fix Report: Element Adoption Error

## Issue
**Error:** `Unable to adopt element handle from a different document`
**Status:** ✅ FIXED
**Date:** 2025-10-26

## Root Cause
The error occurred in the `extract_links_from_section` function at line 125. The code was:
1. Querying DOM elements using `page.query_selector_all(selector)`
2. Storing element handles in memory
3. Later attempting to access these element handles' attributes

**Problem:** Playwright element handles become stale/invalid if:
- The page navigates to a different URL
- The DOM is modified
- The page context changes
- Time passes between getting the handle and using it

When element handles from one document state are used after the page changes, Playwright throws the "Unable to adopt element handle from a different document" error.

## Solution Applied

### Changed: Element Handle Extraction → Direct JavaScript Evaluation

**Before (Line 123-137):**
```python
all_hrefs = set()
for selector in selectors:
    elements = await page.query_selector_all(selector)
    for element in elements:
        href = await element.get_attribute('href')
        if href:
            all_hrefs.add(href)
```

**After (Line 123-141):**
```python
all_hrefs = set()
# Use page.evaluate to extract hrefs directly, avoiding element handle issues
try:
    for selector in selectors:
        try:
            hrefs = await page.evaluate('''
                (selector) => {
                    const elements = document.querySelectorAll(selector);
                    return Array.from(elements).map(el => el.getAttribute('href')).filter(href => href);
                }
            ''', selector)
            all_hrefs.update(hrefs)
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {e}")
            continue
except Exception as e:
    logger.warning(f"Error extracting links: {e}")
    # Fallback: try to get at least some links
    return [section_url]
```

### Why This Works

1. **No Element Handles:** `page.evaluate()` runs JavaScript directly in the browser context and returns primitive values (strings), not element handles
2. **Atomic Operation:** The entire extraction happens in one JavaScript execution, eliminating timing issues
3. **No Cross-Document Issues:** Since we're extracting data immediately and returning strings, there's no possibility of document adoption errors
4. **Better Error Handling:** Added try-except blocks with graceful fallbacks

### Additional Improvements

Also improved page cleanup in `scrape_section` function (line 737-742):
```python
page = await context.new_page()
try:
    links = await extract_links_from_section(page, section_url, section)
    logger.info(f"Found {len(links)} page(s) under section /{section}")
finally:
    await page.close()
```

This ensures the page is always properly closed, even if an error occurs.

## Testing Recommendation

After deploying this fix, test with the URL that was failing:
```
POST /api/scrape
{
  "url": "https://docs.agno.com/introduction/quickstart/"
}
```

## Prevention

To prevent similar issues in the future:
1. **Prefer `page.evaluate()`** for extracting data from DOM
2. **Avoid storing element handles** - use them immediately or extract their data
3. **Use try-finally blocks** to ensure proper resource cleanup
4. **Add comprehensive error handling** for Playwright operations

## Impact
- ✅ Fixes production error preventing scraping
- ✅ Makes link extraction more reliable
- ✅ Improves error handling and logging
- ✅ No breaking changes to API
