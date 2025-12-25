# Notion Curator Observations Database Schema

**Purpose:** Curator's oversight reports on system efficiency, cost optimization, limitations, and improvement suggestions

---

## Properties

| Property | Type | Options/Format |
|----------|------|----------------|
| **Report Title** | Title | Brief description (e.g., "Week 1 Efficiency Analysis") |
| **Report Date** | Date | Date of observation/report |
| **Report Type** | Select | Daily Summary, Weekly Analysis, Cost Review, Efficiency Audit, Limitation Report, Tool Request, Incident Review, Performance Analysis |
| **Observation Category** | Multi-select | Cost Optimization, Efficiency Improvement, Tool Gap, Restriction Issue, Agent Behavior, Data Quality, Budget Impact, Pattern Discovery |
| **Severity/Priority** | Select | Critical, High, Medium, Low, Informational |
| **Status** | Select | New, Under Review, Addressed, Deferred, Monitoring |
| **Summary** | Text (long) | Brief executive summary of findings |
| **Detailed Findings** | Text (long) | Full analysis and observations |
| **Metrics** | Text | Key numbers (cost, time, success rate, etc.) |
| **Cost Impact** | Number | Estimated savings or cost if implemented ($) |
| **Efficiency Gain** | Number | Estimated time saved (hours) or performance improvement (%) |
| **Affected Agents** | Multi-select | extractor, validator, storage, curator, website-validator |
| **Suggested Actions** | Text (long) | Recommended next steps |
| **Tools Needed** | Text | New tools or capabilities required |
| **Restrictions Identified** | Text (long) | Limitations discovered |
| **Implementation Complexity** | Select | Simple, Moderate, Complex, Requires Architecture Change |
| **Implemented** | Checkbox | Whether suggestion was implemented |
| **Implementation Date** | Date | When implemented |
| **Actual Impact** | Text | Real results after implementation |
| **Related Errors** | Text | Error IDs from Error Log database |
| **Related Extractions** | Text | Extraction IDs that illustrate the issue |
| **Supporting Data** | Text (long) | Logs, examples, statistics |

---

## Views

### 1. Pending Review (Default)
- **Filter:** Status = "New" OR Status = "Under Review"
- **Sort:** Severity/Priority (Critical first), Report Date (newest first)
- **Purpose:** What needs human attention

### 2. High Impact Opportunities
- **Filter:** Cost Impact > 5 OR Efficiency Gain > 10
- **Sort:** Cost Impact (descending)
- **Purpose:** Biggest wins to prioritize

### 3. By Category
- **Group by:** Observation Category
- **Sort:** Report Date (newest first)
- **Purpose:** See patterns in similar observations

### 4. Tool Requests
- **Filter:** Observation Category contains "Tool Gap"
- **Sort:** Severity/Priority, Report Date
- **Purpose:** Track what tools are needed

### 5. Implemented Improvements
- **Filter:** Implemented = TRUE
- **Sort:** Implementation Date (newest first)
- **Purpose:** Track what's been done and actual impact

### 6. Cost Savings Tracker
- **Filter:** Cost Impact > 0 AND Implemented = TRUE
- **Sort:** Cost Impact (descending)
- **Purpose:** Calculate total savings achieved

### 7. Weekly Summaries
- **Filter:** Report Type = "Daily Summary" OR "Weekly Analysis"
- **Sort:** Report Date (newest first)
- **Purpose:** Regular oversight reports

---

## Report Types Explained

### Daily Summary
- **Frequency:** Every day
- **Content:** Pages processed, extractions created, errors encountered, cost estimate
- **Purpose:** Track daily progress

### Weekly Analysis
- **Frequency:** Every week
- **Content:** Trends, patterns, success rates, cost analysis
- **Purpose:** Identify weekly patterns

### Cost Review
- **Frequency:** As needed (when costs spike or monthly)
- **Content:** Cost breakdown, budget status, optimization opportunities
- **Purpose:** Budget management

### Efficiency Audit
- **Frequency:** Monthly or when performance degrades
- **Content:** Agent performance metrics, bottlenecks, optimization suggestions
- **Purpose:** System optimization

### Limitation Report
- **Frequency:** As encountered
- **Content:** Restrictions discovered, workarounds, long-term solutions needed
- **Purpose:** Track technical debt

### Tool Request
- **Frequency:** As needed
- **Content:** Missing capabilities, tools that would help, use cases
- **Purpose:** Feature requests

### Incident Review
- **Frequency:** After major errors
- **Content:** What happened, why, how to prevent, lessons learned
- **Purpose:** Prevent recurrence

### Performance Analysis
- **Frequency:** Monthly
- **Content:** Success rates, confidence scores, lineage quality, extraction accuracy
- **Purpose:** Quality tracking

---

## Sample Reports

### Example 1: Cost Optimization Opportunity

**Report Title:** "Extractor Re-requesting Same Snapshot Multiple Times"

