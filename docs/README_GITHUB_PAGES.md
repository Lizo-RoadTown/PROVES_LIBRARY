# PROVES Library - GitHub Pages Setup

## Overview

This GitHub Pages site visualizes the comprehensive dependency analysis from the trial mapping of F´ and PROVES Kit documentation. The site demonstrates how the PROVES Library system tracks dependencies, identifies knowledge gaps, and prevents mission failures.

## Site Structure

```
docs/
├── _config.yml              # Jekyll configuration
├── index.md                 # Main landing page
├── diagrams/                # Diagram pages
│   ├── overview.md          # All 45+ dependencies
│   ├── cross-system.md      # Hidden F´ ↔ PROVES Kit dependencies
│   ├── transitive-chains.md # Multi-hop dependency paths
│   ├── knowledge-gaps.md    # Undocumented requirements
│   └── team-boundaries.md   # FRAMES organizational analysis
├── TRIAL_MAPPING_DESIGN.md  # Design document
└── *.md                     # Other documentation
```

## Enable GitHub Pages

### Step 1: Push to GitHub

```bash
cd c:/Users/LizO5/PROVES_LIBRARY
git add docs/
git commit -m "Add GitHub Pages site with dependency diagrams"
git push origin master
```

### Step 2: Enable GitHub Pages

1. Go to: `https://github.com/LizO5/PROVES_LIBRARY/settings/pages`
2. Under "Source", select **Deploy from a branch**
3. Under "Branch", select:
   - Branch: `master`
   - Folder: `/docs`
4. Click **Save**

### Step 3: Access Site

After ~1-2 minutes, site will be available at:
```
https://lizo5.github.io/PROVES_LIBRARY/
```

## Features

### Interactive Mermaid Diagrams

All diagrams use Mermaid.js for interactive visualization:
- Dependency graphs
- Sequence diagrams
- State machines
- Gantt charts
- Quadrant charts
- Pie charts

### Navigation

- Home page with overview and links to all diagrams
- Each diagram page includes navigation to previous/next
- Breadcrumb trail back to home

### Mobile Responsive

Jekyll Cayman theme is mobile-friendly and works on all devices.

## Updating Content

### To Add New Diagrams

1. Create new `.md` file in `docs/diagrams/`
2. Add front matter:
   ```yaml
   ---
   layout: default
   title: Your Page Title
   ---
   ```
3. Add Mermaid diagrams:
   ````markdown
   ```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e3f2fd',
    'primaryTextColor': '#1a1a1a',
    'primaryBorderColor': '#1976d2',
    'secondaryColor': '#fff8e1',
    'secondaryBorderColor': '#f9a825',
    'tertiaryColor': '#f3e5f5',
    'tertiaryBorderColor': '#7b1fa2',
    'lineColor': '#546e7a',
    'textColor': '#1a1a1a',
    'fontFamily': 'system-ui, -apple-system, sans-serif',
    'fontSize': '14px',
    'edgeLabelBackground': '#fff8e1'
  },
  'themeCSS': `
    .edgeLabel foreignObject { overflow: visible; }
    .edgeLabel .label { 
      padding: 5px 5px;
      border: 1px solid #000;
      border-radius: 3px;
      background: #fff8e1;
    }
    .node rect, .node circle, .node ellipse, .node polygon, .node path {
      transition: filter 0.2s ease;
    }
    .node:hover rect, .node:hover circle, .node:hover ellipse, .node:hover polygon, .node:hover path {
      filter: drop-shadow(0 0 10px #1976d2) drop-shadow(0 0 5px #64b5f6);
      cursor: pointer;
    }
    .cluster rect {
      transition: filter 0.2s ease;
    }
    .cluster:hover rect {
      filter: drop-shadow(0 0 8px rgba(25, 118, 210, 0.5));
    }
  `,
  'flowchart': {
    'curve': 'linear',
    'nodeSpacing': 40,
    'rankSpacing': 60,
    'padding': 15,
    'htmlLabels': true,
    'useMaxWidth': false
  }
}}%%
   graph TB
       A[Start] --> B[End]
   ```
   ````
4. Add navigation links to/from other pages
5. Update `docs/_config.yml` navigation section

### To Update Existing Diagrams

1. Edit the corresponding `.md` file
2. Commit and push to GitHub
3. Site automatically rebuilds

## Local Testing

To test locally before pushing:

```bash
# Install Jekyll (one time)
gem install bundler jekyll

# Create Gemfile in docs/
cat > docs/Gemfile <<EOF
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
gem "jekyll-theme-cayman"
EOF

# Install dependencies
cd docs
bundle install

# Serve locally
bundle exec jekyll serve

# Open browser to http://localhost:4000/PROVES_LIBRARY/
```

## Troubleshooting

### Diagrams Not Rendering

If Mermaid diagrams don't render:
1. Check that code blocks use ```mermaid (not ```mmd)
2. Ensure Mermaid script is loaded in layout
3. Check browser console for errors

### 404 Errors

If pages show 404:
1. Verify `baseurl` in `_config.yml` matches repo name
2. Check that file paths are correct
3. Ensure front matter exists in all `.md` files

### Styling Issues

If styling looks wrong:
1. Clear browser cache
2. Check that `theme: jekyll-theme-cayman` is in `_config.yml`
3. Verify layout is set to `default` in front matter

## Site Analytics

To add Google Analytics:

1. Get tracking ID from Google Analytics
2. Add to `_config.yml`:
   ```yaml
   google_analytics: UA-XXXXXXXX-X
   ```

## Custom Domain (Optional)

To use custom domain like `proves-library.org`:

1. Add `CNAME` file to `docs/`:
   ```
   proves-library.org
   ```
2. Configure DNS:
   ```
   A record: @ → 185.199.108.153
   A record: @ → 185.199.109.153
   A record: @ → 185.199.110.153
   A record: @ → 185.199.111.153
   CNAME: www → lizo5.github.io
   ```
3. Wait for DNS propagation (~24 hours)

## License

This documentation is part of the PROVES Library project and follows the same license.

## Contact

For issues or questions about the GitHub Pages site, open an issue at:
https://github.com/LizO5/PROVES_LIBRARY/issues
