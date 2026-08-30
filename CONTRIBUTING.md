# Contributing

## First-time setup

Clone the repository and check out your assigned preview branch:

```text
git clone https://github.com/berhea1/Group-3.git
cd Group-3
git switch preview/<your-username>
```

Docker is not required on teammate computers. Portainer builds and runs the pushed branch on the shared Ubuntu server.

## Normal work

Before starting, bring the latest approved changes from `main` into your branch:

```text
git switch preview/<your-username>
git fetch origin
git merge origin/main
```

Make a focused change, then publish it:

```text
git add .
git commit -m "Describe the change"
git push origin preview/<your-username>
```

Portainer checks the branch and updates its preview. Test the change at the assigned preview address. When it is ready for the group, open a pull request from the preview branch into `main` and ask another teammate to review it.

## Rules

- Never commit `.env` files, passwords, tokens, or database exports.
- Never push directly to `main`.
- Keep each commit focused on one understandable change.
- Pull `main` into the preview branch regularly to reduce merge conflicts.
- Production data must not be copied into preview databases.
