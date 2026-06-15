"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { MessageSquare, Activity, Zap, Clock, CalendarDays, Download, Database, ShieldCheck, Server, Shield, Mail, Cloud, Monitor } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import Link from "next/link";
import { Badge } from "@/components/ui/badge";

const activeRooms = [
  "#inc-104-bruteforce",
  "#inc-105-phishing",
  "#inc-106-data-exfil"
];

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

export default function OverviewPage() {
  const [rooms, setRooms] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/rooms")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setRooms(data.slice(0, 5));
        } else {
          setRooms([]);
        }
      })
      .catch((err) => {
        console.error("Error fetching rooms:", err);
        setRooms([]);
      });
  }, []);

  const renderSeverityBadge = (severity: string) => {
    const s = (severity || "P2").toUpperCase();
    if (s === "P0" || s === "CRITICAL") return <Badge variant="destructive" className="font-mono">P0</Badge>;
    if (s === "P1" || s === "HIGH") return <Badge variant="secondary" className="bg-orange-500/15 text-orange-700 hover:bg-orange-500/25 border-transparent font-mono">P1</Badge>;
    if (s === "P2" || s === "MEDIUM") return <Badge variant="secondary" className="bg-yellow-500/15 text-yellow-700 hover:bg-yellow-500/25 border-transparent font-mono">P2</Badge>;
    if (s === "P3" || s === "LOW") return <Badge variant="secondary" className="font-mono">P3</Badge>;
    return <Badge variant="secondary" className="font-mono">P4</Badge>;
  };

  const getStatusColor = (status: string) => {
    const s = status?.toLowerCase() || '';
    if (s === 'active' || s === 'new' || s === 'investigating' || s === 'open') return 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
    if (s === 'resolved' || s === 'closed') return 'bg-slate-400';
    return 'bg-slate-300';
  };

  return (
    <div className="flex-1 space-y-4 pt-2">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <div className="flex items-center space-x-2">
          <Button variant="outline" className="hidden md:flex">
            <CalendarDays className="mr-2 h-4 w-4" />
            Jan 20, 2024 - Feb 09, 2024
          </Button>
          <Button>
            <Download className="mr-2 h-4 w-4" />
            Download
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Rooms</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeRooms.length}</div>
            <p className="text-xs text-muted-foreground">
              +2 since last hour
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Incidents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">412</div>
            <p className="text-xs text-muted-foreground">
              +12.5% from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mean Time to Detect</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2m 15s</div>
            <p className="text-xs text-muted-foreground">
              -14s from last week
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Manual Time Saved</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">184 hrs</div>
            <p className="text-xs text-muted-foreground">
              via AI auto-context this month
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Active Rooms</CardTitle>
            <CardDescription>You have {rooms.length} active incidents.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[120px] text-[10px] uppercase tracking-wider font-bold text-muted-foreground">Channel</TableHead>
                  <TableHead className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">Incident</TableHead>
                  <TableHead className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">Severity</TableHead>
                  <TableHead className="text-right text-[10px] uppercase tracking-wider font-bold text-muted-foreground">Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rooms.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-4 text-muted-foreground">
                      No active rooms found.
                    </TableCell>
                  </TableRow>
                ) : (
                  rooms.map((room: any) => (
                    <TableRow key={room.id} className="hover:bg-muted/50">
                      <TableCell>
                        <div className="flex items-center">
                          <div className={`w-2.5 h-2.5 rounded-full mr-2.5 ${getStatusColor(room.status)}`} />
                          <Link href={`/rooms/${room.id}`} className="font-mono text-xs font-medium hover:underline underline-offset-4">
                            #inc-{room.id.substring(0,5)}
                          </Link>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">{room.title}</TableCell>
                      <TableCell>
                        {renderSeverityBadge(room.severity)}
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground">
                        {timeAgo(room.created_at)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Incidents by Severity</CardTitle>
            <CardDescription>Distribution of active alerts.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center h-[200px]">
              <div className="flex-1 h-full min-h-[200px] min-w-0">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: "P0", value: 12, color: "#ef4444" },
                        { name: "P1", value: 45, color: "#f97316" },
                        { name: "P2", value: 184, color: "#eab308" },
                        { name: "P3", value: 171, color: "#94a3b8" },
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                    >
                      {[
                        { color: "#ef4444" },
                        { color: "#f97316" },
                        { color: "#eab308" },
                        { color: "#94a3b8" },
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ borderRadius: '8px', fontSize: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-col gap-4 ml-4 pr-8">
                {[
                  { name: "P0", value: 12, color: "bg-red-500" },
                  { name: "P1", value: 45, color: "bg-orange-500" },
                  { name: "P2", value: 184, color: "bg-yellow-500" },
                  { name: "P3", value: 171, color: "bg-slate-400" },
                ].map((item) => (
                  <div key={item.name} className="flex items-center justify-between min-w-[90px]">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 ${item.color} mr-2`} />
                      <span className="text-sm font-medium text-muted-foreground">{item.name}</span>
                    </div>
                    <span className="text-sm font-bold ml-4">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Top Assets Under Attack</CardTitle>
            <CardDescription>Endpoints involved in the most active incidents.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-5">
              {[
                { asset: "vpn-gw-primary", icon: Shield, hits: 450 },
                { asset: "auth-db-prod", icon: Database, hits: 284 },
                { asset: "mail-server-01", icon: Mail, hits: 156 },
                { asset: "payment-api-v2", icon: Cloud, hits: 92 },
                { asset: "john-doe-laptop", icon: Monitor, hits: 45 },
              ].map((item, i) => (
                <div key={i} className="flex flex-col space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <item.icon className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium leading-none">{item.asset}</span>
                    </div>
                    <span className="text-sm font-medium">{item.hits}</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden mt-2">
                    <div className="h-full bg-slate-400" style={{ width: `${Math.min((item.hits / 500) * 100, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Threat Classifications</CardTitle>
            <CardDescription>Breakdown of investigation categories.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-5">
              {[
                { label: "Brute Force", count: 142 },
                { label: "Phishing", count: 89 },
                { label: "Malware", count: 64 },
                { label: "Data Exfiltration", count: 45 },
                { label: "Insider Threat", count: 21 },
              ].map((item, i) => (
                <div key={i} className="flex flex-col space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium leading-none">{item.label}</span>
                    <span className="text-sm font-medium">{item.count}</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden mt-2">
                    <div className="h-full bg-indigo-400" style={{ width: `${Math.min((item.count / 150) * 100, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Active IOCs</CardTitle>
            <CardDescription>Most frequently detected indicators.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-5">
              {[
                { ioc: "192.168.1.5", type: "IP", count: 142, threat: "Malicious" },
                { ioc: "update-server-bin.com", type: "Domain", count: 89, threat: "Suspicious" },
                { ioc: "8e29bc40...a9f", type: "Hash", count: 34, threat: "Malicious" },
                { ioc: "10.0.0.42", type: "IP", count: 12, threat: "Investigating" },
                { ioc: "admin@evil.corp", type: "Email", count: 8, threat: "Suspicious" }
              ].map((item, i) => (
                <div key={i} className="flex items-center">
                  <div className="space-y-1">
                    <p className="text-sm font-medium leading-none">{item.ioc}</p>
                    <p className="text-sm text-muted-foreground">{item.type} • {item.threat}</p>
                  </div>
                  <div className="ml-auto font-medium">+{item.count}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}
