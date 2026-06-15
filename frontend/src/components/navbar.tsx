"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Overview", href: "/" },
    { name: "Incidents", href: "/rooms" },
    { name: "Integrations", href: "/integrations" },
    { name: "Test Chat", href: "/chat" },
  ];

  return (
    <header className="border-b bg-background">
      <div className="flex h-16 items-center px-4 md:px-8">
        <div className="flex items-center mr-6">
          <Link href="/" className="flex items-center">
            <span className="hidden font-bold sm:inline-flex items-center tracking-tight text-xl">
              WarRoom
              <Zap 
                className="h-5 w-5 ml-1 text-primary fill-primary" 
                strokeWidth={1.5} 
                style={{ transform: "scaleY(1.4) scaleX(0.8) translateY(-1px)" }} 
              />
            </span>
          </Link>
        </div>
        
        <nav className="flex items-center space-x-4 lg:space-x-6 mx-6">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`text-sm font-medium transition-colors hover:text-primary ${
                  isActive ? "text-primary" : "text-muted-foreground"
                }`}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center space-x-4">
          <div className="h-8 w-8 rounded-full bg-slate-200 border border-slate-300 flex items-center justify-center text-xs font-bold text-slate-700 cursor-pointer hover:ring-2 hover:ring-blue-600 hover:ring-offset-2 transition-all">
            SC
          </div>
        </div>
      </div>
    </header>
  );
}
