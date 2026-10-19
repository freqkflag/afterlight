import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Afterlight — Digital Estate Planning",
  description: "Your digital life, handled with care when you're gone.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
