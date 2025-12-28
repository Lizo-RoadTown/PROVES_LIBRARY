# Mermaid Diagram Syntax Rules

Comprehensive rules compiled from official Mermaid documentation (v10+).

## Critical Syntax Rules

### 1. NO HTML Tags
- ❌ **NEVER use `<br/>`, `<span>`, `<div>`, or any HTML tags** in flowchart nodes
- ✅ Use simple text or markdown formatting with backticks
- Exception: `<br/>` is ONLY allowed in sequence diagrams for line breaks

### 2. Special Characters - CRITICAL

#### Colons (`:`) - Multiple Breaking Contexts
- ❌ **Colons in subgraph labels break parsing**: `subgraph "Layer 1: App"` → FAILS
- ✅ **Remove colons from subgraph labels**: `subgraph "Layer 1 App"` → WORKS
- ❌ **Double colons in text ALWAYS break**: `Status::OK` → FAILS
- ✅ **Remove double colons**: `Status OK` or `Status_OK` → WORKS
- ❌ **Colons in sequence note text after first colon**: `Note over A: Step 1: Details` → FAILS
- ✅ **Remove colons from note content**: `Note over A: Step 1 Details` → WORKS
- ✅ **Single colon separating label from text is OK**: `Note over A: Some text` → WORKS
- ✅ **Colons OK in link text**: `A -->|Status: OK| B` → WORKS

#### Forward Slashes (`/`) - Breaking in Node Labels
- ❌ **File paths without quotes break parsing**: `DEV[/dev/i2c-1]` → FAILS
- ✅ **Quote all paths with slashes**: `DEV["/dev/i2c-1"]` → WORKS
- ❌ **URLs without quotes can break**: `NODE[http://example.com]` → FAILS
- ✅ **Quote URLs in node labels**: `NODE["http://example.com"]` → WORKS
- ✅ **Slashes in shape syntax are OK**: `A[/Parallelogram/]` → WORKS (defined shape)
- ⚠️ **Slashes in plain text or tables are OK** (not in diagram code)

#### Quotes - When Required
- ✅ **Quote text with forward slashes**: `id["/path/to/file"]`
- ✅ **Quote text with parentheses**: `id["Text with (parens)"]`
- ✅ **Quote text with special symbols**: `id["Price: $50"]`
- ✅ Use entity codes: `#` (e.g., `#9829;` for ♥)
- ✅ For markdown: Use backticks: `` id["`**Bold** text`"] ``

#### Reserved Words
- ❌ Word "end" must be capitalized or quoted: `End`, `[end]`, `{end}`
- ❌ Starting with "o" or "x" creates special edges: `A---oB` = circle edge

### 3. Subgraph Syntax
```mermaid
subgraph id [Label Text]
    nodes...
end
```
- ✅ Must have space between id and bracket
- ❌ **NO colons in labels**: `subgraph "Layer 1: App"` → BREAKS - use `subgraph "Layer 1 App"`
- ✅ Labels can be quoted for special chars: `subgraph "System/Network"`
- ✅ Plain text labels work: `subgraph id` or `subgraph "Text Label"`

### 4. Node Labels

#### Simple text
```mermaid
id[This is text]
id(Round edges)
id{Diamond shape}
```

#### Unicode/Special characters
```mermaid
id["Unicode: ❤ works"]
id["Escaped: #9829;"]
```

#### Markdown formatting (requires config)
```mermaid
---
config:
  flowchart:
    htmlLabels: false
---
flowchart LR
    id["`**Bold** and *italic*`"]
```

### 5. Line Breaks

#### Flowcharts
- ❌ NO `<br/>` tags
- ✅ Markdown formatting with newlines:
```mermaid
id["`Line 1
Line 2
Line 3`"]
```

#### Sequence Diagrams
- ✅ `<br/>` is allowed:
```mermaid
Alice->John: Hello<br/>World
```
- ✅ In participant aliases:
```mermaid
participant A as Alice<br/>Johnson
```

### 6. Links/Edges

#### Arrow types
```
-->  solid with arrow
---  solid no arrow
-.-> dotted with arrow
-.-  dotted no arrow
==>  thick with arrow
===  thick no arrow
--x  solid with cross
--o  solid with circle
<<-->> bidirectional (v11.0.0+)
```

#### Link text
```mermaid
A -->|Text on link| B
A -- Text --- B
A ---|Text| B
```

#### Edge IDs (v11.3.0+)
```mermaid
A e1@--> B
e1@{ animate: true }
```

### 7. Comments
```mermaid
%% This is a comment
%% Must start line with %%
flowchart LR
    A --> B %% inline comments NOT supported
```

### 8. Styling

#### Node styling
```mermaid
style id1 fill:#f9f,stroke:#333,stroke-width:4px
```

#### Classes
```mermaid
classDef className fill:#f9f
class nodeId className
A:::className --> B
```

#### Link styling
```mermaid
linkStyle 0 stroke:#ff3,stroke-width:4px
```

## Flowchart-Specific Rules

### Node Shapes
```mermaid
id[Rectangle]
id(Round edges)
id([Stadium])
id[[Subroutine]]
id[(Database)]
id((Circle))
id>Asymmetric]
id{Diamond}
id{{Hexagon}}
id[/Parallelogram/]
id[\Parallelogram alt\]
id[/Trapezoid\]
id[\Trapezoid alt/]
id(((Double circle)))
```

