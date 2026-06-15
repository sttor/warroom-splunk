"use client";

import * as React from "react"
import { useRouter } from "next/navigation"
import {
  Calculator,
  Calendar,
  CreditCard,
  Settings,
  Smile,
  User,
  MessageSquare,
  LayoutDashboard,
  ShieldAlert
} from "lucide-react"

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command"

export function CommandPalette() {
  const [open, setOpen] = React.useState(false)
  const router = useRouter()

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const runCommand = React.useCallback((command: () => unknown) => {
    setOpen(false)
    command()
  }, [])

  return (
    <>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Type a command or search incidents..." />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          <CommandGroup heading="Navigation">
            <CommandItem onSelect={() => runCommand(() => router.push("/"))}>
              <LayoutDashboard className="mr-2 h-4 w-4" />
              <span>Overview</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push("/rooms"))}>
              <MessageSquare className="mr-2 h-4 w-4" />
              <span>Incidents</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push("/integrations"))}>
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings & Integrations</span>
            </CommandItem>
          </CommandGroup>
          <CommandSeparator />
          <CommandGroup heading="Quick Actions">
            <CommandItem onSelect={() => runCommand(() => router.push("/rooms"))}>
              <ShieldAlert className="mr-2 h-4 w-4 text-red-500" />
              <span>New Incident Investigation</span>
              <CommandShortcut>⌘N</CommandShortcut>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
