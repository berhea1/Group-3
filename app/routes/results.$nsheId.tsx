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
    include: {},
  });
  if (!student) {
    return { error: "NSHE Id not found linked to a student" };
  }
  return { student };
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
    </div>
  );
}
