import csv
import os

from datetime import datetime
import matplotlib.pyplot as plt


fileInput = 'data/file_touches_rootbeer.csv'
fileOutput = 'repo_mining/davidpenrose_file_activity.png'


if not os.path.exists("repo_mining"):
    os.makedirs("repo_mining")


fileChanges = []

with open(fileInput, 'r', newline='', encoding='utf-8') as fileCSV:
    reader = csv.DictReader(fileCSV)

    for row in reader:
        dateChanged = datetime.strptime(
            row["Date"],
            "%Y-%m-%dT%H:%M:%SZ"
        )

        fileChanges.append({
            "Filename": row["Filename"],
            "Author": row["Author"],
            "Date": dateChanged
        })


if len(fileChanges) == 0:
    print("No file-touch data was found")
    raise SystemExit(1)


startDate = min(change["Date"] for change in fileChanges)

filenames = sorted(set(
    change["Filename"] for change in fileChanges
))

authors = sorted(set(
    change["Author"] for change in fileChanges
))

filePositions = {}
for position, filename in enumerate(filenames):
    filePositions[filename] = position

activityPoints = set()

for change in fileChanges:
    weekNumber = (change["Date"] - startDate).days // 7
    activityPoints.add((
        weekNumber,
        change["Filename"],
        change["Author"]
    ))


plt.figure(figsize=(20, 11))
colorMap = plt.colormaps["tab20"].resampled(len(authors))

for authorNumber, author in enumerate(authors):
    xValues = []
    yValues = []

    for weekNumber, filename, pointAuthor in sorted(activityPoints):
        if pointAuthor == author:
            xValues.append(weekNumber)
            yValues.append(filePositions[filename])

    plt.scatter(
        xValues,
        yValues,
        color=colorMap(authorNumber),
        label=author,
        s=32,
        alpha=0.85
    )


plt.yticks(
    range(len(filenames)),
    filenames,
    fontsize=8
)

plt.xlabel("Weeks Since Beginning of Repository")
plt.ylabel("Source Files")
plt.title("Rootbeer Source File Activity by Author")
plt.grid(axis="x", linestyle="--", alpha=0.35)
plt.gca().invert_yaxis()

plt.legend(
    title="Authors",
    bbox_to_anchor=(1.01, 1),
    loc="upper left",
    fontsize=8
)

plt.tight_layout()
plt.savefig(fileOutput, dpi=300, bbox_inches="tight")
plt.close()


print("Repository start date: " + startDate.strftime("%Y-%m-%d"))
print("Number of source files: " + str(len(filenames)))
print("Number of authors: " + str(len(authors)))
print("Number of plotted points: " + str(len(activityPoints)))
print("Scatter plot written to " + fileOutput)
