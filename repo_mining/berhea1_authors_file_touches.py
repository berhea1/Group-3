import json
import requests
import csv
import os
from datetime import datetime

if not os.path.exists("data"):
    os.makedirs("data")

# Load GitHub tokens from environment variable
# Usage: export GITHUB_TOKENS="token1,token2,token3"
lstTokens = os.getenv('GITHUB_TOKENS', '').split(',')
lstTokens = [token.strip() for token in lstTokens if token.strip()]

if not lstTokens:
    print("Error: GITHUB_TOKENS environment variable not set")
    print("Usage: export GITHUB_TOKENS='token1,token2,token3'")
    print("Then run: python berhea1_authors_file_touches.py")
    exit(1)

print(f"Loaded {len(lstTokens)} GitHub token(s)\n")

# SOURCE FILE EXTENSIONS (same as Task 1)
SOURCE_EXTENSIONS = {'.java', '.kt', '.cpp', '.h', '.c', '.xml', '.gradle', '.kts', '.properties', '.toml'}

# EXCLUDE PATTERNS (same as Task 1)
EXCLUDE_PATTERNS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ttf', '.otf', '.jar', '.aar', '.dex', '.apk', '.class', '.o', '.so', '.a'}

# EXCLUDE DIRECTORIES (same as Task 1)
EXCLUDE_DIRS = {'.git', '.circleci', '.github', 'gradle/wrapper', 'art', 'build', '.idea', '.gradle', '__pycache__', 'mipmap', 'drawable'}

def should_include_file(filepath):
    """Determine if a file should be included as a source file."""
    path_parts = filepath.split('/')
    for excluded_dir in EXCLUDE_DIRS:
        if excluded_dir in path_parts:
            return False
    
    filename = filepath.split('/')[-1]
    _, ext = os.path.splitext(filename)
    
    if ext in EXCLUDE_PATTERNS:
        return False
    
    if ext in SOURCE_EXTENSIONS:
        return True
    
    if filename in ['CMakeLists.txt']:
        return True
    
    return False

# GitHub Authentication function
def github_auth(url, lsttoken, ct):
    jsonData = None
    try:
        ct = ct % len(lsttoken)
        headers = {'Authorization': 'Bearer {}'.format(lsttoken[ct])}
        request = requests.get(url, headers=headers)
        jsonData = json.loads(request.content)
        ct += 1
    except Exception as e:
        print(e)
    return jsonData, ct

# Get the default branch of the repository
def get_default_branch(lsttokens, repo):
    ct = 0
    url = 'https://api.github.com/repos/' + repo
    jsonData, ct = github_auth(url, lsttokens, ct)
    if jsonData and 'default_branch' in jsonData:
        return jsonData['default_branch']
    return 'master'

# Collect author and file-touch data
def collect_author_file_touches(lsttokens, repo):
    """
    For each source file, collect:
    - File path
    - Authors who changed the file
    - Dates of the changes
    - Number of times the file was changed
    """
    ipage = 1
    ct = 0
    default_branch = get_default_branch(lsttokens, repo)
    print(f"Using default branch: {default_branch}\n")
    
    # Dictionary to store: filename -> [(author, date, commit_sha), ...]
    file_touch_data = {}
    
    try:
        while True:
            spage = str(ipage)
            commitsUrl = 'https://api.github.com/repos/' + repo + '/commits?page=' + spage + '&per_page=100&sha=' + default_branch
            jsonCommits, ct = github_auth(commitsUrl, lsttokens, ct)
            
            if len(jsonCommits) == 0:
                break
            
            for shaObject in jsonCommits:
                sha = shaObject['sha']
                commit_author = shaObject['commit']['author']['name'] if 'commit' in shaObject and 'author' in shaObject['commit'] else 'Unknown'
                commit_date = shaObject['commit']['author']['date'] if 'commit' in shaObject and 'author' in shaObject['commit'] else None
                
                shaUrl = 'https://api.github.com/repos/' + repo + '/commits/' + sha
                shaDetails, ct = github_auth(shaUrl, lsttokens, ct)
                
                # Skip merge commits
                if shaDetails and 'parents' in shaDetails and len(shaDetails['parents']) > 1:
                    continue
                
                if shaDetails and 'files' in shaDetails:
                    filesjson = shaDetails['files']
                    for filenameObj in filesjson:
                        filename = filenameObj['filename']
                        
                        if should_include_file(filename):
                            if filename not in file_touch_data:
                                file_touch_data[filename] = []
                            
                            file_touch_data[filename].append({
                                'author': commit_author,
                                'date': commit_date,
                                'sha': sha
                            })
                            
                            print(f"{filename} - touched by {commit_author} on {commit_date}")
            
            ipage += 1
    
    except Exception as e:
        print("Error receiving data: " + str(e))
        exit(0)
    
    return file_touch_data

# GitHub repo
repo = 'scottyab/rootbeer'

# Collect data
file_touch_data = collect_author_file_touches(lstTokens, repo)

print(f"\nTotal source files touched: {len(file_touch_data)}\n")

# Write to CSV
file = repo.split('/')[1]
fileOutput = 'data/file_' + file + '_authors_touches.csv'
rows = ["Filename", "Author", "Date", "Total_Touches"]

fileCSV = open(fileOutput, 'w', newline='')
writer = csv.writer(fileCSV)
writer.writerow(rows)

for filename, touches in file_touch_data.items():
    total_touches = len(touches)
    
    # Group by author
    authors = {}
    for touch in touches:
        author = touch['author']
        if author not in authors:
            authors[author] = []
        authors[author].append(touch['date'])
    
    # Write one row per file (with all authors and dates)
    authors_str = '; '.join([f"{author}({len(dates)})" for author, dates in authors.items()])
    dates_str = '; '.join([touch['date'] for touch in touches])
    
    rows = [filename, authors_str, dates_str, total_touches]
    writer.writerow(rows)

fileCSV.close()
print(f"Data written to {fileOutput}")
print(f"Total number of source files: {len(file_touch_data)}")

# Print summary
for filename, touches in sorted(file_touch_data.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    authors_set = set(touch['author'] for touch in touches)
    print(f"{filename}: {len(touches)} touches by {len(authors_set)} author(s)")