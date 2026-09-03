import csv
from datetime import datetime
import matplotlib.pyplot as plt

#files
input_file = "repo_mining/NDPDA_authors_file_touches.csv"
output_file = "repo_mining/NDPDA_file_activity.png"
activity = []

#colleciton
with open(input_file, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        activity.append({
            "file": row["File Path"],
            "author": row["Author"],
            "date": datetime.fromisoformat(
                row["Date"].replace("Z", "+00:00")
            )
        })

# starting the search
start_date = min(item["date"] for item in activity)

for item in activity:
    item["week"] = (item["date"] - start_date).days // 7

#one point per author
unique_activity = {}

for item in activity:
    key = (item["author"], item["file"], item["week"])
    unique_activity[key] = item

activity = list(unique_activity.values())

# Create a numbered Y-axis for the source files
files = sorted(set(item["file"] for item in activity))
file_numbers = {
    filename: index
    for index, filename in enumerate(files)
}

#  contributors
authors = sorted(set(item["author"] for item in activity))
plt.figure(figsize=(14, max(8, len(files) * 0.25)))

# pull each author's activity
for author in authors:
    author_activity = [
        item for item in activity
        if item["author"] == author
    ]
    #Values
    x_values = [
        item["week"]
        for item in author_activity
    ]
    y_values = [
        file_numbers[item["file"]]
        for item in author_activity
    ]
#PlotInfo
    plt.scatter(
        x_values,
        y_values,
        label=author,
        alpha=0.7
    )

#Axis Names
plt.xlabel("Weeks Since Beginning of Repository")
plt.ylabel("Source File")
plt.yticks(
    range(len(files)),
    files,
    fontsize=7
)
#title
plt.title("RootBeer Repository Source File Activity")
#legend
plt.legend(
    title="Author",
    bbox_to_anchor=(1.05, 1),
    loc="upper left",
    fontsize=7
)
#display
plt.tight_layout()
plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)
#end of plot
plt.close()

print("Scatter plot saved to:", output_file)