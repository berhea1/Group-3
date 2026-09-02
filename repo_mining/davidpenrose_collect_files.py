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
        ct = ct % len(lstTokens)
        headers = {'Authorization': 'Bearer {}'.format(lsttoken[ct])}
        request = requests.get(url, headers=headers)
        jsonData = json.loads(request.content)
        ct += 1
    except Exception as e:
        pass
        print(e)
    return jsonData, ct

fileExtensionsLanguagesMap = {
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ header",
    ".java": "Java",
    ".kt": "Kotlin",
}

excludedFolders = {
    "build",
    "generated",
    "node_modules",
    "out",
    "target",
    "vendor"
}

# @dictFiles, empty dictionary of files
# @lstTokens, GitHub authentication tokens
# @repo, GitHub repo
def countfiles(dictFiles, lstTokens, repo):
    ct = 0
    
    try:
        repoUrl = "https://api.github.com/repos/" + repo
        repoDetails, ct = github_auth(repoUrl, lstTokens, ct)
        defaultBranch = repoDetails["default_branch"]

        treeUrl = (
        "https://api.github.com/repos/" + repo +
        "/git/trees/" + defaultBranch + "?recursive=1"
        )
        treeJson, ct = github_auth(treeUrl, lstTokens, ct)

        for fileObject in treeJson["tree"]:
            if fileObject["type"] == "blob":
                filename = fileObject["path"]

                if is_source_file(filename):
                    extension = os.path.splitext(filename)[1].lower()
                    dictFiles[filename] = fileExtensionsLanguagesMap[extension]
                    print(filename)

        return defaultBranch

    except Exception as e:
        print("Error receiving data")
        print(e)
        exit(0)
# GitHub repo
repo = 'scottyab/rootbeer'
# repo = 'Skyscanner/backpack' # This repo is commit heavy. It takes long to finish executing
# repo = 'k9mail/k-9' # This repo is commit heavy. It takes long to finish executing
# repo = 'mendhak/gpslogger'


def is_source_file(filename):
    extension = os.path.splitext(filename)[1].lower()

    if extension not in fileExtensionsLanguagesMap:
        return False

    folders = filename.lower().split("/")[:-1]
    for folder in folders:
        if folder in excludedFolders:
            return False

    return True

# put your tokens here
# Remember to empty the list when going to commit to GitHub.
# Otherwise they will all be reverted and you will have to re-create them
# I would advise to create more than one token for repos with heavy commits
lstTokens = []
token = os.environ.get("GITHUB_TOKEN")
if token:
    lstTokens.append(token)

dictFiles = dict()
countfiles(dictFiles, lstTokens, repo)
print('Total number of files: ' + str(len(dictFiles)))

file = repo.split('/')[1]
# change this to the path of your file
fileOutput = 'data/file_' + file + '.csv'
rows = ["Filename", "Language"]
fileCSV = open(fileOutput, 'w', newline='')
writer = csv.writer(fileCSV)
writer.writerow(rows)

for filename, language in dictFiles.items():
    writer.writerow([filename, language])

fileCSV.close()