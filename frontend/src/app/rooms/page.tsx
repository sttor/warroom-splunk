"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, Globe, ArrowUpDown, Search } from "lucide-react";
import { SiSlack } from "react-icons/si";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const timeAgo = (dateStr: string) => {
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.floor(hours / 24);
  return `${days} days ago`;
};

export default function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [filterText, setFilterText] = useState("");
  const [sortField, setSortField] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const router = useRouter();

  useEffect(() => {
    fetch("http://localhost:8000/api/rooms")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setRooms(data);
        } else {
          setRooms([]);
        }
      })
      .catch((err) => {
        console.error("Error fetching rooms:", err);
        setRooms([]);
      });
  }, []);

  const getStatusColor = (status: string) => {
    const s = status?.toLowerCase() || '';
    if (s === 'active' || s === 'new' || s === 'investigating' || s === 'open') return 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
    if (s === 'resolved' || s === 'closed') return 'bg-slate-400';
    return 'bg-slate-300';
  };

  const renderSeverityBadge = (severity: string) => {
    const s = (severity || "P2").toUpperCase();
    if (s === "P0" || s === "CRITICAL") return <Badge variant="destructive" className="font-mono">P0</Badge>;
    if (s === "P1" || s === "HIGH") return <Badge variant="secondary" className="bg-orange-500/15 text-orange-700 hover:bg-orange-500/25 border-transparent font-mono">P1</Badge>;
    if (s === "P2" || s === "MEDIUM") return <Badge variant="secondary" className="bg-yellow-500/15 text-yellow-700 hover:bg-yellow-500/25 border-transparent font-mono">P2</Badge>;
    if (s === "P3" || s === "LOW") return <Badge variant="secondary" className="font-mono">P3</Badge>;
    return <Badge variant="secondary" className="font-mono">P4</Badge>;
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  const processedRooms = rooms
    .filter((r: any) => 
      r.title.toLowerCase().includes(filterText.toLowerCase()) || 
      r.id.toLowerCase().includes(filterText.toLowerCase()) ||
      r.status.toLowerCase().includes(filterText.toLowerCase())
    )
    .sort((a: any, b: any) => {
      let valA = a[sortField] || "";
      let valB = b[sortField] || "";
      
      if (sortField === "created_at") {
        valA = new Date(valA).getTime();
        valB = new Date(valB).getTime();
      }

      if (valA < valB) return sortOrder === "asc" ? -1 : 1;
      if (valA > valB) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });

  return (
    <div className="flex-1 space-y-4 pt-2">
      <div className="flex items-center justify-between space-y-2 mb-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Incidents</h2>
          <p className="text-sm text-muted-foreground">Manage and review active incidents.</p>
        </div>
        <div className="relative w-72">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="search"
            placeholder="Filter incidents..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 pl-8"
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-muted/50">
              <TableRow>
                <TableHead className="w-[300px] pl-6 cursor-pointer hover:bg-muted transition-colors select-none text-[10px] uppercase tracking-wider font-bold" onClick={() => handleSort('title')}>
                  Investigation <ArrowUpDown className="ml-1 h-3 w-3 inline" />
                </TableHead>
                <TableHead className="cursor-pointer hover:bg-muted transition-colors select-none text-[10px] uppercase tracking-wider font-bold" onClick={() => handleSort('severity')}>
                  Severity <ArrowUpDown className="ml-1 h-3 w-3 inline" />
                </TableHead>

                <TableHead className="cursor-pointer hover:bg-muted transition-colors select-none text-[10px] uppercase tracking-wider font-bold" onClick={() => handleSort('status')}>
                  Status <ArrowUpDown className="ml-1 h-3 w-3 inline" />
                </TableHead>
                <TableHead className="text-right pr-6 cursor-pointer hover:bg-muted transition-colors select-none text-[10px] uppercase tracking-wider font-bold" onClick={() => handleSort('created_at')}>
                  Created <ArrowUpDown className="ml-1 h-3 w-3 inline" />
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {processedRooms.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No incidents found matching your filter.
                  </TableCell>
                </TableRow>
              ) : (
                processedRooms.map((room: any) => (
                  <TableRow key={room.id} className="cursor-pointer hover:bg-muted/50" onClick={() => router.push(`/rooms/${room.id}`)}>
                    <TableCell className="pl-6">
                      <div className="font-medium text-sm">{room.title}</div>
                      <div className="text-xs text-muted-foreground font-mono mt-1">
                        #inc-{room.id.substring(0,5)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {renderSeverityBadge(room.severity)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center">
                        <div className={`w-2.5 h-2.5 rounded-full mr-2.5 ${getStatusColor(room.status)}`} />
                        <span className="text-sm font-medium text-muted-foreground capitalize">{room.status}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right text-sm text-muted-foreground pr-6">
                      {timeAgo(room.created_at)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
