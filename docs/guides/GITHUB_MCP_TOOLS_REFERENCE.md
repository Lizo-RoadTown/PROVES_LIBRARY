# GitHub MCP Tools Reference

## Overview

The GitHub MCP (Model Context Protocol) server provides ~40 tools for interacting with GitHub repositories, issues, pull requests, and workflows. These tools enable autonomous agents to perform GitHub operations programmatically.

## Tool Categories

### 1. Repository Management (7 tools)

#### `github_get_repository`
- **Purpose**: Get repository details
- **Usage**: Fetch repo metadata, default branch, description, topics
- **Example**: Get PROVES_LIBRARY repo details

#### `github_create_repository`
- **Purpose**: Create a new repository
- **Usage**: Create repos for component libraries, examples, or documentation

#### `github_update_repository`
- **Purpose**: Update repository settings
- **Usage**: Change description, topics, default branch, visibility

#### `github_delete_repository`
- **Purpose**: Delete a repository (use with caution!)
- **Usage**: Clean up test repos or deprecated projects

#### `github_list_repositories`
- **Purpose**: List repositories for a user or organization
- **Usage**: Discover all PROVES-related repos

#### `github_fork_repository`
- **Purpose**: Fork a repository
- **Usage**: Fork F´ or other repos for customization

#### `github_get_repository_topics`
- **Purpose**: Get repository topics/tags
- **Usage**: Categorize and discover repos by topic

---

### 2. File Operations (8 tools)

#### `github_get_file_contents`
- **Purpose**: Read file content from repository
- **Usage**: Fetch markdown docs, code files, configuration
- **PROVES Use Case**: Sync F´ and PROVES Kit documentation

#### `github_create_or_update_file`
- **Purpose**: Create or update a file in repository
- **Usage**: Update documentation, commit code changes
- **PROVES Use Case**: Auto-commit curator-normalized entries

#### `github_delete_file`
- **Purpose**: Delete a file from repository
- **Usage**: Remove deprecated docs or code

#### `github_get_directory_contents`
- **Purpose**: List files in a directory
- **Usage**: Explore repo structure, find all markdown files
- **PROVES Use Case**: Discover all docs in `docs/` directory

#### `github_search_code`
- **Purpose**: Search code across GitHub
- **Usage**: Find code patterns, component usage examples
- **PROVES Use Case**: Find all I2C implementations across F´

#### `github_get_commit`
- **Purpose**: Get commit details
- **Usage**: Track changes, get commit SHA, author, message

#### `github_list_commits`
- **Purpose**: List commits on a branch
- **Usage**: Track documentation update history

#### `github_compare_commits`
- **Purpose**: Compare two commits
- **Usage**: Get diff, changed files between commits
- **PROVES Use Case**: Incremental doc sync (detect changes)

---

### 3. Issue Management (9 tools)

#### `github_create_issue`
- **Purpose**: Create a new issue
- **Usage**: Auto-create issues for detected risks, missing documentation
- **PROVES Use Case**: Curator agent creates issue when conflict detected

#### `github_get_issue`
- **Purpose**: Get issue details
- **Usage**: Read issue content, status, labels

#### `github_update_issue`
- **Purpose**: Update issue (title, body, labels, assignees)
- **Usage**: Mark issues as resolved, add labels

#### `github_close_issue`
- **Purpose**: Close an issue
- **Usage**: Auto-close when risk is mitigated

#### `github_list_issues`
- **Purpose**: List issues (filter by state, labels, assignee)
- **Usage**: Track open risks, documentation tasks

#### `github_add_issue_comment`
- **Purpose**: Comment on an issue
- **Usage**: Provide updates, link to solutions

#### `github_list_issue_comments`
- **Purpose**: List comments on an issue
- **Usage**: Track discussion history

#### `github_add_labels_to_issue`
- **Purpose**: Add labels to an issue
- **Usage**: Categorize issues (risk:high, doc:missing, etc.)

#### `github_remove_label_from_issue`
- **Purpose**: Remove label from an issue
- **Usage**: Update issue categorization

