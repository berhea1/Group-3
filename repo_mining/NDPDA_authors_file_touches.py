import os
import csv
import requests

repo = "scottyab/rootbeer"


# token reading 
token = os.getenv("GITHUB_TOKEN")

if not token:
    print("Error: GITHUB_TOKEN is not set.")
    exit(1)

headers = {
    "Authorization": "Bearer " + token
}

#branch infos

repo_url = "https://api.github.com/repos/" + repo

response = requests.get(repo_url, headers=headers)
response.raise_for_status()
repo_info = response.json()

default_branch = repo_info["default_branch"]

print("Default branch:", default_branch)

# Source_files

source_files = []

with open("repo_mining/data/file_rootbeer.csv", "r") as file:
    reader = csv.DictReader(file)

    for row in reader:
        source_files.append(row["Filename"])

# Output

output_file = "repo_mining/NDPDA_authors_file_touches.csv"

with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "File Path",
        "Author",
        "Date",
        "Number of Changes"
    ])

    for filepath in source_files:
        changes = []
        page = 1

        while True:
            commits_url = "https://api.github.com/repos/" + repo + "/commits"
            params = {
                "sha": default_branch,
                "path": filepath,
                "per_page": 100,
                "page": page
            }
            response = requests.get(
                commits_url,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            commits = response.json()
            if len(commits) == 0:
                break

            for commit in commits:

                if commit["author"] is not None:
                    author = commit["author"]["login"]
                else:
                    author = commit["commit"]["author"]["name"]

                date = commit["commit"]["author"]["date"]
                changes.append([author, date])

            page += 1

        total_changes = len(changes)

        for author, date in changes:
            writer.writerow([
                filepath,
                author,
                date,
                total_changes
            ])

        print(filepath, "-", total_changes, "changes")


print("Finished collecting author and file-touch data.")