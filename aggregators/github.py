import httpx
from datetime import datetime, timedelta
from typing import List, Dict
from config import settings
import asyncio


class GitHubAggregator:
    def __init__(self):
        self.token = settings.github_token
        self.username = settings.github_username
        self.repos = settings.github_repos.split(",") if settings.github_repos else []
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def fetch_commits(self, repo: str, since: datetime = None) -> List[Dict]:
        """Fetch commits from a repository"""
        if not self.token or not self.username:
            return []
        
        owner, repo_name = repo.split("/") if "/" in repo else (self.username, repo)
        
        url = f"{self.base_url}/repos/{owner}/{repo_name}/commits"
        params = {
            "author": self.username,
            "per_page": 100
        }
        
        if since:
            params["since"] = since.isoformat()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                commits = response.json()
                
                return [
                    {
                        "sha": commit["sha"],
                        "message": commit["commit"]["message"],
                        "date": commit["commit"]["author"]["date"],
                        "repo": repo
                    }
                    for commit in commits
                ]
            except Exception as e:
                print(f"Error fetching commits from {repo}: {str(e)}")
                return []
    
    async def fetch_prs(self, repo: str, since: datetime = None) -> List[Dict]:
        """Fetch pull requests from a repository"""
        if not self.token or not self.username:
            return []
        
        owner, repo_name = repo.split("/") if "/" in repo else (self.username, repo)
        
        url = f"{self.base_url}/repos/{owner}/{repo_name}/pulls"
        params = {
            "state": "all",
            "per_page": 100
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                prs = response.json()
                
                # Filter by author and date
                filtered_prs = []
                for pr in prs:
                    if pr["user"]["login"].lower() == self.username.lower():
                        pr_date = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                        if not since or pr_date >= since:
                            filtered_prs.append({
                                "number": pr["number"],
                                "title": pr["title"],
                                "state": pr["state"],
                                "created_at": pr["created_at"],
                                "repo": repo
                            })
                
                return filtered_prs
            except Exception as e:
                print(f"Error fetching PRs from {repo}: {str(e)}")
                return []
    
    async def sync_to_loglify(self, entries: List[Dict], entry_type: str):
        """Send entries to Loglify API"""
        async with httpx.AsyncClient() as client:
            for entry in entries:
                if entry_type == "commit":
                    log_entry = {
                        "source": "github",
                        "raw_text": entry["message"],
                        "action": "GitHub Commit",
                        "project": entry["repo"],
                        "tags": ["coding", "github", "commit"],
                        "metadata": {
                            "sha": entry["sha"],
                            "repo": entry["repo"]
                        }
                    }
                elif entry_type == "pr":
                    log_entry = {
                        "source": "github",
                        "raw_text": entry["title"],
                        "action": f"GitHub PR ({entry['state']})",
                        "project": entry["repo"],
                        "tags": ["coding", "github", "pr"],
                        "metadata": {
                            "number": entry["number"],
                            "repo": entry["repo"]
                        }
                    }
                else:
                    continue
                
                try:
                    response = await client.post(
                        f"http://localhost:{settings.port}/api/logs",
                        json=log_entry,
                        timeout=10.0
                    )
                    if response.status_code != 200:
                        print(f"Error logging entry: {response.text}")
                except Exception as e:
                    print(f"Error sending to Loglify: {str(e)}")
    
    async def sync(self, days: int = 1):
        """Sync GitHub data from the last N days"""
        if not self.token or not self.username:
            print("GitHub token or username not configured")
            return
        
        since = datetime.utcnow() - timedelta(days=days)
        
        all_commits = []
        all_prs = []
        
        repos_to_sync = self.repos if self.repos else [self.username]
        
        for repo in repos_to_sync:
            commits = await self.fetch_commits(repo, since)
            all_commits.extend(commits)
            
            prs = await self.fetch_prs(repo, since)
            all_prs.extend(prs)
        
        print(f"Found {len(all_commits)} commits and {len(all_prs)} PRs")
        
        await self.sync_to_loglify(all_commits, "commit")
        await self.sync_to_loglify(all_prs, "pr")
        
        print("✅ GitHub sync completed")


async def main():
    aggregator = GitHubAggregator()
    await aggregator.sync(days=7)


if __name__ == "__main__":
    asyncio.run(main())

