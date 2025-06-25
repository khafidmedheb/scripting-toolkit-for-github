# Git Auto Init

This script initializes a local Git repo and pushes it to GitHub using the GitHub API.

## Usage

1. Export your GitHub token:

```bash
export GITHUB_TOKEN=ghp_yourTokenHere
```

2. Edit the `deploy.sh` script to customize:
- GitHub username
- Repo name
- Visibility

3. Run it:

```bash
bash deploy.sh
```

