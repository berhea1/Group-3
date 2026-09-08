import type { LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";

import { prisma } from "~/db.server";

export async function loader(args: LoaderFunctionArgs) {
  const { nsheId } = args.params;
  if (!nsheId) {
    return { error: "Missing NSHE ID" };
  }
  const student = await prisma.student.findUnique({
    where: {
      nsheId,
    },
    include: {
      certifications: {
        include: {
          certification: true,
        },
      },
    },
  });
  if (!student) {
    return { error: "NSHE Id not found linked to a student" };
  }
  const machines = await prisma.machine.findMany({
    include: {
      requirements: {
        include: {
          certification: true,
        },
      },
    },
  });
  const useAbleMachines = machines.filter((m) => {
    const requiredCerts = m.requirements.map((r) => r.certification.name);
    const studentCerts = student.certifications.map(
      (c) => c.certification.name,
    );
    return requiredCerts.every((rc) => studentCerts.includes(rc));
  });
  return { student, useAbleMachines };
}

export default function Resutls() {
  const loaderData = useLoaderData<typeof loader>();
  if ("error" in loaderData) {
    return <div>Error: {loaderData.error}</div>;
  }
  const { student } = loaderData;
  return (
    <div>
      <h1>Student Info</h1>
      <p>Name: {student.name}</p>
      <p>Email: {student.email}</p>

      <div className="mt-4">
        <h2>Certifications</h2>
        <ul>
          {student.certifications.map((c) => (
            <li key={c.certificationId}>
              {c.certification.name} (completed at: {c.completedAt})
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4">
        <h2>Machines You Can Use</h2>
        <ul>
          {loaderData.useAbleMachines.map((m) => (
            <li key={m.id}>{m.name}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
