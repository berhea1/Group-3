import json
import requests
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

if not os.path.exists("data"):
    os.makedirs("data")

# Load GitHub tokens from environment variable
lstTokens = os.getenv('GITHUB_TOKENS', '').split(',')
lstTokens = [token.strip() for token in lstTokens if token.strip()]

if not lstTokens:
    print("Error: GITHUB_TOKENS environment variable not set")
    print("Usage: export GITHUB_TOKENS='token1,token2,token3'")
    print("Then run: python berhea1_scatterplot.py")
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

# Get the default branch and first commit date
def get_default_branch(lsttokens, repo):
    ct = 0
    url = 'https://api.github.com/repos/' + repo
    jsonData, ct = github_auth(url, lsttokens, ct)
    if jsonData and 'default_branch' in jsonData:
        return jsonData['default_branch']
    return 'master'

def get_first_commit_date(lsttokens, repo, default_branch):
    """Get the date of the first commit in the repository"""
    ct = 0
    url = 'https://api.github.com/repos/' + repo + '/commits?sha=' + default_branch + '&per_page=1&page=999999'
    jsonCommits, ct = github_auth(url, lsttokens, ct)
    
    if jsonCommits and len(jsonCommits) > 0:
        first_commit_date = jsonCommits[0]['commit']['author']['date']
        return datetime.strptime(first_commit_date, "%Y-%m-%dT%H:%M:%SZ")
    
    return datetime.now()

# Collect data for visualization
def collect_visualization_data(lsttokens, repo):
    """Collect data for scatter plot visualization"""
    ipage = 1
    ct = 0
    default_branch = get_default_branch(lsttokens, repo)
    print(f"Using default branch: {default_branch}\n")
    
    # Get the first commit date to calculate weeks
    first_commit_date = get_first_commit_date(lsttokens, repo, default_branch)
    print(f"Repository started on: {first_commit_date}\n")
    
    # List to collect scatter plot data
    scatter_points = []
    
    # Dictionary to map filenames to Y positions
    file_positions = {}
    current_y_position = 0
    
    # List to track all authors for color mapping
    all_authors = set()
    
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
                commit_date_str = shaObject['commit']['author']['date'] if 'commit' in shaObject and 'author' in shaObject['commit'] else None
                
                if not commit_date_str:
                    continue
                
                commit_date = datetime.strptime(commit_date_str, "%Y-%m-%dT%H:%M:%SZ")
                
                # Calculate weeks since first commit
                time_diff = commit_date - first_commit_date
                weeks_since_start = time_diff.days / 7.0
                
                all_authors.add(commit_author)
                
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
                            # Assign Y position to file if not already assigned
                            if filename not in file_positions:
                                file_positions[filename] = current_y_position
                                current_y_position += 1
                            
                            scatter_points.append({
                                'author': commit_author,
                                'filename': filename,
                                'week': weeks_since_start
                            })
                            
                            print(f"Week {int(weeks_since_start)}: {filename} - {commit_author}")
            
            ipage += 1
    
    except Exception as e:
        print("Error receiving data: " + str(e))
        exit(0)
    
    return scatter_points, file_positions, all_authors, first_commit_date

# GitHub repo
repo = 'scottyab/rootbeer'

# Collect visualization data
print("Collecting visualization data...\n")
scatter_points, file_positions, all_authors, first_commit_date = collect_visualization_data(lstTokens, repo)

print(f"\nTotal unique files: {len(file_positions)}")
print(f"Total unique authors: {len(all_authors)}")
print(f"Total data points: {len(scatter_points)}\n")

# Prepare data for plotting
x_coords = []
y_coords = []
colors = []
author_list = sorted(list(all_authors))
author_to_color = {author: i for i, author in enumerate(author_list)}

for point in scatter_points:
    x_coords.append(point['week'])
    y_coords.append(file_positions[point['filename']])
    colors.append(author_to_color[point['author']])

# Create scatter plot
plt.figure(figsize=(16, 10))
scatter = plt.scatter(x_coords, y_coords, c=colors, cmap='tab20', s=100, alpha=0.6, edgecolors='black', linewidth=0.5)

plt.xlabel('Weeks since repository began', fontsize=12)
plt.ylabel('Source files', fontsize=12)
plt.title('scottyab/rootbeer Repository Activity Over Time', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)

# Create legend for authors
cbar = plt.colorbar(scatter, pad=0.01)
cbar.set_label('Authors', fontsize=12)
tick_positions = np.linspace(0, len(author_list) - 1, min(len(author_list), 20))
cbar.set_ticks(tick_positions)
cbar.set_ticklabels([author_list[int(i)] for i in tick_positions], fontsize=8)

plt.tight_layout()

# Save figure
file = repo.split('/')[1]
output_file = 'data/berhea1_file_activity.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Visualization saved to {output_file}")

plt.show()