**Report Type:** Efficiency Audit

**Observation Category:** Cost Optimization, Efficiency Improvement

**Severity/Priority:** High

**Summary:**
```
Observed extractor agent re-fetching the same snapshot 3 times for a single page
extraction. Each fetch costs ~$0.05 in API calls. This happens when extractor
retries on low confidence - it should reuse the existing snapshot instead of
fetching again.
```

**Detailed Findings:**
```
Analysis of thread logs from 2025-12-24:
- FC Board page extraction
- Extractor fetched page at 10:15 AM (snapshot ID: abc-123)
- Got low confidence (0.55)
- Triggered re-extraction
- RE-FETCHED same page at 10:18 AM (snapshot ID: def-456)
- Same content, different snapshot ID
- Cost: $0.05 × 2 = $0.10 wasted per page

For 60 pages, if this happens 20% of the time:
60 × 0.20 × $0.05 = $0.60/month wasted
```

**Suggested Actions:**
```
1. Modify extractor to check for existing snapshot by URL + date
2. If snapshot exists from today, reuse it
3. Only fetch new snapshot if >24 hours old
4. Update re-extraction logic to pass snapshot_id instead of URL
```

**Tools Needed:**
```
None - just logic change in extractor agent
```

**Cost Impact:** $0.60 (monthly savings)

**Implementation Complexity:** Simple

---

### Example 2: Tool Gap

**Report Title:** "Need Semantic Search for Finding Similar Extractions"

**Report Type:** Tool Request

**Observation Category:** Tool Gap, Efficiency Improvement

**Severity/Priority:** Medium

**Summary:**
```
Validator agent spends significant time comparing new extractions to existing
ones to check for duplicates. Currently doing string matching, which misses
semantic duplicates like "MSP430FR Microcontroller" vs "MSP430FR MCU".

pgvector is installed but not being used. Could save ~30 seconds per validation.
```

**Detailed Findings:**
```
Current validation process:
1. Validator gets new extraction: "RP2350 Processor"
2. Queries staging_extractions WHERE candidate_key LIKE '%RP2350%'
3. Manual string comparison
4. Takes ~30 seconds, makes 5-10 LLM calls

With semantic search:
1. Generate embedding for "RP2350 Processor"
2. Query pgvector for similar embeddings
3. Find "RP2350 Microcontroller" (91% similarity)
4. Takes ~2 seconds, 1 LLM call

Cost savings: ~$0.02 per validation × 342 extractions = $6.84
Time savings: 28 seconds × 342 = 2.6 hours
```

**Suggested Actions:**
```
1. Add embedding column to staging_extractions
2. Generate embeddings during extraction
3. Update validator to use pgvector similarity search
4. Set threshold at 0.85 similarity
```

**Tools Needed:**
```
- pgvector (already installed ✓)
- Embedding model (Claude has built-in embeddings)
```

**Cost Impact:** $6.84 (monthly savings)

**Efficiency Gain:** 2.6 hours

**Implementation Complexity:** Moderate

---

### Example 3: Restriction Issue

**Report Title:** "Lineage Verification Failing for PDF-Based Pages"

**Report Type:** Limitation Report

**Observation Category:** Restriction Issue, Data Quality

**Severity/Priority:** High

**Summary:**
```
Discovered that pages serving PDF documentation instead of HTML fail lineage
verification. PDF text extraction changes formatting, so exact quote matching
doesn't work. Lineage confidence drops to 0.4-0.5.
```

**Detailed Findings:**
```
Affected pages (4 out of 60):
- /datasheets/MSP430FR5969.pdf
- /datasheets/RP2350.pdf
- /guides/power_budgeting.pdf
- /guides/thermal_analysis.pdf

Problem:
1. PDF is fetched and stored in raw_snapshots.payload
2. PDF text extraction converts to plain text
3. Text loses formatting (line breaks, spacing changes)
4. Evidence quote from extraction doesn't match byte-for-byte
5. Lineage verification fails

Example:
Original PDF: "MSP430FR5969\nUltra-Low-Power\nMicrocontroller"
Extracted: "MSP430FR5969 Ultra-Low-Power Microcontroller"
Quote: "MSP430FR5969 Ultra-Low-Power Microcontroller"
Match result: FAIL (because original has \n)
```

**Restrictions Identified:**
```
1. PDF text extraction is inherently lossy
2. Byte offset tracking doesn't work with reformatted text
3. Can't achieve 1.0 lineage confidence with PDFs
```

**Suggested Actions:**
```
SHORT-TERM:
1. Accept 0.5-0.7 lineage confidence for PDF sources
2. Add "source_format" field to raw_snapshots (HTML, PDF, etc.)
3. Adjust lineage threshold based on source format
4. Mark PDF extractions for mandatory human review

LONG-TERM:
1. Store both raw PDF and extracted text
2. Calculate checksums on normalized text (strip whitespace)
3. Use fuzzy matching for PDF lineage verification
4. Consider extracting directly from PDF annotations/metadata
```

