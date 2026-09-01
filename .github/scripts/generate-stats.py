import os
import requests
import json
from datetime import datetime, timedelta

USERNAME = os.environ.get("USERNAME", "patrickviniciusfs")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

def fetch_user_data():
    url = f"https://api.github.com/users/{USERNAME}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def fetch_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}"
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_commits():
    url = f"https://api.github.com/search/commits?q=author:{USERNAME}&sort=author-date&order=desc&per_page=1"
    resp = requests.get(url, headers={**HEADERS, "Accept": "application/vnd.github.cloak-preview+json"})
    resp.raise_for_status()
    return resp.json().get("total_count", 0)

def generate_stats_card(user, repos):
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    contributions = fetch_commits()

    svg = f'''<svg width="495" height="195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#58a6ff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#bc8cff;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="495" height="195" rx="10" fill="#0d1117"/>
  <rect x="2" y="2" width="491" height="191" rx="8" fill="none" stroke="url(#grad)" stroke-width="2"/>
  
  <text x="30" y="45" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="bold" fill="#58a6ff">GitHub Stats</text>
  <text x="30" y="70" font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="#8b949e">@{USERNAME}</text>
  
  <line x1="30" y1="85" x2="465" y2="85" stroke="#21262d" stroke-width="1"/>
  
  <text x="30" y="115" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Total Stars:</text>
  <text x="465" y="115" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="bold" fill="#e3b341" text-anchor="end">{total_stars}</text>
  
  <text x="30" y="140" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Total Forks:</text>
  <text x="465" y="140" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="bold" fill="#58a6ff" text-anchor="end">{total_forks}</text>
  
  <text x="30" y="165" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Contributions:</text>
  <text x="465" y="165" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="bold" fill="#3fb950" text-anchor="end">{contributions}</text>
</svg>'''
    return svg

def generate_top_langs_card(repos):
    lang_bytes = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/languages"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            for lang, bytes_count in resp.json().items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + bytes_count

    total = sum(lang_bytes.values()) or 1
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:5]

    colors = {
        "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Java": "#b07219",
        "Python": "#3572A5", "HTML": "#e34c26", "CSS": "#563d7c",
        "Shell": "#89e051", "SQL": "#e38c00", "Vue": "#41b883",
        "Svelte": "#ff3e00", "Go": "#00ADD8", "Rust": "#dea584",
        "C++": "#f34b7d", "C": "#555555", "Ruby": "#701516",
    }

    bars = ""
    y = 65
    for i, (lang, count) in enumerate(sorted_langs):
        pct = (count / total) * 100
        color = colors.get(lang, "#8b949e")
        bar_width = pct * 2.5
        bars += f'''
    <text x="30" y="{y}" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#e6edf3">{lang}</text>
    <text x="465" y="{y}" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#8b949e" text-anchor="end">{pct:.1f}%</text>
    <rect x="30" y="{y + 5}" width="{bar_width}" height="8" rx="4" fill="{color}"/>'''
        y += 35

    svg = f'''<svg width="495" height="{y + 20}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#58a6ff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#bc8cff;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="495" height="{y + 20}" rx="10" fill="#0d1117"/>
  <rect x="2" y="2" width="491" height="{y + 16}" rx="8" fill="none" stroke="url(#grad)" stroke-width="2"/>
  
  <text x="30" y="45" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="bold" fill="#58a6ff">Top Languages</text>
  {bars}
</svg>'''
    return svg

def generate_streak_card(user):
    svg = f'''<svg width="495" height="195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#58a6ff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#bc8cff;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="495" height="195" rx="10" fill="#0d1117"/>
  <rect x="2" y="2" width="491" height="191" rx="8" fill="none" stroke="url(#grad)" stroke-width="2"/>
  
  <text x="30" y="45" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="bold" fill="#58a6ff">Profile Summary</text>
  
  <line x1="30" y1="60" x2="465" y2="60" stroke="#21262d" stroke-width="1"/>
  
  <text x="30" y="90" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Public Repos:</text>
  <text x="465" y="90" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="bold" fill="#e6edf3" text-anchor="end">{user.get("public_repos", 0)}</text>
  
  <text x="30" y="115" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Followers:</text>
  <text x="465" y="115" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="bold" fill="#e6edf3" text-anchor="end">{user.get("followers", 0)}</text>
  
  <text x="30" y="140" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Following:</text>
  <text x="465" y="140" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="bold" fill="#e6edf3" text-anchor="end">{user.get("following", 0)}</text>
  
  <text x="30" y="165" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Joined:</text>
  <text x="465" y="165" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="bold" fill="#e6edf3" text-anchor="end">{datetime.strptime(user.get("created_at", ""), "%Y-%m-%dT%H:%M:%SZ").strftime("%b %Y")}</text>
</svg>'''
    return svg

def main():
    print(f"Generating stats for {USERNAME}...")
    
    user = fetch_user_data()
    repos = fetch_repos()
    
    os.makedirs("stats", exist_ok=True)
    
    with open("stats/github-stats.svg", "w", encoding="utf-8") as f:
        f.write(generate_stats_card(user, repos))
    print("Generated github-stats.svg")
    
    with open("stats/top-langs.svg", "w", encoding="utf-8") as f:
        f.write(generate_top_langs_card(repos))
    print("Generated top-langs.svg")
    
    with open("stats/github-streak.svg", "w", encoding="utf-8") as f:
        f.write(generate_streak_card(user))
    print("Generated github-streak.svg")
    
    print("Done!")

if __name__ == "__main__":
    main()
