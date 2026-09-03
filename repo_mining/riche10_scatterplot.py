import csv
from datetime import datetime
import matplotlib.pyplot as plt


def shorten_filename(path, max_length=45):
    if len(path) <= max_length:
        return path
    return "..." + path[-max_length:]


fileInput = 'data/file_touches_rootbeer.csv'
fileOutput = 'repo_mining/riche10_file_activity.png'

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


startDate = min(change["Date"] for change in fileChanges)

filenames = sorted(set(
    change["Filename"] for change in fileChanges
))

authors = sorted(set(
    change["Author"] for change in fileChanges
))

filePositions = {
    filename: position
    for position, filename in enumerate(filenames)
}


plt.figure(figsize=(18, 10))


for author in authors:
    xValues = []
    yValues = []

    for change in fileChanges:
        if change["Author"] == author:
            weekNumber = (change["Date"] - startDate).days // 7

            xValues.append(weekNumber)
            yValues.append(filePositions[change["Filename"]])

    plt.scatter(
        xValues,
        yValues,
        label=author
    )


shortFilenames = [
    shorten_filename(filename)
    for filename in filenames
]

plt.yticks(
    range(len(filenames)),
    shortFilenames,
    fontsize=7
)

plt.xlabel("Weeks Since Beginning of Repository")
plt.ylabel("Source Files")
plt.title("Rootbeer Source File Activity by Author")

plt.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    fontsize=7
)

plt.tight_layout()

plt.savefig(
    fileOutput,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("Scatter plot written to " + fileOutput)