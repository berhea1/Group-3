import json
import requests
import csv

import os

repo = 'scottyab/rootbeer'

lstTokens = []

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

# Read source files from Task 1
source_file = []
with open("data/source_file_rootbeer.csv", "r") as fileCSV:
    reader = csv.DictReader(fileCSV)

    for row in reader:
        source_file.append(row["Filename"])
fileCSV.close()
print("Number of source files:", len(source_file))


# Determine default branch
ct = 0
repoUrl = 'https://api.github.com/repos/' + repo
repoInfo, ct = github_auth(repoUrl, lstTokens, ct)

default_branch = repoInfo['default_branch']
print("Default branch", default_branch)


# For each source file, collect commit info
rows = []

for filepath in source_file:
    print("Processing file:", filepath)

    page = 1
    touch_count = 0

    while True:
        commitsUrl = ('https://api.github.com/repos/' + repo + '/commits' + '?sha=' + default_branch 
        + '&path=' + filepath + '&page=' + str(page) + '&per_page=100')
        commits, ct = github_auth(commitsUrl, lstTokens, ct)

        # break out of the while loop if there are no more commits in the pages
        if len(commits) == 0:
            break

        for object in commits:
            commit = object["commit"]

            author = commit["author"]["name"]
            date = commit["author"]["date"]

            rows.append([filepath, author, date])

            touch_count += 1

        page += 1

    print("Touches: ", touch_count)


# Count total touches for every source file
touch_counts = {}

for row in rows:
    filepath = row[0]
    touch_counts[filepath] = (touch_counts.get(filepath, 0) + 1)



# Save results
file = repo.split('/')[1]

fileOutput = 'data/author_file_touches_' + file + '.csv'

# rows = ["Filename", "Author", "Date", "Touches"]

fileCSV = open(fileOutput, 'w')
writer = csv.writer(fileCSV)

writer.writerow(["Filename", "Author", "Date", "Touches"])
# writer.writerow(rows)
# writer.writerow([filename, author, date, touches])

# Write collected data
for row in rows:
    filepath = row[0]
    author = row[1]
    date = row[2]
    touches = touch_counts[filepath]

    writer.writerow([filepath, author, date, touches])

fileCSV.close()