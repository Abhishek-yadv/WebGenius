# Performance Optimization Guide

## 🚀 Current Performance Bottlenecks

### 1. **Concurrent Page Limit** (Line 742)
```python
max_concurrent = 5  # Current setting
```
**Issue**: Only 5 pages scraped at a time

### 2. **Batch Delay** (Line 753)
```python
await asyncio.sleep(1)  # 1 second delay between batches
```
**Issue**: Adds unnecessary wait time

### 3. **Wait Strategy** (Lines 97, 156)
```python
wait_until="networkidle"  # Waits for all network requests
```
**Issue**: Very slow, waits for everything to load

### 4. **Timeout Values** (Lines 97, 156)
```python
timeout=45000  # 45 seconds
timeout=60000  # 60 seconds
```
**Issue**: Too long for most pages

---

## ⚡ Optimization Strategies

### Strategy 1: **Increase Concurrency** (Easy - High Impact)

**Current Speed**: 5 pages at a time  
**Optimized Speed**: 10-20 pages at a time  
**Expected Speedup**: 2-4x faster

```python
# Line 742: Change from
max_concurrent = 5

# To
max_concurrent = 15  # Good balance for most servers
```

### Strategy 2: **Reduce/Remove Batch Delays** (Easy - High Impact)

**Current**: 1 second delay between batches  
**Optimized**: 0.2-0.5 seconds or remove entirely  
**Expected Speedup**: 20-50% faster

```python
# Line 753: Change from
await asyncio.sleep(1)

# To
await asyncio.sleep(0.3)  # Or remove completely for max speed
```

### Strategy 3: **Faster Page Loading** (Medium - Very High Impact)

**Current**: `wait_until="networkidle"` (waits for everything)  
**Optimized**: `wait_until="domcontentloaded"` (waits for HTML only)  
**Expected Speedup**: 2-3x faster per page

```python
# Line 97 and 156: Change from
await page.goto(url, timeout=45000, wait_until="networkidle")

# To
await page.goto(url, timeout=20000, wait_until="domcontentloaded")
```

### Strategy 4: **Reduce Timeouts** (Easy - Medium Impact)

**Current**: 45-60 seconds  
**Optimized**: 15-20 seconds  
**Expected Speedup**: Faster failure recovery

```python
# Lines 97, 156
timeout=20000  # 20 seconds instead of 45-60
```

### Strategy 5: **Skip Unnecessary Waits** (Medium - High Impact)

**Current**: Waits for specific selectors  
**Optimized**: Skip selector waits if not needed  
**Expected Speedup**: 1-2 seconds per page

```python
# Lines 100-103: Make selector wait optional
try:
    await page.wait_for_selector('article, main', timeout=2000)  # Reduce to 2s
except:
    pass  # Continue anyway
```

### Strategy 6: **Disable Images/CSS** (Advanced - Very High Impact)

**Current**: Loads everything  
**Optimized**: Block images, CSS, fonts  
**Expected Speedup**: 3-5x faster, 70% less bandwidth

```python
# Add to browser context creation (Line 711)
context = await browser.new_context(
    viewport={"width": 1920, "height": 1080},
    user_agent="...",
    locale='en-US',
    timezone_id='America/New_York',
    # Add these lines:
    ignore_https_errors=True,
    bypass_csp=True,
)

# Block unnecessary resources
await context.route("**/*", lambda route: (
    route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"]
    else route.continue_()
))
```

### Strategy 7: **Reuse Browser Pages** (Advanced - Medium Impact)

**Current**: Creates new page for each URL  
**Optimized**: Reuse page instances  
**Expected Speedup**: 10-20% faster

```python
# Instead of creating/closing pages repeatedly, use a pool
```

---

## 🎯 Quick Win Implementation

Here's a ready-to-use optimized version with **minimal changes**:

### Option A: Conservative (Safe for most sites)
```python
# Line 742
max_concurrent = 10  # 2x speed

# Line 753
await asyncio.sleep(0.5)  # 50% faster

# Lines 97, 156
timeout=25000, wait_until="domcontentloaded"  # 2x faster loading
```

**Expected Total Speedup**: **3-4x faster** ✅

### Option B: Aggressive (Fast, but may hit rate limits)
```python
# Line 742
max_concurrent = 20  # 4x speed

# Line 753
# Remove the await asyncio.sleep(1) completely

# Lines 97, 156
timeout=15000, wait_until="domcontentloaded"  # 3x faster loading
```

**Expected Total Speedup**: **6-8x faster** ⚡

### Option C: Maximum Speed (May be blocked by some sites)
```python
max_concurrent = 30
# No delays
timeout=10000, wait_until="domcontentloaded"
# + Block images/CSS (see Strategy 6)
```

**Expected Total Speedup**: **10-15x faster** 🚀

---

## 📊 Performance Comparison

| Configuration | Pages/Min | 100 Pages Time | Risk Level |
|--------------|-----------|----------------|------------|
| **Current** | ~6-8 | ~15 minutes | Low |
| **Conservative** | ~20-25 | ~4-5 minutes | Low |
| **Aggressive** | ~40-50 | ~2 minutes | Medium |
| **Maximum** | ~80-100 | ~1 minute | High |

---

## ⚠️ Important Considerations

### Rate Limiting
- Some sites may block you if you scrape too fast
- Start with conservative settings and increase gradually
- Monitor for HTTP 429 (Too Many Requests) errors

### Server Impact
- Be respectful of the target server
- Don't overwhelm small/personal sites
- Consider adding delays for smaller sites

### Detection Risk
- Faster = More likely to be detected as bot
- Use conservative settings for anti-bot sites
- Maximum settings work best for your own sites or APIs

### Error Handling
- Shorter timeouts = more timeout errors
- May need to implement retry logic
- Some slow pages may fail with aggressive settings

---

## 🛠️ Implementation Steps

### Step 1: Start Conservative
1. Change `max_concurrent` to 10
2. Reduce delays to 0.5 seconds
3. Change to `domcontentloaded`
4. Test on a small section

### Step 2: Monitor & Adjust
- Check for errors in logs
- Verify content quality
- Monitor for rate limiting (429 errors)

### Step 3: Increase Gradually
- If working well, increase to 15 concurrent
- Reduce delays further
- Eventually try blocking images/CSS

---

## 🔧 Quick Implementation

Want me to apply these optimizations? I can implement:
- ✅ Conservative settings (3-4x faster, very safe)
- ⚡ Aggressive settings (6-8x faster, mostly safe)
- 🚀 Maximum settings (10-15x faster, use carefully)

Which level would you like?
