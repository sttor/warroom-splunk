"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { CheckCircle2, Bot } from "lucide-react";
import { SiSplunk, SiVirustotal, SiJira, SiSlack } from "react-icons/si";

export default function IntegrationsPage() {
  const [config, setConfig] = useState<any>({});

  useEffect(() => {
    fetch("http://localhost:8000/api/config")
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(console.error);
  }, []);

  const saveConfig = async (e: React.FormEvent, type: string) => {
    e.preventDefault();
    const formData = new FormData(e.target as HTMLFormElement);
    const data = Object.fromEntries(formData.entries());
    
    // Merge existing config from state
    const payload = {
      splunk_mcp_url: type === 'splunk' ? data.url : config.splunk_mcp_url,
      splunk_mcp_token: type === 'splunk' ? data.token : config.has_splunk_token ? '********' : '',
      vt_api_key: type === 'vt' ? data.key : config.has_vt_key ? '********' : '',
      ollama_model: type === 'llm' ? data.model : config.ollama_model,
      llm_api_key: type === 'llm' ? data.key : config.has_llm_key ? '********' : '',
      llm_api_base: type === 'llm' ? data.base : config.llm_api_base || '',
      jira_mcp_url: type === 'jira' ? data.url : config.jira_mcp_url,
      jira_mcp_token: type === 'jira' ? data.token : config.has_jira_token ? '********' : '',
      slack_app_token: type === 'slack' ? data.app_token : config.has_slack_app_token ? '********' : '',
      slack_bot_token: type === 'slack' ? data.bot_token : config.has_slack_bot_token ? '********' : '',
    };

    try {
      await fetch("http://localhost:8000/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      // Refresh config to update UI status
      const res = await fetch("http://localhost:8000/api/config");
      setConfig(await res.json());
      
      // Close the modal by triggering a click on the dialog close button
      // Or we can just use a simple alert for now
      alert("Configuration saved successfully!");
      
      // Better way to close Dialog without controlled state:
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    } catch (err) {
      console.error(err);
      alert("Failed to save configuration.");
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Integrations</h1>
        <p className="text-slate-500 mt-2">Connect external data sources and AI models to empower your WarRoom agent.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Splunk Integration */}
        <Card className="flex flex-col shadow-none border hover:bg-slate-50 transition-colors">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between mb-2">
              <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Splunk_logo.svg/1280px-Splunk_logo.svg.png" alt="Splunk" className="h-7 w-auto object-contain opacity-80 grayscale" />
              {config.has_splunk_token && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
            </div>
            <CardTitle className="text-base">Splunk Enterprise</CardTitle>
            <CardDescription className="text-xs">Query security events natively via MCP.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-2">
             {/* Spacing */}
          </CardContent>
          <CardFooter>
            <Dialog>
              <DialogTrigger className={buttonVariants({ variant: config.has_splunk_token ? "outline" : "default", size: "sm", className: "w-full h-8 text-xs cursor-pointer" })}>
                {config.has_splunk_token ? "Configure" : "Connect"}
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Configure Splunk MCP</DialogTitle>
                  <DialogDescription>Enter your Splunk connection details.</DialogDescription>
                </DialogHeader>
                <form onSubmit={(e) => saveConfig(e, 'splunk')} className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="url">MCP URL</Label>
                    <Input id="url" name="url" defaultValue={config.splunk_mcp_url || ""} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="token">Bearer Token</Label>
                    <Input id="token" name="token" type="password" placeholder="ey..." />
                  </div>
                  <Button type="submit" className="w-full">Save Configuration</Button>
                </form>
              </DialogContent>
            </Dialog>
          </CardFooter>
        </Card>


        {/* VirusTotal Integration */}
        <Card className="flex flex-col shadow-none border hover:bg-slate-50 transition-colors">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between mb-2">
              <SiVirustotal className="w-8 h-8 text-slate-800" />
              {config.has_vt_key && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
            </div>
            <CardTitle className="text-base">VirusTotal</CardTitle>
            <CardDescription className="text-xs">Enrich IPs and Hashes with threat intel.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-2"></CardContent>
          <CardFooter>
            <Dialog>
              <DialogTrigger className={buttonVariants({ variant: config.has_vt_key ? "outline" : "default", size: "sm", className: "w-full h-8 text-xs cursor-pointer" })}>
                {config.has_vt_key ? "Configure" : "Connect"}
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Configure VirusTotal</DialogTitle>
                  <DialogDescription>Enter your VT API Key.</DialogDescription>
                </DialogHeader>
                <form onSubmit={(e) => saveConfig(e, 'vt')} className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="key">API Key</Label>
                    <Input id="key" name="key" type="password" />
                  </div>
                  <Button type="submit" className="w-full">Save Configuration</Button>
                </form>
              </DialogContent>
            </Dialog>
          </CardFooter>
        </Card>

        {/* LLM Connection */}
        <Card className="flex flex-col shadow-none border hover:bg-slate-50 transition-colors">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between mb-2">
              <Bot className="w-8 h-8 text-slate-800" />
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
            <CardTitle className="text-base">LLM Connection</CardTitle>
            <CardDescription className="text-xs">Connect to any AI provider (Local, OpenAI, Azure, Anthropic).</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-2">
             <div className="text-[10px] font-mono text-muted-foreground bg-slate-100 px-2 py-1 rounded inline-block">
               {config.ollama_model || "ollama/qwen2.5:latest"}
             </div>
          </CardContent>
          <CardFooter>
            <Dialog>
              <DialogTrigger className={buttonVariants({ variant: "default", size: "sm", className: "w-full h-8 text-xs cursor-pointer" })}>
                Configure
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Configure LLM</DialogTitle>
                  <DialogDescription>Enter your LiteLLM compatible model string and API key.</DialogDescription>
                </DialogHeader>
                <form onSubmit={(e) => saveConfig(e, 'llm')} className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="model">Model String</Label>
                    <Input id="model" name="model" defaultValue={config.ollama_model || "ollama/qwen2.5:latest"} placeholder="e.g. azure/gpt-5-mini or gpt-4o" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="base">Endpoint / API Base (Optional)</Label>
                    <Input id="base" name="base" defaultValue={config.llm_api_base || ""} placeholder="https://aiusage.../openai/v1/" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="key">API Key (Optional for Local)</Label>
                    <Input id="key" name="key" type="password" placeholder="sk-..." />
                  </div>
                  <Button type="submit" className="w-full">Save Configuration</Button>
                </form>
              </DialogContent>
            </Dialog>
          </CardFooter>
        </Card>

        {/* Jira MCP Integration */}
        <Card className="flex flex-col shadow-none border hover:bg-slate-50 transition-colors">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between mb-2">
              <SiJira className="w-8 h-8 text-slate-800" />
              {config.has_jira_token && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
            </div>
            <CardTitle className="text-base">Jira REST API</CardTitle>
            <CardDescription className="text-xs">Read and search Jira tickets natively via blazing-fast REST API.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-2"></CardContent>
          <CardFooter>
            <Dialog>
              <DialogTrigger className={buttonVariants({ variant: config.has_jira_token ? "outline" : "default", size: "sm", className: "w-full h-8 text-xs cursor-pointer" })}>
                {config.has_jira_token ? "Configure" : "Connect"}
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Configure Jira</DialogTitle>
                  <DialogDescription>Enter your Atlassian Cloud Workspace URL and credentials.</DialogDescription>
                </DialogHeader>
                <form onSubmit={(e) => saveConfig(e, 'jira')} className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="url">Workspace URL</Label>
                    <Input id="url" name="url" defaultValue={config.jira_mcp_url || ""} placeholder="https://your-company.atlassian.net" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="token">Auth (Email:Token)</Label>
                    <Input id="token" name="token" type="password" placeholder="user@company.com:ATLASSIAN_API_TOKEN" />
                  </div>
                  <Button type="submit" className="w-full">Save Configuration</Button>
                </form>
              </DialogContent>
            </Dialog>
          </CardFooter>
        </Card>

        {/* Slack Integration */}
        <Card className="flex flex-col shadow-none border hover:bg-slate-50 transition-colors">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between mb-2">
              <SiSlack className="w-8 h-8 text-slate-800" />
              {(config.has_slack_app_token && config.has_slack_bot_token) && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
            </div>
            <CardTitle className="text-base">Slack Socket Mode</CardTitle>
            <CardDescription className="text-xs">Connect WarRoom to Slack using Socket Mode (no webhooks required).</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-2"></CardContent>
          <CardFooter>
            <Dialog>
              <DialogTrigger className={buttonVariants({ variant: (config.has_slack_app_token && config.has_slack_bot_token) ? "outline" : "default", size: "sm", className: "w-full h-8 text-xs cursor-pointer" })}>
                {(config.has_slack_app_token && config.has_slack_bot_token) ? "Configure" : "Connect"}
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Configure Slack</DialogTitle>
                  <DialogDescription>Enter your Slack Socket Mode credentials.</DialogDescription>
                </DialogHeader>
                <form onSubmit={(e) => saveConfig(e, 'slack')} className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="app_token">App-Level Token</Label>
                    <Input id="app_token" name="app_token" type="password" placeholder="xapp-..." />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bot_token">Bot User Token</Label>
                    <Input id="bot_token" name="bot_token" type="password" placeholder="xoxb-..." />
                  </div>
                  <Button type="submit" className="w-full">Save Configuration</Button>
                </form>
              </DialogContent>
            </Dialog>
          </CardFooter>
        </Card>

      </div>
    </div>
  );
}
