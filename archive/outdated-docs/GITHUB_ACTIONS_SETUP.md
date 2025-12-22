# GitHub Actions Deployment for PROVES Library Pages

## Why GitHub Actions?

Using GitHub Actions instead of branch deployment provides:

✅ **Automated Validation** - Jekyll build tested before deployment
✅ **CI/CD Integration** - Professional workflow pattern
✅ **Error Detection** - Catches build errors before going live
✅ **Dependency Management** - Bundler ensures correct gem versions
✅ **Flexible** - Easy to add tests, link checking, diagram validation
✅ **Transparent** - See exactly what's deployed in Actions tab
✅ **Reproducible** - Same build environment every time

---

## Quick Setup (3 Steps)

### Step 1: Enable GitHub Actions in Pages Settings

1. Go to: **https://github.com/Lizo-RoadTown/PROVES_LIBRARY/settings/pages**
2. Under **"Build and deployment"**:
   - **Source:** Select **GitHub Actions**
3. That's it! No need to select branch or folder.

### Step 2: Verify Workflow is Committed

The workflow file is already created at:
```
.github/workflows/deploy-pages.yml
```

Just push it to GitHub:
```bash
cd c:/Users/LizO5/PROVES_LIBRARY
git add .github/ docs/Gemfile
git commit -m "Add GitHub Actions workflow for Pages deployment"
git push origin master
```

### Step 3: Watch it Deploy

1. Go to: **https://github.com/Lizo-RoadTown/PROVES_LIBRARY/actions**
2. You'll see "Deploy GitHub Pages" workflow running
3. Click on the running workflow to watch progress:
   - **Build job**: Installs Ruby, Jekyll dependencies, builds site
   - **Deploy job**: Uploads and deploys to GitHub Pages
4. When both jobs show ✅ green checkmark, site is live!

---

## Accessing Your Site

Once deployed, site will be available at:
```
https://lizo-roadtown.github.io/PROVES_LIBRARY/
```

The workflow runs automatically on every push to `master` that modifies files in `docs/`.

---

## Workflow Details

### What the Workflow Does

```yaml
# Trigger: On push to master that changes docs/ or workflow file
on:
  push:
    branches: ["master"]
    paths:
      - 'docs/**'
      - '.github/workflows/deploy-pages.yml'
  workflow_dispatch:  # Also allow manual trigger
```

### Build Process

1. **Checkout code** - Gets latest from master
2. **Setup Ruby 3.1** - Installs Ruby with bundler
3. **Install dependencies** - Runs `bundle install` with Gemfile
4. **Build Jekyll site** - Runs `jekyll build` with proper baseurl
5. **Upload artifact** - Packages built site for deployment
6. **Deploy** - Pushes to GitHub Pages

### Validation (Future Enhancements)

The workflow includes placeholder steps for:
- HTML validation (using html-proofer)
- Link checking (to catch broken links)
- Mermaid diagram validation

These can be enabled by replacing the `continue-on-error: true` steps.

---

## Monitoring Deployments

### View Workflow Runs

- All runs: https://github.com/Lizo-RoadTown/PROVES_LIBRARY/actions
- Filter by workflow: Click "Deploy GitHub Pages" in left sidebar
- Status badges available for README if desired

### Debugging Failed Builds

If a deployment fails:

1. Click on the failed workflow run
2. Click on the failed job ("build" or "deploy")
3. Expand the failing step to see error logs
4. Common issues:
   - **Jekyll build errors**: Syntax in markdown files
   - **Missing dependencies**: Gemfile issues
   - **Permission errors**: Check workflow permissions in Settings

### Manual Trigger

You can manually trigger deployment:

1. Go to Actions tab
2. Click "Deploy GitHub Pages" workflow
3. Click "Run workflow" button
4. Select branch and click "Run workflow"

---

## File Structure

```
PROVES_LIBRARY/
├── .github/
│   └── workflows/
│       └── deploy-pages.yml    # Deployment workflow
├── docs/
│   ├── Gemfile                 # Ruby dependencies
│   ├── _config.yml             # Jekyll config
│   ├── index.md                # Home page
│   └── diagrams/               # Diagram pages
└── ...
```

---

## Local Testing

To test the Jekyll build locally before pushing:

```bash
cd docs
bundle install
bundle exec jekyll serve

# Open: http://localhost:4000/PROVES_LIBRARY/
```

This builds the site exactly as GitHub Actions will.

---

## Updating the Site

### To Update Content

1. Edit markdown files in `docs/` or `docs/diagrams/`
2. Commit and push to master
3. Workflow automatically triggers
4. Site updates in ~2-3 minutes

### To Update Workflow

1. Edit `.github/workflows/deploy-pages.yml`
2. Commit and push
3. New workflow takes effect immediately

### To Add New Pages

1. Create new `.md` file in appropriate directory
2. Add front matter with `layout: default`
3. Update navigation in other pages if needed
4. Commit and push

---

## Comparison: Actions vs Branch Deployment

| Feature | GitHub Actions | Branch Deployment |
|---------|---------------|-------------------|
| **Validation** | ✅ Build tested first | ❌ Deploys as-is |
| **Error Detection** | ✅ Shows build errors | ❌ Silent failures |
| **CI/CD** | ✅ Full workflow | ❌ Just file copy |
| **Testing** | ✅ Can add tests | ❌ No testing |
| **Transparency** | ✅ See all steps | ❌ Black box |
| **Flexibility** | ✅ Customizable | ❌ Fixed |
| **Setup** | Medium (workflow file) | Easy (UI only) |

**Recommendation:** GitHub Actions for professional projects, branch deployment for quick prototypes.

---

## Troubleshooting

### "Workflow not found"

- Make sure `.github/workflows/deploy-pages.yml` is pushed to master
- Refresh the Actions tab

### "Permission denied"

- Go to Settings → Actions → General
- Under "Workflow permissions", select "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"

### "Jekyll build failed"

- Check for syntax errors in markdown files
- Verify Mermaid diagram syntax
- Test locally with `bundle exec jekyll build`

### "Site not updating"

- Check workflow ran successfully (green checkmark)
- Hard refresh browser (Ctrl+Shift+R)
- Check that baseurl in _config.yml is correct

---

## Next Steps

After site is live, you can:

1. **Add validation**: Enable HTML and link checking in workflow
2. **Add tests**: Test Mermaid diagrams render correctly
3. **Add badges**: Show build status in README
4. **Monitor traffic**: Enable GitHub Pages analytics
5. **Custom domain**: Point your domain to GitHub Pages

---

## Contact

For workflow issues, open an issue at:
https://github.com/Lizo-RoadTown/PROVES_LIBRARY/issues