**Cost Impact:** $0 (quality issue, not cost issue)

**Implementation Complexity:** Moderate (short-term), Complex (long-term)

---

### Example 4: Pattern Discovery

**Report Title:** "High Confidence Extractions Clustered on Certain Pages"

**Report Type:** Performance Analysis

**Observation Category:** Pattern Discovery, Data Quality

**Severity/Priority:** Informational

**Summary:**
```
Analysis of 6 completed extractions shows confidence scores vary by page type:
- Component datasheets: 0.85-0.95 confidence
- Tutorial pages: 0.60-0.75 confidence
- Architecture diagrams: 0.55-0.70 confidence

Suggests extractor performs better with structured technical documentation.
```

**Detailed Findings:**
```
Breakdown by page type:
Component datasheets (2 extractions):
- Average confidence: 0.90
- Lineage confidence: 0.67 (retroactive)
- Attributes: Well-structured, consistent format

Tutorial pages (2 extractions):
- Average confidence: 0.68
- Lineage confidence: 0.67 (retroactive)
- Attributes: Narrative text, less structured

Architecture diagrams (2 extractions):
- Average confidence: 0.63
- Lineage confidence: 0.67 (retroactive)
- Attributes: Heavy on visual info, light on text

Hypothesis: Extractor prompt is optimized for technical specs, not tutorials.
```

**Suggested Actions:**
```
1. Create page-type classifier (runs before extraction)
2. Use different prompts based on page type:
   - Datasheet prompt: Focus on specs, parameters, technical details
   - Tutorial prompt: Extract learning objectives, procedures, outcomes
   - Diagram prompt: Describe visual relationships, components shown
3. Test if specialized prompts improve confidence
4. Monitor confidence scores by page type after change
```

**Efficiency Gain:** Potential 10-15% confidence improvement on tutorial pages

**Implementation Complexity:** Moderate

---

## Integration with Daily Workflow

### Curator Daily Routine

**Morning (after daily extraction run):**
1. Review Error Log for overnight errors
2. Create Daily Summary report with metrics
3. Note any anomalies or patterns

**Weekly:**
1. Generate Weekly Analysis report
2. Review cost vs budget
3. Identify top 3 optimization opportunities
4. Create Tool Request or Efficiency Audit reports as needed

**Monthly:**
1. Performance Analysis report
2. Cost Review report
3. Review all "Under Review" observations
4. Update implemented improvements with actual impact

---

## Metrics to Track

### Cost Metrics
- Daily API cost
- Cost per page processed
- Cost per extraction
- Budget utilization (% of $20)
- Savings from optimizations

### Efficiency Metrics
- Pages processed per day
- Extractions per page (average)
- Time per extraction
- Re-extraction rate
- Error rate

### Quality Metrics
- Average confidence score
- Average lineage confidence
- Percentage with perfect lineage (1.0)
- Approval rate (human review)
- Rejection rate

### Agent Performance
- Extractor success rate
- Validator pass rate
- Storage promotion rate
- Curator intervention rate

---

## Automation Opportunities

### Automated Metric Collection
```python
# Curator runs this daily to populate metrics
def generate_daily_metrics():
    return {
        'pages_processed': count_pages_today(),
        'extractions_created': count_extractions_today(),
        'errors_encountered': count_errors_today(),
        'cost_estimate': calculate_daily_cost(),
        'avg_confidence': avg_confidence_today(),
        'avg_lineage': avg_lineage_today(),
        'budget_utilization': cost_to_date / monthly_budget
    }
```

### Automated Pattern Detection
```python
# Curator runs this weekly to find patterns
def detect_efficiency_patterns():
    patterns = []

    # Check for recurring errors
    recurring = find_recurring_errors()
    if recurring:
        patterns.append({
            'type': 'recurring_error',
            'severity': 'high',
            'description': f'Error {recurring} occurred {count} times'
        })

    # Check for cost spikes
    if daily_cost > avg_cost * 1.5:
        patterns.append({
            'type': 'cost_spike',
            'severity': 'medium',
            'description': f'Cost {daily_cost} is 50% above average'
        })

    # Check for confidence drop
    if avg_confidence < 0.7:
        patterns.append({
            'type': 'quality_decline',
            'severity': 'high',
            'description': f'Confidence dropped to {avg_confidence}'
        })

    return patterns
```

---

## Benefits of Curator Observations

1. **Proactive Problem Detection** - Spot issues before they become critical
2. **Cost Control** - Identify waste and optimize spending
3. **Quality Improvement** - Track and improve extraction accuracy
4. **Knowledge Building** - Learn what works and what doesn't
5. **Accountability** - Document decisions and their outcomes
6. **Pattern Recognition** - Find systemic issues vs one-off errors
7. **Continuous Improvement** - Data-driven optimization over time

This transforms the curator from reactive (fixing errors) to proactive (preventing them and optimizing the system).
