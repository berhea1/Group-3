import csv
import matplotlib.pyplot as plt
from datetime import datetime



# Read CSV from Task 2

input_file = "data/author_file_touches_rootbeer.csv"

rows = []

with open(input_file, "r") as fileCSV:
    reader = csv.DictReader(fileCSV)

    for row in reader:
        rows.append(row)

print("Number of records:", len(rows))


# Find when the repo activity begins
dates = []

for row in rows:
    date = datetime.fromisoformat(
        row["Date"].replace("Z", "+00:00")
    )

    dates.append(date)

start_date = min(dates)
print("Repo beginning:", start_date)

# Calculate week 
activity = []

for row in rows:
    filepath = row["Filename"]
    author = row["Author"]

    date = datetime.fromisoformat(
        row["Date"].replace("Z", "+00:00")
    )

    days_since_start = (date - start_date).days
    week = days_since_start // 7

    activity.append([
        week,
        filepath,
        author
    ])


# Sort activity into one per author/file/week
unique_activity = set()

for item in activity:
    week = item[0]
    filepath = item[1]
    author = item[2]

    unique_activity.add(
        (week, filepath, author)
    )


# Find all the authors
authors = []

for item in unique_activity:
    authors.append(item[2])

unique_authors = sorted(set(authors))



# Scatter plot

unique_files = sorted(set(row["Filename"] for row in rows))

file_numbers = {}

for i in range(len(unique_files)):
    file_numbers[unique_files[i]] = i

plt.figure(figsize=(14, 10))

for author in unique_authors:

    weeks = []
    files = []

    for row in rows:

        if row["Author"] == author:

            date = datetime.fromisoformat(
                row["Date"].replace("Z", "+00:00")
            )

            days_since_start = (date - start_date).days
            week = days_since_start // 7

            file_number = file_numbers[row["Filename"]]

            files.append(file_number)
            weeks.append(week)


    plt.scatter(files, weeks, label=author, s=20)


# Labels
plt.xlabel("Files")
plt.ylabel("Weeks")
plt.title("Rootbeer Source File Activity")

plt.legend(
    title="Author",
    bbox_to_anchor=(1.05, 1),
    loc="upper left"
)

plt.tight_layout()


# Save visualization
output_file = "M-ming519_file_activity.png"

plt.savefig(
    output_file,
    bbox_inches="tight"
)

print("Scatter plot saved to:", output_file)

plt.show()