### Direction
```mermaid
flowchart TB   %% Top to Bottom
flowchart TD   %% Top-Down (same as TB)
flowchart BT   %% Bottom to Top
flowchart LR   %% Left to Right
flowchart RL   %% Right to Left
```

### Subgraph Direction
```mermaid
flowchart LR
    subgraph id
        direction TB
        A --> B
    end
```

## Sequence Diagram-Specific Rules

### Participants
```mermaid
participant A as Alice
actor B as Bob
participant C@{ "type" : "boundary" }
participant D@{ "type" : "database" }
```

### Messages
```
->   solid no arrow
-->  dotted no arrow
->>  solid with arrow
-->> dotted with arrow
-x   solid with cross
--x  dotted with cross
-)   solid async
--)  dotted async
<<->> bidirectional (v11.0.0+)
```

### Activations
```mermaid
activate Alice
deactivate Alice
%% Or shorthand:
Alice->>+Bob: Message
Bob-->>-Alice: Reply
```

### Notes
```mermaid
Note right of Alice: Text
Note left of Alice: Text
Note over Alice,Bob: Text
```
- ⚠️ **CRITICAL**: Text after first colon cannot contain more colons
- ❌ **BREAKS**: `Note over A: Step 1: Initialize device` 
- ✅ **WORKS**: `Note over A: Step 1 Initialize device`
- ✅ **Single colon separating label is OK**: `Note over A: Any text here`

### Loops/Alt/Par
```mermaid
loop Every minute
    A->>B: Check
end

alt Success
    A->>B: OK
else Failure
    A->>B: Error
end

par Parallel 1
    A->>B: Task 1
and Parallel 2
    A->>C: Task 2
end
```

## Common Errors and Fixes

### Error: "Unable to render rich display"
**Causes:** 
- HTML tags like `<br/>` in flowcharts
- Colons in subgraph labels or node text
- Unquoted special characters

**Fix:**
```mermaid
%% BAD
flowchart LR
    A[Line 1<br/>Line 2]
    B["Layer 1: Application"]
    C[Status::OK]
    D[/dev/i2c-1]

%% GOOD
flowchart LR
    A["`Line 1
    Line 2`"]
    B["Layer 1 Application"]
    C[Status OK]
    D["/dev/i2c-1"]
```

### Error: "Unexpected character at offset X"
**Causes:**
- Colons in subgraph labels: `subgraph "Layer 1: App"`
- Colons after colon in sequence notes: `Note over A: Step 1: Details`
- Unquoted forward slashes: `/dev/i2c-1`

**Fix:**
```mermaid
%% BAD
subgraph "API: v2"
    node[Address: 0x68]
end
Note over A: Step 1: Initialize

%% GOOD
subgraph "API v2"
    node[Address 0x68]
end
Note over A: Step 1 Initialize
```

### Error: "Lexical error on line X. Unrecognized text"
**Causes:**
- Forward slashes without quotes: `node[/path/to/file]`
- File paths or URLs without quotes: `/dev/i2c-1`

**Fix:**
```mermaid
%% BAD
flowchart LR
    DEV[/dev/i2c-1 device]
    URL[http://example.com]

%% GOOD
flowchart LR
    DEV["/dev/i2c-1 device"]
    URL["http://example.com"]
end

%% GOOD
subgraph "API v2"
    node[Address 0x68]
end
```

### Error: Nodes not rendering
**Cause:** Reserved word "end" or starting with "o"/"x"

**Fix:**
```mermaid
%% BAD
A --> end
dev --> ops

%% GOOD
A --> End
dev --> Ops
```

## Configuration

### Frontmatter
```mermaid
---
title: My Diagram
config:
  theme: forest
  look: handDrawn
  layout: elk
flowchart:
  htmlLabels: false
---
flowchart LR
    A --> B
```

### Directives
```mermaid
%%{init: {'theme':'forest'}}%%
flowchart LR
    A --> B
```

## Best Practices

1. **Always test diagrams** in Mermaid Live Editor first
2. **Use semantic naming** for node IDs
3. **Keep labels concise** - use notes for details
4. **Prefer simple text** over complex formatting
5. **Comment your diagrams** with %% for complex logic
6. **Use consistent styling** with classes
7. **Validate special characters** before committing
8. **Avoid nesting** HTML or special syntax
9. **Check version compatibility** for new features
10. **Document your diagram intent** in surrounding markdown

## Validation Checklist

- [ ] No `<br/>` tags in flowcharts
- [ ] No HTML tags in any nodes
- [ ] No colons in node labels (except links)
- [ ] No `::` double colons anywhere
- [ ] Word "end" is capitalized or quoted
- [ ] Subgraph syntax has space: `subgraph id [label]`
- [ ] All quotes are properly closed
- [ ] Comments start with `%%`
- [ ] Direction specified (TB/LR/etc)
- [ ] Special characters escaped or quoted

## Resources

- [Official Mermaid Docs](https://mermaid.js.org/)
- [Flowchart Syntax](https://mermaid.js.org/syntax/flowchart.html)
- [Sequence Diagram Syntax](https://mermaid.js.org/syntax/sequenceDiagram.html)
- [Mermaid Live Editor](https://mermaid.live/)

---

**Version:** Based on Mermaid v10+ (GitHub rendering)
**Last Updated:** December 28, 2024
