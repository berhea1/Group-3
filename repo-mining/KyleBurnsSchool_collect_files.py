import json
import requests
import csv

import os

if not os.path.exists("data"):
 os.makedirs("data")

# GitHub Authentication function
def github_auth(url, lsttoken, ct):
    jsonData = None

    try:
        request = requests.get(url)
        jsonData = json.loads(request.content)
    except Exception as e:
        print(e)

    return jsonData, ct

# @dictFiles, empty dictionary of files
# @lstTokens, GitHub authentication tokens
# @repo, GitHub repo
def get_source_files(repo, lsttokens):
    # Repo Information
    repoURL = 'https://api.github.com/repos/' + repo
    repoInfo, ct = github_auth(repoURL, lsttokens, 0)

    # print(repoInfo)
    # Default Branch
    branch = repoInfo['default_branch']
    print('Default Branch: ' + branch)

    # Source File Extentions
    sourceExtensions = {
        '.java',
        '.kt',
        '.h',
        '.cpp'
    }

    # Get files in branch
    treeURL = (
        'https://api.github.com/repos/' + repo +
        '/git/trees/' + branch + '?recursive=1'
    )

    tree, ct = github_auth(treeURL, lsttokens, ct)
    sourceFiles = []

    for item in tree['tree']:
        if item['type'] != 'blob':
            continue

        filename = item['path']
        extension = os.path.splitext(filename)[1].lower()
        if extension in sourceExtensions:
            sourceFiles.append(filename)

    return sourceFiles

# GitHub repo
repo = 'scottyab/rootbeer'
# repo = 'Skyscanner/backpack' # This repo is commit heavy. It takes long to finish executing
# repo = 'k9mail/k-9' # This repo is commit heavy. It takes long to finish executing
# repo = 'mendhak/gpslogger'


# put your tokens here
# Remember to empty the list when going to commit to GitHub.
# Otherwise they will all be reverted and you will have to re-create them
# I would advise to create more than one token for repos with heavy commits
lstTokens = []

sourceFiles = get_source_files(repo, lstTokens)

print('Total number of source files: ' + str(len(sourceFiles)))

file = repo.split('/')[1]

fileOutput = 'data/file_' + file + '.csv'

fileCSV = open(fileOutput, 'w', newline='')
writer = csv.writer(fileCSV)

writer.writerow(['Filename'])

for filename in sourceFiles:
    writer.writerow([filename])
    print(filename)

fileCSV.close()

print('Source file list written to ' + fileOutput)
