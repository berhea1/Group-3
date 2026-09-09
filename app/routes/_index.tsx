import type { MetaFunction } from "@remix-run/node";
import { redirect, type ActionFunctionArgs } from "@remix-run/node";
import {
  Form,
  useActionData,
  useLoaderData,
  useNavigation,
} from "@remix-run/react";
import { useRef, useState } from "react";

import { prisma } from "~/db.server";

export const meta: MetaFunction = () => [{ title: "Scan your RebelCard" }];
export async function action(args: ActionFunctionArgs) {
  const formData = await args.request.formData();
  const rebelCardId = formData.get("rebelCardId");
  if (typeof rebelCardId !== "string") {
    return { error: "Invalid RebelCard ID" };
  }

  const student = await prisma.student.findUnique({
    where: {
      rebelCardId,
    },
  });

  if (!student) {
    return {
      error:
        "RebelCard not recognized. Please see a Makerspace staff member to register your RebelCard.",
    };
  }

  return redirect(`/results/${student.nsheId}`);
}

export async function loader() {
  const demoStudents = await prisma.student.findMany({
    take: 3,
    orderBy: { createdAt: "desc" },
  });
  return {
    demoStudents: demoStudents.map((s) => ({
      name: s.name,
      rebelCardId: s.rebelCardId,
    })),
  };
}

export default function ScanPage() {
  const [cardId, setCardId] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const actionData = useActionData<typeof action>();
  const loaderData = useLoaderData<typeof loader>();
  const navigation = useNavigation();
  const scanning = navigation.state === "submitting";

  const error = actionData?.error;

  return (
    <div
      className="flex min-h-screen flex-col"
      style={{ background: "#111111" }}
    >
      {/* Header bar */}
      <header
        style={{ background: "#B10202" }}
        className="flex items-center gap-4 px-8 py-4"
      >
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-sm font-bold"
            style={{
              fontFamily: "Oswald, sans-serif",
              color: "#B10202",
              fontSize: "11px",
              lineHeight: 1,
              textAlign: "center",
              letterSpacing: "0.05em",
            }}
          >
            UNLV
          </div>
          <div>
            <p
              className="text-xs uppercase tracking-widest text-white/70"
              style={{ fontFamily: "Oswald, sans-serif" }}
            >
              University of Nevada, Las Vegas
            </p>
            <p
              className="text-sm font-semibold text-white"
              style={{
                fontFamily: "Oswald, sans-serif",
                letterSpacing: "0.08em",
              }}
            >
              MAKERSPACE ACCESS SYSTEM
            </p>
          </div>
        </div>
        <div className="ml-auto">
          <a
            href="/admin"
            className="text-xs uppercase tracking-widest text-white/60 transition-colors hover:text-white"
            style={{ fontFamily: "Oswald, sans-serif" }}
          >
            Admin →
          </a>
        </div>
      </header>

      {/* Main content */}
      <main className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        {/* UNLV Wordmark block */}
        <div className="mb-12 text-center">
          <div
            className="mb-1 text-7xl font-bold tracking-tight"
            style={{
              fontFamily: "Oswald, sans-serif",
              color: "#B10202",
              letterSpacing: "-0.01em",
            }}
          >
            UNLV
          </div>
          <div
            className="text-xl font-medium uppercase tracking-[0.2em] text-white/50"
            style={{ fontFamily: "Oswald, sans-serif" }}
          >
            College of Engineering Makerspace Access
          </div>
          <div
            className="mx-auto mt-3 h-px w-24"
            style={{ background: "#B10202" }}
          />
        </div>

        {/* Scan card */}
        <div
          className="w-full max-w-md rounded-sm"
          style={{ background: "#1c1c1c", border: "1px solid #2a2a2a" }}
        >
          {/* Card top accent */}
          <div
            className="h-1 w-full rounded-t-sm"
            style={{ background: "#B10202" }}
          />

          <div className="p-8">
            <h1
              className="mb-1 text-2xl font-semibold text-white"
              style={{
                fontFamily: "Oswald, sans-serif",
                letterSpacing: "0.05em",
              }}
            >
              REBELCARD CHECK-IN
            </h1>
            <p className="mb-8 text-sm" style={{ color: "#666666" }}>
              Swipe or scan your RebelCard, or enter your 10-digit card number
              below.
            </p>

            <Form className="space-y-4" method="POST">
              <div>
                <label
                  htmlFor="cardId"
                  className="mb-2 block text-xs uppercase tracking-widest"
                  style={{ fontFamily: "Oswald, sans-serif", color: "#888888" }}
                >
                  Card / NSHE Number
                </label>
                <input
                  ref={inputRef}
                  id="cardId"
                  type="text"
                  // eslint-disable-next-line jsx-a11y/no-autofocus
                  autoFocus
                  name="rebelCardId"
                  value={cardId}
                  onChange={(e) => setCardId(e.target.value)}
                  placeholder="1001234567"
                  className="w-full rounded-sm px-4 py-3 text-white placeholder-white/20 transition-all focus:outline-none"
                  style={{
                    background: "#111111",
                    border: "1px solid #333",
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "16px",
                    letterSpacing: "0.1em",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#B10202")}
                  onBlur={(e) => (e.target.style.borderColor = "#333")}
                />
              </div>

              {error != undefined ? (
                <div
                  className="rounded-sm px-4 py-3 text-sm"
                  style={{
                    background: "#2a0000",
                    border: "1px solid #5a0000",
                    color: "#ff8080",
                  }}
                >
                  {error}
                </div>
              ) : null}

              <button
                type="submit"
                disabled={scanning || !cardId.trim()}
                className="w-full rounded-sm py-3 font-semibold uppercase tracking-widest text-white transition-all disabled:opacity-40"
                style={{
                  fontFamily: "Oswald, sans-serif",
                  letterSpacing: "0.15em",
                  background: scanning ? "#8a0101" : "#B10202",
                  fontSize: "15px",
                }}
              >
                {scanning ? "Verifying..." : "Check In"}
              </button>
            </Form>

            {/* Demo hint */}
            <div
              className="mt-8 pt-6"
              style={{ borderTop: "1px solid #2a2a2a" }}
            >
              <p
                className="mb-2 text-xs"
                style={{
                  color: "#444",
                  fontFamily: "Oswald, sans-serif",
                  letterSpacing: "0.05em",
                }}
              >
                DEMO — TRY THESE IDs
              </p>
              <div className="space-y-1">
                {loaderData.demoStudents.map(({ rebelCardId, name }) => (
                  <button
                    key={rebelCardId}
                    onClick={() => setCardId(rebelCardId)}
                    className="flex w-full items-center gap-3 rounded-sm px-3 py-2 text-left transition-colors hover:bg-white/5"
                  >
                    <span
                      style={{
                        fontFamily: "JetBrains Mono, monospace",
                        color: "#B10202",
                        fontSize: "12px",
                      }}
                    >
                      {rebelCardId}
                    </span>
                    <span style={{ color: "#666", fontSize: "12px" }}>
                      {name}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <p className="mt-8 text-center text-xs" style={{ color: "#444" }}>
          Access is logged per university policy.{" "}
          <span style={{ color: "#666" }}>Unauthorized use is prohibited.</span>
        </p>
      </main>
    </div>
  );
}