---

### 4. Pull Request Operations (8 tools)

#### `github_create_pull_request`
- **Purpose**: Create a pull request
- **Usage**: Submit code changes, documentation updates
- **PROVES Use Case**: Builder agent creates PR with generated component

#### `github_get_pull_request`
- **Purpose**: Get PR details
- **Usage**: Check PR status, reviews, checks

#### `github_update_pull_request`
- **Purpose**: Update PR (title, body, base branch)
- **Usage**: Update PR description with additional context

#### `github_merge_pull_request`
- **Purpose**: Merge a pull request
- **Usage**: Auto-merge approved PRs

#### `github_close_pull_request`
- **Purpose**: Close a PR without merging
- **Usage**: Reject invalid PRs

#### `github_list_pull_requests`
- **Purpose**: List pull requests
- **Usage**: Track pending code reviews

#### `github_list_pull_request_files`
- **Purpose**: List files changed in a PR
- **Usage**: Review what changed

#### `github_create_pull_request_review`
- **Purpose**: Review a pull request
- **Usage**: Approve, request changes, or comment

---

### 5. Branch Management (4 tools)

#### `github_create_branch`
- **Purpose**: Create a new branch
- **Usage**: Create feature branches for development
- **PROVES Use Case**: Curator creates branch for batch normalization

#### `github_get_branch`
- **Purpose**: Get branch details
- **Usage**: Check branch protection, latest commit

#### `github_delete_branch`
- **Purpose**: Delete a branch
- **Usage**: Clean up merged feature branches

#### `github_list_branches`
- **Purpose**: List repository branches
- **Usage**: Discover all branches

---

### 6. Workflow & Actions (3 tools)

#### `github_list_workflow_runs`
- **Purpose**: List GitHub Actions workflow runs
- **Usage**: Track CI/CD status, test results

#### `github_get_workflow_run`
- **Purpose**: Get workflow run details
- **Usage**: Check if tests passed, get logs

#### `github_trigger_workflow`
- **Purpose**: Manually trigger a workflow
- **Usage**: Run tests, deploy documentation site
- **PROVES Use Case**: Trigger docs rebuild after sync

---

### 7. Search & Discovery (2 tools)

#### `github_search_repositories`
- **Purpose**: Search for repositories on GitHub
- **Usage**: Find related projects, dependencies

#### `github_search_issues_and_prs`
- **Purpose**: Search issues and PRs
- **Usage**: Find similar bugs, related discussions

---

## PROVES Library Integration Use Cases

### Use Case 1: Automated Documentation Sync

**Tools Used:**
1. `github_get_commit` - Get latest commit SHA
2. `github_compare_commits` - Detect changed files
3. `github_get_file_contents` - Fetch updated markdown files
4. `github_create_or_update_file` - Commit normalized docs

**Workflow:**
```
Daily Sync Job:
├─ Check latest commit SHA on F´ repo
├─ Compare with stored SHA in Neon
├─ If changes detected:
│  ├─ Get list of changed markdown files
│  ├─ Fetch content for each file
│  ├─ Process and normalize with curator agent
│  └─ Update library_entries in Neon
└─ Store new SHA
```

---

### Use Case 2: Risk Detection and Issue Creation

**Tools Used:**
1. `github_search_code` - Find potential risk patterns
2. `github_create_issue` - Create issue for detected risk
3. `github_add_labels_to_issue` - Tag with risk severity
4. `github_add_issue_comment` - Link to mitigation pattern

**Workflow:**
```
Risk Scanner Agent:
├─ Scan repository code for patterns
├─ Detect: Missing I2C bus conflict handling
├─ Create issue: "I2C Bus Conflict Risk in IMU Driver"
├─ Add labels: ["risk:medium", "component:imu"]
└─ Comment: Link to TCA9548A mitigation pattern in library
```

---

### Use Case 3: Builder Agent Component Generation

**Tools Used:**
1. `github_create_branch` - Create feature branch
2. `github_create_or_update_file` - Write generated component files
3. `github_create_pull_request` - Submit for review
4. `github_add_labels_to_issue` - Tag PR with metadata

