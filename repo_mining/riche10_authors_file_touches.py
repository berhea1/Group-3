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
        print(e)

    return jsonData, ct


# @fileChanges, list of file changes
# @lstTokens, GitHub authentication tokens
# @repo, GitHub repo
def collect_file_touches(fileChanges, lsttokens, repo):
    ipage = 1
    ct = 0

    try:
        while True:
            spage = str(ipage)

            commitsUrl = (
                'https://api.github.com/repos/'
                + repo
                + '/commits?page='
                + spage
                + '&per_page=100'
            )

            jsonCommits, ct = github_auth(commitsUrl, lsttokens, ct)

            if len(jsonCommits) == 0:
                break

            for shaObject in jsonCommits:
                sha = shaObject['sha']

                shaUrl = (
                    'https://api.github.com/repos/'
                    + repo
                    + '/commits/'
                    + sha
                )

                shaDetails, ct = github_auth(shaUrl, lsttokens, ct)

                filesjson = shaDetails['files']

                author = shaDetails['commit']['author']['name']
                dateChanged = shaDetails['commit']['author']['date']

                for filenameObj in filesjson:
                    filename = filenameObj['filename']

                    if filename.endswith(('.java', '.kt', '.cpp', '.h')):
                        fileChanges.append([
                            filename,
                            author,
                            dateChanged
                        ])

                        print(filename, author, dateChanged)

            ipage += 1

    except Exception as e:
        print("Error receiving data")
        print(e)
        exit(0)


# GitHub repo
repo = 'scottyab/rootbeer'

# Get token from environment
lstTokens = []

token = os.environ.get("GITHUB_TOKEN")

if token:
    lstTokens.append(token)


fileChanges = []

collect_file_touches(fileChanges, lstTokens, repo)

print('Total number of file changes: ' + str(len(fileChanges)))


file = repo.split('/')[1]

fileOutput = 'data/file_touches_' + file + '.csv'

rows = ["Filename", "Author", "Date"]

fileCSV = open(fileOutput, 'w', newline='', encoding='utf-8')

writer = csv.writer(fileCSV)

writer.writerow(rows)

for filename, author, dateChanged in fileChanges:
    writer.writerow([
        filename,
        author,
        dateChanged
    ])

fileCSV.close()

print('File-touch data written to ' + fileOutput)