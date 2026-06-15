import os
import asyncio
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_splunk_mcp():
    print("Testing Splunk MCP Connection...")
    splunk_url = os.getenv("SPLUNK_MCP_URL")
    splunk_token = os.getenv("SPLUNK_MCP_TOKEN")
    
    if not splunk_token:
        print("❌ Missing SPLUNK_MCP_TOKEN")
        return
        
    print(f"Connecting to {splunk_url}...")
    
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    try:
        server_params = StdioServerParameters(
            command="npx",
            args=[
                "-y", "mcp-remote",
                splunk_url,
                "--header", f"Authorization: Bearer {splunk_token}"
            ]
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ Successfully initialized Splunk MCP session!")
                
                # Test 1: splunk_get_info
                try:
                    print("\n[Test 1] Executing splunk_get_info...")
                    res = await session.call_tool("splunk_get_info", {})
                    print(f"✅ Success: {res.content[0].text[:100]}...")
                except Exception as e:
                    print(f"❌ Failed: {e}")

                # Test 2: saia_generate_spl
                try:
                    print("\n[Test 2] Executing saia_generate_spl (Prompt: 'Show me all failed logins')...")
                    res = await session.call_tool("saia_generate_spl", {"prompt": "Show me all failed logins"})
                    print(f"✅ Success: {res.content[0].text}")
                except Exception as e:
                    print(f"❌ Failed: {e}")

                # Test 3: splunk_run_query
                try:
                    print("\n[Test 3] Executing splunk_run_query (SPL: '| makeresults | eval test=\"working\"')...")
                    res = await session.call_tool("splunk_run_query", {"query": "| makeresults | eval test=\"working\""})
                    print(f"✅ Success: {res.content[0].text}")
                except Exception as e:
                    print(f"❌ Failed: {e}")
                    
                # Test 4: saia_ask_splunk_question
                try:
                    print("\n[Test 4] Executing saia_ask_splunk_question (Prompt: 'What is a sourcetype?')...")
                    res = await session.call_tool("saia_ask_splunk_question", {"prompt": "What is a sourcetype?"})
                    print(f"✅ Success: {res.content[0].text[:150]}...")
                except Exception as e:
                    print(f"❌ Failed: {e}")

                return
                
    except Exception as e:
        print(f"❌ Splunk MCP Error: {e}")

async def test_virustotal():
    print("\n-------------------\nTesting VirusTotal API...")
    vt_key = os.getenv("VT_API_KEY")
    if not vt_key:
        print("❌ Missing VT_API_KEY")
        return
        
    ip = "8.8.8.8"
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {
        "accept": "application/json",
        "x-apikey": vt_key
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                print("✅ Successfully connected to VirusTotal API!")
                data = response.json()
                owner = data.get("data", {}).get("attributes", {}).get("as_owner")
                print(f"🔍 Test IP {ip} Owner: {owner}")
            else:
                print(f"❌ VirusTotal API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ VirusTotal Request Error: {e}")

async def main():
    await test_splunk_mcp()
    await test_virustotal()

if __name__ == "__main__":
    asyncio.run(main())
