import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Shell } from "@/components/shell";
import "./globals.css";
import "./forms.css";
import "./compare.css";
import "./accessibility.css";

export const metadata: Metadata = {
  title: { default: "EvalForge", template: "%s · EvalForge" },
  description: "Reproducible evaluation infrastructure for AI models and agents.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body><Shell>{children}</Shell></body></html>;
}
