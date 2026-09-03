import json
import requests
import csv
import os

if not os.path.exists("data"):
 os.makedirs("data")

#Load GitHub tokens from environment variable
# Usage: export GITHUB_TOKENS="token1,token2,token3"
lstTokens = os.getenv('GITHUB_TOKENS', '').split(',')
lstTokens = [token.strip() for token in lstTokens if token.strip()]

if not lstTokens:
    print("Error: GITHUB_TOKENS envrionment variable not set")
    print("Usage: export GITHUB_TOKENS='token1,token2,token3'")
    print("Then run: python berhea1_collect_files.py")
    exit(1)

print(f"Loaded {len(lstTokens)} GitHub token(s)\n")

# Source File Extensions (Allowed)
SOURCE_EXTENSIONS = {'.java', '.kt', '.cpp', '.h', '.c', '.xml', '.gradle', '.kts', '.properties', '.toml'}

# Non Source Files to Exclude
EXCLUDE_PATTERNS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ttf', '.otf', '.jar', '.aar', '.dex', '.apk', '.class', '.o', '.so', '.a'}

# Directories to skip
EXCLUDE_DIRS = {'.git', '.circleci', '.github', 'gradle/wrapper', 'art', 'build', '.idea', '.gradle', '__pycache__', 'mipmap', 'drawable'}

def should_include_file(filepath):
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
        ct = ct % len(lstTokens)
        headers = {'Authorization': 'Bearer {}'.format(lsttoken[ct])}
        request = requests.get(url, headers=headers)
        jsonData = json.loads(request.content)
        ct += 1
    except Exception as e:
        pass
        print(e)
    return jsonData, ct

# Get the default branch of the repository
def get_default_branch(lsttokens, repo):
    ct = 0
    url = 'https://api.github.com/repos' + repo
    jsonData, ct = github_auth(url, lsttokens, ct)
    if jsonData and 'default_branch' in jsonData:
        return jsonData['default_branch']
    return 'master'


# @dictFiles, empty dictionary of files
# @lstTokens, GitHub authentication tokens
# @repo, GitHub repo
def countfiles(dictfiles, lsttokens, repo):
    ipage = 1  # url page counter
    ct = 0  # token counter

    try:
        # loop though all the commit pages until the last returned empty page
        while True:
            spage = str(ipage)
            commitsUrl = 'https://api.github.com/repos/' + repo + '/commits?page=' + spage + '&per_page=100'
            jsonCommits, ct = github_auth(commitsUrl, lsttokens, ct)

            # break out of the while loop if there are no more commits in the pages
            if len(jsonCommits) == 0:
                break
            # iterate through the list of commits in  spage
            for shaObject in jsonCommits:
                sha = shaObject['sha']
                # For each commit, use the GitHub commit API to extract the files touched by the commit
                shaUrl = 'https://api.github.com/repos/' + repo + '/commits/' + sha
                shaDetails, ct = github_auth(shaUrl, lsttokens, ct)

                #Skip merge commits (multiple parents)
                if shaDetails and 'parents' in shaDetails and len(shaDetails['parents']) > 1:
                    continue

                if shaDetails and 'files' in shaDetails:
                    filesjson = shaDetails['files']
                    for filenameObj in filesjson:
                        filename = filenameObj['filename']
                        if should_include_file(filename):
                            dictfiles[filename] = dictfiles.get(filename, 0) + 1
                            print(filename)
            ipage += 1
    except:
        print("Error receiving data")
        exit(0)
# GitHub repo
repo = 'scottyab/rootbeer'
# repo = 'Skyscanner/backpack' # This repo is commit heavy. It takes long to finish executing
# repo = 'k9mail/k-9' # This repo is commit heavy. It takes long to finish executing
# repo = 'mendhak/gpslogger'


# put your tokens here
# Remember to empty the list when going to commit to GitHub.
# Otherwise they will all be reverted and you will have to re-create them
# I would advise to create more than one token for repos with heavy commits


dictfiles = dict()
countfiles(dictfiles, lstTokens, repo)
print('\nTotal number of files: ' + str(len(dictfiles)))

file = repo.split('/')[1]
# change this to the path of your file
fileOutput = 'data/file_' + file + '.csv'
rows = ["Filename", "Touches"]
fileCSV = open(fileOutput, 'w')
writer = csv.writer(fileCSV)
writer.writerow(rows)

bigcount = None
bigfilename = None
for filename, count in dictfiles.items():
    rows = [filename, count]
    writer.writerow(rows)
    if bigcount is None or count > bigcount:
        bigcount = count
        bigfilename = filename
fileCSV.close()
print('The file ' + bigfilename + ' has been touched ' + str(bigcount) + ' times.')
