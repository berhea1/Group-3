# Group-3

Git and GitHub

Docker startup applies migrations, runs the compiled Prisma seed, then starts
the app. Rebuild and deploy the image to pick up seed changes; no Docker access
or database tunnel is needed after deployment. Migration or seed failures stop
startup and are reported in the container logs.

The seed creates missing certifications, classes, machines, and the three demo
students. It creates `admin@unlv.nevada.edu` with the initial demo password
`makerspace-admin` only when that account is missing. Change that password before
using the deployment with real data. Later starts preserve existing accounts,
passwords, student records, awards, and machine requirements. Seed writes run in
one transaction, so a failure leaves no partially seeded data.
