"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Loader2, Download, FileText, User, Activity, Target, Shield, Clock, ExternalLink, ShieldCheck, Ticket } from "lucide-react";
import { SiJira, SiSlack, SiSplunk, SiVirustotal } from "react-icons/si";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Database, Laptop, AlertTriangle, ShieldAlert, Bot } from "lucide-react";

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

export default function InvestigationDetail() {
  const params = useParams();
  const id = params.id as string;
  const [room, setRoom] = useState<any>(null);
  const [showCollaborators, setShowCollaborators] = useState(false);
  const [showAllCollaborators, setShowAllCollaborators] = useState(false);

  useEffect(() => {
    fetch(`http://localhost:8000/api/rooms/${id}`)
      .then(res => res.json())
      .then(data => {
        if (data && data.id) {
          setRoom(data);
        } else {
          console.error("Invalid room data:", data);
        }
      })
      .catch(err => console.error("Error fetching room:", err));
  }, [id]);

  if (!room) return <div className="p-12 flex items-center justify-center bg-background h-full"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>;

  const mockSummary = "Multiple failed login attempts detected against the primary VPN gateway originating from 192.168.1.5, followed by a successful login by the user 'jsmith'. WarRoom automatically queried Splunk, cross-referenced the IP on VirusTotal (flagged as Malicious), and alerted the on-call engineer in Slack. The incident was escalated, the IP was blocked at the firewall, and a password reset was enforced for 'jsmith'.";
  const mockPersonnel = {
    commander: "Sarah Chen",
    firstResponder: "Alex Rivera",
  };

  const mockTimeline = [
    { time: "08:00 AM", title: "WarRoom Initialized", desc: "Slack channel #inc-104-bruteforce created from high-severity alert.", type: "system", sources: ["Slack"] },
    { time: "08:02 AM", title: "Autonomous Context Gathering", desc: "WarRoom Agent queried Splunk for surrounding events near 192.168.1.5.", type: "ai", sources: ["Splunk"] },
    { time: "08:05 AM", title: "Threat Intel Enrichment", desc: "Cross-referenced source IP with VirusTotal. Flagged as malicious (90/90 confidence).", type: "ai", sources: ["VirusTotal"] },
    { time: "08:07 AM", title: "First Responder Joined", desc: "Alex Rivera acknowledged the page and began investigation.", type: "user", sources: [] },
    { time: "08:15 AM", title: "Incident Handover", desc: "Escalated to Sarah Chen as Incident Commander.", type: "user", sources: ["Jira"] },
    { time: "08:30 AM", title: "Remediation", desc: "IP blocked at firewall. User jsmith password reset.", type: "action", sources: ["Palo Alto"] },
    { time: "09:00 AM", title: "Incident Closed", desc: "Threat contained. Finalizing report.", type: "system", sources: [] },
  ];

  const mockJiraTickets = [
    { id: "SEC-492", title: "Investigate VPN Brute Force", status: "In Progress" },
    { id: "IT-1082", title: "Reset credentials for jsmith", status: "Done" }
  ];

  const mockIdentifiedAssets = [
    { name: "vpn-gw-primary", type: "Gateway", context: "Target of external brute force attempts." },
    { name: "jsmith-laptop", type: "Endpoint", context: "Source of successful internal login post-attack." }
  ];

  const mockThreatClassifications = [
    { category: "Brute Force", confidence: 0.98 },
    { category: "Credential Access", confidence: 0.85 }
  ];

  const renderSeverityBadge = (severity: string) => {
    const s = (severity || "P2").toUpperCase();
    if (s === "P0" || s === "CRITICAL") return <Badge variant="destructive" className="font-mono">P0</Badge>;
    if (s === "P1" || s === "HIGH") return <Badge variant="secondary" className="bg-orange-500/15 text-orange-700 hover:bg-orange-500/25 border-transparent font-mono">P1</Badge>;
    if (s === "P2" || s === "MEDIUM") return <Badge variant="secondary" className="bg-yellow-500/15 text-yellow-700 hover:bg-yellow-500/25 border-transparent font-mono">P2</Badge>;
    if (s === "P3" || s === "LOW") return <Badge variant="secondary" className="font-mono">P3</Badge>;
    return <Badge variant="secondary" className="font-mono">P4</Badge>;
  };

  const getSourceIcon = (src: string) => {
    const s = src.toLowerCase();
    if (s.includes("slack")) return <SiSlack className="w-3.5 h-3.5 text-[#E01E5A]" />;
    if (s.includes("virustotal")) return <SiVirustotal className="w-3.5 h-3.5 text-blue-600" />;
    if (s.includes("splunk")) return <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Splunk_logo.svg/1280px-Splunk_logo.svg.png" alt="Splunk" className="h-2.5 w-auto object-contain opacity-70 grayscale" />;
    if (s.includes("jira")) return <SiJira className="w-3.5 h-3.5 text-[#0052CC]" />;
    if (s.includes("palo alto") || s.includes("crowdstrike")) return <ShieldAlert className="w-3.5 h-3.5 text-orange-600" />;
    return <Database className="w-3.5 h-3.5 text-slate-400" />;
  };

  return (
    <div className="flex-1 space-y-4 pt-2">
      
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-start justify-between space-y-2 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h2 className="text-3xl font-bold tracking-tight">{room.title}</h2>
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-2 ${room.status === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`} />
              <span className="text-sm font-medium text-muted-foreground capitalize">{room.status === 'active' ? 'Active' : 'Closed'}</span>
            </div>
            {renderSeverityBadge(room.severity)}
          </div>
          <p className="text-sm text-muted-foreground flex items-center font-medium">
            Created {timeAgo(room.created_at)} <span className="mx-2">•</span> Channel: #inc-{room.id.substring(0,5)}
          </p>
        </div>

        <div className="flex items-center space-x-6">
          <div className="relative">
            <div 
              className="flex items-center -space-x-2 cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setShowCollaborators(!showCollaborators)}
            >
              <div className="w-8 h-8 rounded-full border-2 border-background bg-blue-100 flex items-center justify-center text-[10px] font-bold text-blue-700 z-30" title="Sarah Chen (Commander)">SC</div>
              <div className="w-8 h-8 rounded-full border-2 border-background bg-emerald-100 flex items-center justify-center text-[10px] font-bold text-emerald-700 z-20" title="Alex Rivera (Responder)">AR</div>
              <div className="w-8 h-8 rounded-full border-2 border-background bg-purple-100 flex items-center justify-center text-[10px] font-bold text-purple-700 z-10" title="WarRoom Agent">AI</div>
              <div className="w-8 h-8 rounded-full border-2 border-background bg-muted flex items-center justify-center text-[10px] font-bold text-muted-foreground z-0" title="3 other collaborators">+3</div>
            </div>
            
            {showCollaborators && (
              <div className="absolute right-0 mt-2 w-64 bg-white border rounded-md shadow-lg z-50 p-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Active Collaborators</h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[10px] font-bold">SC</div>
                    <div className="flex-1"><p className="text-sm font-medium leading-none">Sarah Chen</p><p className="text-xs text-muted-foreground">Incident Commander</p></div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-[10px] font-bold">AR</div>
                    <div className="flex-1"><p className="text-sm font-medium leading-none">Alex Rivera</p><p className="text-xs text-muted-foreground">First Responder</p></div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-[10px] font-bold">AI</div>
                    <div className="flex-1"><p className="text-sm font-medium leading-none">WarRoom AI</p><p className="text-xs text-muted-foreground">Autonomous Agent</p></div>
                  </div>
                  {showAllCollaborators ? (
                    <div className="pt-2 mt-2 border-t space-y-3">
                      <div className="flex items-center gap-3 pt-1">
                        <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-[10px] font-bold">JD</div>
                        <div className="flex-1"><p className="text-sm font-medium leading-none">John Doe</p><p className="text-xs text-muted-foreground">Network Admin</p></div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-[10px] font-bold">ML</div>
                        <div className="flex-1"><p className="text-sm font-medium leading-none">Mike Lee</p><p className="text-xs text-muted-foreground">SOC Analyst</p></div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-[10px] font-bold">KW</div>
                        <div className="flex-1"><p className="text-sm font-medium leading-none">Kate Wong</p><p className="text-xs text-muted-foreground">Legal Counsel</p></div>
                      </div>
                    </div>
                  ) : (
                    <div 
                      className="pt-2 mt-2 border-t text-xs text-center text-muted-foreground cursor-pointer hover:underline"
                      onClick={() => setShowAllCollaborators(true)}
                    >
                      View 3 others
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button variant="outline" className="h-8 shadow-none">
              <SiSlack className="mr-2 h-3.5 w-3.5 text-[#E01E5A]" />
              Open in Slack
            </Button>
            <Button variant="outline" className="h-8 shadow-none">
              <FileText className="mr-2 h-3.5 w-3.5 text-blue-600" />
              Crisis Comm
            </Button>
            <Button variant="outline" className="h-8 w-8 p-0 shadow-none" title="Download Report">
              <Download className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        
        {/* Main Content Area */}
        <div className="col-span-4 space-y-4">

          <div className="bg-slate-50/50 border border-slate-200 rounded-lg p-5">
            <h3 className="text-sm font-semibold mb-2">Executive Summary</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              {mockSummary}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="border border-slate-200 rounded-lg p-5">
              <h3 className="text-sm font-semibold mb-1">AI Threat Classification</h3>
              <p className="text-xs text-muted-foreground mb-4">Model's assessment of threat categories.</p>
              <div className="space-y-4">
                {mockThreatClassifications.map((t, i) => (
                  <div key={i} className="flex flex-col space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 text-orange-500" />
                        <span className="text-sm font-medium leading-none">{t.category}</span>
                      </div>
                      <span className="text-[10px] font-bold text-muted-foreground">{Math.round(t.confidence * 100)}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden mt-1.5">
                      <div className="h-full bg-orange-400" style={{ width: `${t.confidence * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-slate-200 rounded-lg p-5">
              <h3 className="text-sm font-semibold mb-1">Identified Assets</h3>
              <p className="text-xs text-muted-foreground mb-4">Internal systems targeted or involved.</p>
              <div className="space-y-4">
                {mockIdentifiedAssets.map((asset, i) => (
                  <div key={i} className="flex flex-col space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Database className="w-3.5 h-3.5 text-blue-500" />
                        <span className="text-sm font-medium leading-none">{asset.name}</span>
                      </div>
                      <span className="text-[9px] uppercase font-bold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">{asset.type}</span>
                    </div>
                    <p className="text-xs text-muted-foreground ml-5 mt-1">{asset.context}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="border border-slate-200 rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold mb-1">Indicators of Compromise</h3>
                <p className="text-xs text-muted-foreground">Detected entities linked to this investigation.</p>
              </div>
              <Target className="h-4 w-4 text-slate-400" />
            </div>
            {(!room.evidence || room.evidence.length === 0) ? (
              <p className="text-sm text-slate-400 italic">No indicators pinned.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {room.evidence.map((ev: any, i: number) => (
                  <div key={i} className="flex items-center bg-slate-50 border border-slate-200 rounded-md px-2 py-1.5 hover:bg-slate-100 transition-colors cursor-default">
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mr-2">{ev.type}</span>
                    <code className="text-xs font-mono font-semibold text-slate-800 mr-2">{ev.value}</code>
                    {ev.malicious && <span className="w-1.5 h-1.5 rounded-full bg-red-500" title="Malicious" />}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="border border-slate-200 rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold mb-1">Linked Jira Tickets</h3>
                <p className="text-xs text-muted-foreground">External tracking and remediation tasks.</p>
              </div>
              <Ticket className="h-4 w-4 text-slate-400" />
            </div>
            <div className="space-y-3">
              {mockJiraTickets.map((ticket, i) => (
                <div key={i} className="flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <SiJira className="w-3.5 h-3.5 text-[#0052CC]" />
                    <div>
                      <p className="text-sm font-medium leading-none text-slate-800 group-hover:text-blue-600 transition-colors cursor-pointer">{ticket.title}</p>
                      <p className="text-[10px] text-slate-500 font-mono mt-1">{ticket.id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] uppercase font-bold text-slate-500 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded">{ticket.status}</span>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-300 group-hover:text-blue-500 transition-colors cursor-pointer" />
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Column (Timeline) */}
        <Card className="col-span-3 shadow-none border-slate-200">
          <CardHeader className="pb-3 border-b border-slate-100 mb-4">
            <CardTitle className="text-base">Activity Timeline</CardTitle>
            <CardDescription className="text-xs">Chronological log of events and actions.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative border-l border-slate-200 ml-3 space-y-8 pb-4 mt-2">
              {mockTimeline.map((event, i) => (
                <div key={i} className="relative pl-6">
                  <div className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-slate-300 ring-4 ring-background" />
                  
                  <div className="flex flex-col">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="text-sm font-semibold">{event.title}</h4>
                      <span className="text-xs font-medium text-muted-foreground">
                        {event.time}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 leading-relaxed">{event.desc}</p>
                    {event.sources && event.sources.length > 0 && (
                      <div className="flex flex-wrap gap-3 mt-3">
                        {event.sources.map((src, idx) => (
                          <div key={idx} className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                            {getSourceIcon(src)}
                            <span>{src}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
