import json
import requests
import csv

import os
from urllib.parse import quote


if not os.path.exists("data"):
    os.makedirs("data")


# GitHub Authentication function
def github_auth(url, lsttoken, ct):
    jsonData = None
    try:
        headers = {}

        if len(lsttoken) > 0:
            ct = ct % len(lsttoken)
            headers = {'Authorization': 'Bearer {}'.format(lsttoken[ct])}
            ct += 1

        request = requests.get(url, headers=headers, timeout=30)
        request.raise_for_status()
        jsonData = json.loads(request.content)
    except Exception as e:
        print(e)

    return jsonData, ct


def read_source_files(fileInput):
    sourceFiles = []

    with open(fileInput, 'r', newline='', encoding='utf-8') as fileCSV:
        reader = csv.DictReader(fileCSV)

        for row in reader:
            sourceFiles.append(row["Filename"])

    return sourceFiles


# @sourceFiles, source files produced by the Task 1 script
# @lstTokens, GitHub authentication tokens
# @repo, GitHub repo
def collect_file_touches(sourceFiles, lstTokens, repo):
    ct = 0
    fileTouchRows = []

    try:
        repoUrl = "https://api.github.com/repos/" + repo
        repoDetails, ct = github_auth(repoUrl, lstTokens, ct)
        defaultBranch = repoDetails["default_branch"]

        for filename in sourceFiles:
            ipage = 1
            fileRows = []

            while True:
                commitsUrl = (
                    "https://api.github.com/repos/" + repo +
                    "/commits?sha=" + quote(defaultBranch, safe='') +
                    "&path=" + quote(filename, safe='') +
                    "&page=" + str(ipage) + "&per_page=100"
                )

                jsonCommits, ct = github_auth(commitsUrl, lstTokens, ct)

                if jsonCommits is None:
                    raise RuntimeError("Could not receive commits for " + filename)

                if len(jsonCommits) == 0:
                    break

                for shaObject in jsonCommits:
                    commit = shaObject["commit"]
                    authorInfo = commit.get("author")

                    if authorInfo is None:
                        authorInfo = commit.get("committer", {})

                    author = authorInfo.get("name", "Unknown")
                    dateChanged = authorInfo.get("date", "")

                    fileRows.append({
                        "Filename": filename,
                        "Author": author,
                        "Date": dateChanged
                    })

                if len(jsonCommits) < 100:
                    break

                ipage += 1

            numberOfTouches = len(fileRows)

            for row in fileRows:
                row["Touches"] = numberOfTouches
                fileTouchRows.append(row)

            print(filename + ": " + str(numberOfTouches) + " touches")

        return fileTouchRows

    except Exception as e:
        print("Error receiving data")
        print(e)
        exit(0)


# GitHub repo
repo = 'scottyab/rootbeer'

# CSV produced by davidpenrose_collect_files.py
fileInput = 'data/file_rootbeer.csv'
fileOutput = 'data/file_touches_rootbeer.csv'

lstTokens = []
token = os.environ.get("GITHUB_TOKEN")
if token:
    lstTokens.append(token)

sourceFiles = read_source_files(fileInput)
fileTouchRows = collect_file_touches(sourceFiles, lstTokens, repo)

fileCSV = open(fileOutput, 'w', newline='', encoding='utf-8')
writer = csv.DictWriter(
    fileCSV,
    fieldnames=["Filename", "Author", "Date", "Touches"]
)
writer.writeheader()

for row in sorted(
    fileTouchRows,
    key=lambda item: (item["Date"], item["Filename"], item["Author"])
):
    writer.writerow(row)

fileCSV.close()

print('Total number of file changes: ' + str(len(fileTouchRows)))
print('File-touch data written to ' + fileOutput)
