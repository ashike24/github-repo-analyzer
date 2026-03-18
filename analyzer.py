import requests
import json
from datetime import datetime, timezone
from typing import Optional
import time

class GitHubAnalyzer:
    def __init__(self, token: Optional[str] = None):
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.base_url = "https://api.github.com"

    def _get(self, url, params=None):
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 404:
                return None
            if response.status_code == 403:
                print("Rate limit hit. Waiting 60 seconds...")
                time.sleep(60)
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_repo_url(self, url):
        url = url.strip().rstrip("/")
        parts = url.replace("https://github.com/", "").split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
        return None, None

    def get_repo_info(self, owner, repo):
        return self._get(f"{self.base_url}/repos/{owner}/{repo}")

    def get_commit_count(self, owner, repo):
        # Use contributors stats to estimate commit count
        data = self._get(f"{self.base_url}/repos/{owner}/{repo}/contributors", params={"per_page": 1, "anon": "true"})
        if data is None:
            return 0
        # Get total via commits endpoint with per_page=1
        resp = requests.get(
            f"{self.base_url}/repos/{owner}/{repo}/commits",
            headers=self.headers,
            params={"per_page": 1},
            timeout=10
        )
        if resp.status_code != 200:
            return 0
        link = resp.headers.get("Link", "")
        if 'rel="last"' in link:
            import re
            match = re.search(r'page=(\d+)>; rel="last"', link)
            if match:
                return int(match.group(1))
        return len(resp.json()) if resp.json() else 0

    def get_languages(self, owner, repo):
        data = self._get(f"{self.base_url}/repos/{owner}/{repo}/languages")
        return data if data else {}

    def get_contributor_count(self, owner, repo):
        resp = requests.get(
            f"{self.base_url}/repos/{owner}/{repo}/contributors",
            headers=self.headers,
            params={"per_page": 1, "anon": "true"},
            timeout=10
        )
        if resp.status_code != 200:
            return 0
        link = resp.headers.get("Link", "")
        if 'rel="last"' in link:
            import re
            match = re.search(r'page=(\d+)>; rel="last"', link)
            if match:
                return int(match.group(1))
        try:
            return len(resp.json())
        except:
            return 0

    def get_dependency_files(self, owner, repo):
        dep_files = [
            "requirements.txt", "package.json", "pom.xml",
            "Gemfile", "go.mod", "Cargo.toml", "build.gradle"
        ]
        found = 0
        tree = self._get(f"{self.base_url}/repos/{owner}/{repo}/git/trees/HEAD", params={"recursive": "false"})
        if tree and "tree" in tree:
            names = [item["path"] for item in tree["tree"]]
            for dep in dep_files:
                if dep in names:
                    found += 1
        return found

    def calculate_activity_score(self, stars, forks, open_issues, commit_count, contributor_count, days_since_update):
        """
        Activity Score Formula (out of 100):
        - Stars:        20% weight (log-scaled)
        - Forks:        15% weight (log-scaled)
        - Commits:      25% weight (log-scaled)
        - Contributors: 20% weight (log-scaled)
        - Recency:      20% weight (inverse of days since update)
        """
        import math

        star_score    = min(20, math.log1p(stars) / math.log1p(10000) * 20)
        fork_score    = min(15, math.log1p(forks) / math.log1p(5000) * 15)
        commit_score  = min(25, math.log1p(commit_count) / math.log1p(5000) * 25)
        contrib_score = min(20, math.log1p(contributor_count) / math.log1p(500) * 20)

        if days_since_update <= 7:
            recency_score = 20
        elif days_since_update <= 30:
            recency_score = 15
        elif days_since_update <= 90:
            recency_score = 10
        elif days_since_update <= 365:
            recency_score = 5
        else:
            recency_score = 0

        total = star_score + fork_score + commit_score + contrib_score + recency_score
        return round(total, 2)

    def calculate_complexity(self, language_count, file_count, dep_files, commit_count):
        """
        Complexity Score (out of 100):
        - Language diversity: 25%
        - File count:         35%
        - Dependency files:   20%
        - Commit history:     20%
        """
        import math

        lang_score   = min(25, language_count / 10 * 25)
        file_score   = min(35, math.log1p(file_count) / math.log1p(10000) * 35)
        dep_score    = min(20, dep_files / 5 * 20)
        commit_score = min(20, math.log1p(commit_count) / math.log1p(5000) * 20)

        total = lang_score + file_score + dep_score + commit_score
        return round(total, 2)

    def classify_difficulty(self, activity_score, complexity_score):
        combined = (activity_score + complexity_score) / 2
        if combined < 30:
            return "Beginner"
        elif combined < 60:
            return "Intermediate"
        else:
            return "Advanced"

    def get_file_count(self, owner, repo):
        tree = self._get(f"{self.base_url}/repos/{owner}/{repo}/git/trees/HEAD", params={"recursive": "true"})
        if tree and "tree" in tree:
            return len([i for i in tree["tree"] if i["type"] == "blob"])
        return 0

    def analyze(self, repo_url):
        owner, repo = self.parse_repo_url(repo_url)
        if not owner or not repo:
            return {"error": f"Invalid URL: {repo_url}"}

        print(f"  Fetching repo info...")
        info = self.get_repo_info(owner, repo)
        if not info:
            return {"error": f"Could not fetch repo: {repo_url}"}

        print(f"  Fetching commits...")
        commit_count = self.get_commit_count(owner, repo)
        print(f"  Fetching contributors...")
        contributor_count = self.get_contributor_count(owner, repo)
        print(f"  Fetching languages...")
        languages = self.get_languages(owner, repo)
        print(f"  Fetching dependency files...")
        dep_files = self.get_dependency_files(owner, repo)
        print(f"  Fetching file count...")
        file_count = self.get_file_count(owner, repo)

        # Days since last update
        updated_at = info.get("updated_at", "")
        if updated_at:
            updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            days_since_update = (datetime.now(timezone.utc) - updated_dt).days
        else:
            days_since_update = 999

        stars = info.get("stargazers_count", 0)
        forks = info.get("forks_count", 0)
        open_issues = info.get("open_issues_count", 0)
        description = info.get("description", "No description") or "No description"
        license_info = info.get("license")
        license_name = license_info.get("name", "None") if license_info else "None"
        default_branch = info.get("default_branch", "main")
        is_archived = info.get("archived", False)
        topics = info.get("topics", [])

        activity_score = self.calculate_activity_score(
            stars, forks, open_issues, commit_count, contributor_count, days_since_update
        )
        complexity_score = self.calculate_complexity(
            len(languages), file_count, dep_files, commit_count
        )
        difficulty = self.classify_difficulty(activity_score, complexity_score)

        return {
            "repo": f"{owner}/{repo}",
            "url": repo_url,
            "description": description,
            "stars": stars,
            "forks": forks,
            "open_issues": open_issues,
            "commit_count": commit_count,
            "contributor_count": contributor_count,
            "languages": list(languages.keys()),
            "language_count": len(languages),
            "file_count": file_count,
            "dependency_files": dep_files,
            "days_since_update": days_since_update,
            "license": license_name,
            "default_branch": default_branch,
            "is_archived": is_archived,
            "topics": topics,
            "activity_score": activity_score,
            "complexity_score": complexity_score,
            "difficulty": difficulty,
        }