**Workflow:**
```
Builder Agent:
├─ User requests: "Generate I2C sensor component"
├─ Query library for I2C + sensor patterns
├─ Create branch: feature/i2c-sensor-component
├─ Generate files:
│  ├─ I2CSensorComponent.hpp
│  ├─ I2CSensorComponent.cpp
│  └─ I2CSensorComponentAi.xml
├─ Commit files to branch
├─ Create PR with description
└─ Add labels: ["auto-generated", "component:sensor"]
```

---

### Use Case 4: Incremental Library Updates

**Tools Used:**
1. `github_list_commits` - Get recent commits
2. `github_get_file_contents` - Fetch new documentation
3. `github_create_issue` - Create task for manual review

**Workflow:**
```
Curator Agent:
├─ Detect new F´ doc: "CameraDriver.md"
├─ Fetch content
├─ Parse metadata (tags: camera, image, driver)
├─ Create library entry (quality_score: 0.7 - needs review)
├─ Build knowledge graph nodes:
│  ├─ Node: "Camera Driver Component"
│  └─ Relationship: depends_on "I2C Bus"
└─ Create issue: "Review new Camera Driver documentation"
```

---

## Rate Limits & Best Practices

### GitHub API Rate Limits

| Authentication | Requests/Hour | Notes |
|----------------|---------------|-------|
| **Unauthenticated** | 60 | Not recommended |
| **Authenticated (token)** | 5000 | Use personal access token |
| **GitHub App** | 15000 | For production apps |

### Best Practices

1. **Always authenticate**: Set `GITHUB_TOKEN` in `.env`
2. **Batch operations**: Minimize API calls by batching requests
3. **Use webhooks**: For real-time updates instead of polling
4. **Cache responses**: Store commit SHAs, file content when possible
5. **Check rate limits**: Monitor `X-RateLimit-Remaining` header
6. **Handle errors gracefully**: Retry on 429 (rate limit exceeded)

---

## Example: GitHub Token Setup

### Step 1: Generate Token

1. Go to: [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Name: `PROVES Library MCP Access`
4. Permissions:
   - [YES] `repo` (full repository access)
   - [YES] `workflow` (trigger workflows)
   - [YES] `read:org` (read org data)
5. Generate and copy token

### Step 2: Add to .env

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Verify Access

```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

---

## GitHub MCP Tools vs GitHub CLI vs GitHub API

| Feature | GitHub MCP Tools | GitHub CLI (`gh`) | GitHub REST API |
|---------|------------------|-------------------|-----------------|
| **Use Case** | Agent automation | Manual scripting | Direct HTTP calls |
| **Auth** | Token via MCP config | Token via `gh auth` | Token in headers |
| **Format** | Structured tool calls | Command line | HTTP requests |
| **Best For** | LangGraph agents | Shell scripts | Custom apps |

**When to use MCP tools:**
- Building autonomous agents (like curator, builder)
- LangGraph workflows
- Need structured input/output
- Want type safety and validation

**When to use GitHub CLI:**
- Manual operations
- Shell scripts
- Quick one-off tasks

**When to use GitHub API directly:**
- Custom applications
- Need specific endpoints not in MCP
- Building integrations

---

## Next Steps

1. [YES] **Verify GitHub MCP connection**: Check VS Code MCP status
2. ⏸️ **Test basic operations**: Try `github_get_repository` for PROVES_LIBRARY
3. ⏸️ **Implement doc sync**: Use GitHub tools instead of raw API calls in `github_doc_sync.py`
4. ⏸️ **Build curator workflow**: Use tools for auto-commit of normalized entries
5. ⏸️ **Create risk scanner**: Use `github_search_code` to find patterns

---

## Reference Links

- **GitHub MCP Server**: [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
- **GitHub REST API**: [docs.github.com/rest](https://docs.github.com/en/rest)
- **MCP Specification**: [spec.modelcontextprotocol.io](https://spec.modelcontextprotocol.io)
- **LangGraph Documentation**: [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/)
