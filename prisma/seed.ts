import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function seed() {
  // ── Admin account ────────────────────────────────────────────
  const adminEmail = "admin@unlv.nevada.edu";
  await prisma.user.deleteMany({ where: { email: adminEmail } });
  const admin = await prisma.user.create({
    data: {
      email: adminEmail,
      password: { create: { hash: await bcrypt.hash("makerspace-admin", 10) } },
    },
  });

  // ── Certifications ───────────────────────────────────────────
  const certNames = [
    "FDM 3D Printing Fundamentals",
    "Composite & Fiber Printing",
    "Shop Safety & General Machining",
    "CNC Operation & G-Code Basics",
    "Metal Lathe Operation",
    "Laser Cutter Safety & Operation",
    "MIG/TIG Welding Certification",
  ] as const;

  const certs: Record<string, { id: string }> = {};
  for (const name of certNames) {
    certs[name] = await prisma.certification.upsert({
      where: { name },
      update: {},
      create: { name },
    });
  }

  // ── Classes (each awards its matching certification) ─────────
  for (const name of certNames) {
    await prisma.class.upsert({
      where: { name: `${name} — Training` },
      update: {},
      create: {
        name: `${name} — Training`,
        awardsCertificationId: certs[name].id,
      },
    });
  }

  // ── Machine categories & machines ───────────────────────────
  const machines: {
    category: string;
    sortOrder: number;
    name: string;
    requires: (typeof certNames)[number][];
  }[] = [
    {
      category: "3D Printing",
      sortOrder: 1,
      name: "Prusa MK4S",
      requires: ["FDM 3D Printing Fundamentals"],
    },
    {
      category: "3D Printing",
      sortOrder: 1,
      name: "Bambu Lab X1C",
      requires: ["FDM 3D Printing Fundamentals"],
    },
    {
      category: "3D Printing",
      sortOrder: 1,
      name: "Markforged Mark Two",
      requires: ["Composite & Fiber Printing"],
    },
    {
      category: "3D Printing",
      sortOrder: 1,
      name: "Ultimaker S5",
      requires: ["FDM 3D Printing Fundamentals"],
    },
    {
      category: "CNC Machining",
      sortOrder: 2,
      name: "Tormach PCNC 440",
      requires: [
        "Shop Safety & General Machining",
        "CNC Operation & G-Code Basics",
      ],
    },
    {
      category: "CNC Routing",
      sortOrder: 3,
      name: "ShopBot PRSalpha",
      requires: ["Shop Safety & General Machining"],
    },
    {
      category: "Metal Lathe",
      sortOrder: 4,
      name: "Haas ST-10 Lathe",
      requires: ["Shop Safety & General Machining", "Metal Lathe Operation"],
    },
    {
      category: "Laser Cutting",
      sortOrder: 5,
      name: "Epilog Fusion Pro 48",
      requires: ["Laser Cutter Safety & Operation"],
    },
    {
      category: "Laser Cutting",
      sortOrder: 5,
      name: "Glowforge Pro",
      requires: ["Laser Cutter Safety & Operation"],
    },
    {
      category: "Welding",
      sortOrder: 6,
      name: "Miller Multimatic 220",
      requires: [
        "Shop Safety & General Machining",
        "MIG/TIG Welding Certification",
      ],
    },
  ];

  for (const m of machines) {
    const category = await prisma.machineCategory.upsert({
      where: { name: m.category },
      update: { sortOrder: m.sortOrder },
      create: { name: m.category, sortOrder: m.sortOrder },
    });
    const machine = await prisma.machine.upsert({
      where: { name: m.name },
      update: { categoryId: category.id },
      create: { name: m.name, categoryId: category.id },
    });
    await prisma.machineRequirement.deleteMany({
      where: { machineId: machine.id },
    });
    await prisma.machineRequirement.createMany({
      data: m.requires.map((r) => ({
        machineId: machine.id,
        certificationId: certs[r].id,
      })),
    });
  }

  // ── Demo students (match the design mockups) ────────────────
  const students: {
    name: string;
    nsheId: string;
    email: string;
    cardNumber: string;
    certs: { name: (typeof certNames)[number]; completedAt: string }[];
  }[] = [
    {
      name: "Maria Sanchez",
      nsheId: "2001234567",
      email: "m.sanchez@unlv.nevada.edu",
      cardNumber: "1001234567",
      certs: [
        { name: "FDM 3D Printing Fundamentals", completedAt: "2025-09-15" },
        { name: "Laser Cutter Safety & Operation", completedAt: "2025-11-02" },
      ],
    },
    {
      name: "James Okafor",
      nsheId: "2009876543",
      email: "j.okafor@unlv.nevada.edu",
      cardNumber: "1009876543",
      certs: [
        { name: "FDM 3D Printing Fundamentals", completedAt: "2025-08-20" },
        { name: "Shop Safety & General Machining", completedAt: "2025-09-01" },
        { name: "CNC Operation & G-Code Basics", completedAt: "2025-10-10" },
        { name: "Metal Lathe Operation", completedAt: "2025-11-20" },
      ],
    },
    {
      name: "Taylor Kim",
      nsheId: "2005551234",
      email: "t.kim@unlv.nevada.edu",
      cardNumber: "1005551234",
      certs: [],
    },
  ];

  for (const s of students) {
    const student = await prisma.student.upsert({
      where: { nsheId: s.nsheId },
      update: { name: s.name, email: s.email, rebelCardId: s.cardNumber },
      create: {
        name: s.name,
        nsheId: s.nsheId,
        email: s.email,
        rebelCardId: s.cardNumber,
      },
    });

    for (const c of s.certs) {
      await prisma.studentCertification.upsert({
        where: {
          studentId_certificationId: {
            studentId: student.id,
            certificationId: certs[c.name].id,
          },
        },
        update: { completedAt: new Date(c.completedAt) },
        create: {
          studentId: student.id,
          certificationId: certs[c.name].id,
          completedAt: new Date(c.completedAt),
          awardedById: admin.id,
        },
      });
    }
  }

  console.log(`Database has been seeded. 🌱`);
}

seed()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
