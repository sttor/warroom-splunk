import { Inter } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/navbar";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-background text-foreground antialiased`}>
        <div className="flex min-h-screen flex-col">
          {/* Top Navigation Bar */}
          <Navbar />

          {/* Main Content Area */}
          <main className="flex-1 flex-col flex bg-background p-8 md:p-10 pt-6">
            <div className="mx-auto w-full max-w-7xl">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
