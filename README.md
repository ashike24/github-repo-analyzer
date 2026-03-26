# GitHub Repository Intelligence Analyzer

## 🔗 Live Demo
[**Try it on Streamlit Cloud →**](https://ashike24.streamlit.app/)

---

A tool that analyzes multiple GitHub repositories and generates insights about their activity, complexity, and learning difficulty.

## Features
- Accepts multiple GitHub repository URLs as input
- Collects stars, forks, commits, contributors, languages, file count, dependency files
- Calculates a custom Activity Score (0-100)
- Calculates a custom Complexity Score (0-100)
- Classifies repositories as Beginner, Intermediate, or Advanced
- Generates downloadable JSON and CSV reports
- Clean Streamlit web interface

## Scoring Formulas

### Activity Score (0-100)
| Factor | Weight | Logic |
|--------|--------|-------|
| Stars | 20% | Log-scaled up to 10,000 stars |
| Forks | 15% | Log-scaled up to 5,000 forks |
| Commits | 25% | Log-scaled up to 5,000 commits |
| Contributors | 20% | Log-scaled up to 500 contributors |
| Recency | 20% | Full score if updated within 7 days, zero if over 1 year |

### Complexity Score (0-100)
| Factor | Weight | Logic |
|--------|--------|-------|
| Language diversity | 25% | Number of programming languages used |
| File count | 35% | Log-scaled total number of files |
| Dependency files | 20% | Count of requirements.txt, package.json etc |
| Commit history | 20% | Log-scaled total commits |

### Difficulty Classification
- **Beginner**: Combined score < 30
- **Intermediate**: Combined score 30-60
- **Advanced**: Combined score > 60

## Setup and Running
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usage
1. (Optional) Enter a GitHub Personal Access Token in the sidebar to increase API rate limits from 60 to 5000 requests/hour
2. Paste one GitHub repository URL per line
3. Click Analyze Repositories
4. View the summary table and detailed reports
5. Download results as JSON or CSV

## Rate Limit Handling
- Without a token: 60 requests/hour (enough for 2-3 repos)
- With a token: 5000 requests/hour (enough for 100+ repos)
- If rate limit is hit, the tool waits 60 seconds and retries automatically

## Edge Case Handling
- Missing data fields default to zero without crashing
- Private or deleted repositories return a clear error message
- Archived repositories are flagged in the report
- Repositories with no commits or contributors still produce valid scores

## Assumptions and Limitations
- Commit count is estimated via pagination headers for efficiency
- File count uses the HEAD tree and may miss files in submodules
- Activity score does not account for issue or PR activity (GitHub API rate limits)
- Log scaling is used throughout to handle the wide range of repo sizes fairly
