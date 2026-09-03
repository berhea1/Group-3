import csv
import matplotlib.pyplot as plt
from datetime import datetime


# Files

inputFile = 'data/authors_file_touches_rootbeer.csv'
outputFile = 'KyleBurnsSchool_file_activity.png'


# Read data

data = []

with open(inputFile, 'r', newline='') as fileCSV:

    reader = csv.DictReader(fileCSV)

    for row in reader:

        data.append({
            'Filename': row['Filename'],
            'Author': row['Author'],
            'Date': datetime.fromisoformat(
                row['Date'].replace('Z', '+00:00')
            )
        })


if not data:
    print('No data found.')
    exit()


# Determine beginning of repository activity

repositoryStart = min(
    row['Date']
    for row in data
)

print(
    'Beginning of source-file activity: ' +
    str(repositoryStart)
)


# Get all source files

files = sorted(
    set(row['Filename'] for row in data)
)


# Assign each file a number

fileToNumber = {}

for index, filename in enumerate(files):
    fileToNumber[filename] = index + 1


# Calculate weeks since repository beginning

points = set()

for row in data:

    timeDifference = row['Date'] - repositoryStart

    weeks = timeDifference.days // 7

    points.add(
        (
            fileToNumber[row['Filename']],
            weeks,
            row['Author']
        )
    )


# Get authors

authors = sorted(
    set(
        author
        for filenumber, weeks, author in points
    )
)


# Assign a color to each author

cmap = plt.get_cmap('tab20')

authorToColor = {}

for index, author in enumerate(authors):

    authorToColor[author] = cmap(
        index % 20
    )


# Create scatter plot

plt.figure(figsize=(14, 10))


for filenumber, weeks, author in sorted(points):

    plt.scatter(
        filenumber,
        weeks,
        color=authorToColor[author]
    )


# Axis labels

plt.xlabel('Files')
plt.ylabel('Weeks')

plt.xticks(
    range(1, len(files) + 1)
)

plt.title(
    'Rootbeer Source File Activity'
)


# Create legend

handles = []

for author in authors:

    handle = plt.Line2D(
        [0],
        [0],
        marker='o',
        linestyle='',
        color=authorToColor[author],
        label=author
    )

    handles.append(handle)


plt.legend(
    handles=handles,
    title='Author',
    bbox_to_anchor=(1.05, 1),
    loc='upper left'
)


# Save plot

plt.tight_layout()

plt.savefig(
    outputFile,
    dpi=300,
    bbox_inches='tight'
)

plt.close()

print(
    'Scatter plot written to ' +
    outputFile
)