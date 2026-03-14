#!/usr/bin/env python3
# This script connects the MCP AI agent natively to Kali Linux tools using FastMCP.

import subprocess
import shlex
import tempfile
import os

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("KaliLinuxMCP")

def run_cmd(command: list[str], timeout: int = 300) -> str:
    """Helper function to execute shell commands safely with a timeout."""
    try:
        # Check if the tool exists in PATH first
        subprocess.run(["which", command[0]], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        return f"Error: Tool '{command[0]}' is not installed or not in PATH."

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        output = result.stdout
        if result.stderr:
            output += f"\n[Standard Error/Warnings]:\n{result.stderr}"
        return output if output.strip() else "[Command executed successfully with no output]"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# ==========================================
# 1. INFORMATION GATHERING & RECONNAISSANCE
# ==========================================

@mcp.tool()
def whois_lookup(domain: str) -> str:
    """Perform a WHOIS lookup on a domain to find registration and ownership details."""
    return run_cmd(["whois", domain], timeout=30)

@mcp.tool()
def dnsenum_scan(domain: str) -> str:
    """Run Dnsenum to enumerate DNS records for a domain."""
    return run_cmd(["dnsenum", "--noreverse", domain], timeout=60)

@mcp.tool()
def whatweb_scan(target_url: str) -> str:
    """Run WhatWeb to identify CMS, web technologies, and headers of a website."""
    return run_cmd(["whatweb", "-v", target_url], timeout=60)

@mcp.tool()
def amass_enum(domain: str) -> str:
    """Run OWASP Amass for subdomain enumeration (passive mode for speed)."""
    return run_cmd(["amass", "enum", "-passive", "-d", domain], timeout=300)

@mcp.tool()
def netdiscover_scan(ip_range: str) -> str:
    """Run Netdiscover to find active hosts on a local subnet (requires root). Example ip_range: '192.168.1.0/24'"""
    return run_cmd(["netdiscover", "-P", "-r", ip_range], timeout=120)

# ==========================================
# 2. SCANNING & ENUMERATION
# ==========================================

@mcp.tool()
def nmap_scan(target: str, flags: str = "-sV -F") -> str:
    """Run an Nmap scan for network discovery and port scanning [1]."""
    return run_cmd(["nmap"] + shlex.split(flags) + [target])

@mcp.tool()
def enum4linux_scan(target_ip: str) -> str:
    """Run Enum4linux to enumerate information from Windows and Samba systems."""
    return run_cmd(["enum4linux", "-a", target_ip], timeout=300)

@mcp.tool()
def smbclient_list(target_ip: str, user: str = "", password: str = "") -> str:
    """List SMB shares on a target using smbclient."""
    cmd = ["smbclient", "-L", f"\\\\{target_ip}"]
    if user:
        cmd.extend(["-U", f"{user}%{password}"])
    else:
        cmd.append("-N") # No password
    return run_cmd(cmd, timeout=60)

# ==========================================
# 3. WEB VULNERABILITY & DIRECTORY BRUTEFORCING
# ==========================================

@mcp.tool()
def nikto_scan(target_url: str) -> str:
    """Run a Nikto web vulnerability scan against a target URL [1]."""
    return run_cmd(["nikto", "-h", target_url, "-Tuning", "123"], timeout=600)

@mcp.tool()
def gobuster_dir(target_url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt") -> str:
    """Run Gobuster to brute-force directories and files on a web server [1]."""
    return run_cmd(["gobuster", "dir", "-u", target_url, "-w", wordlist, "-q"], timeout=600)

@mcp.tool()
def dirb_scan(target_url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt") -> str:
    """Run Dirb for web content scanning [1]."""
    return run_cmd(["dirb", target_url, wordlist, "-S"], timeout=600)

@mcp.tool()
def ffuf_scan(target_url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt") -> str:
    """Run FFUF (Fuzz Faster U Fool) for fast web directory fuzzing. Target URL must include the 'FUZZ' keyword."""
    return run_cmd(["ffuf", "-u", target_url, "-w", wordlist, "-s"], timeout=600)

@mcp.tool()
def wfuzz_scan(target_url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt") -> str:
    """Run Wfuzz to fuzz web application parameters or directories. Target URL must include 'FUZZ'."""
    return run_cmd(["wfuzz", "-c", "-z", f"file,{wordlist}", "--hc", "404", target_url], timeout=600)

@mcp.tool()
def sqlmap_scan(target_url: str, params: str = "--batch --dbs") -> str:
    """Run SQLMap to detect and exploit SQL injection flaws. Runs in --batch mode automatically."""
    return run_cmd(["sqlmap", "-u", target_url] + shlex.split(params))

@mcp.tool()
def wpscan_enum(target_url: str) -> str:
    """Run WPScan to scan a WordPress site for vulnerabilities and enumerate users/plugins."""
    return run_cmd(["wpscan", "--url", target_url, "--enumerate", "vp,u", "--no-banner"], timeout=600)

# ==========================================
# 4. PASSWORD CRACKING & BRUTE FORCING
# ==========================================

# ==========================================
# 4. PASSWORD CRACKING & BRUTE FORCING
# ==========================================

@mcp.tool() 
def hydra_bruteforce(target: str, service: str, user: str, wordlist: str = "/usr/share/wordlists/rockyou.txt") -> str: 
    """Run THC-Hydra to brute force login credentials for a specific service (e.g., ssh, ftp).""" 
    return run_cmd(["hydra", "-l", user, "-P", wordlist, target, service], timeout=900) 


@mcp.tool() 
def john_crack(hash_string: str, wordlist: str = "/usr/share/wordlists/rockyou.txt") -> str: 
    """Run John the Ripper to crack an inline password hash string.""" 
    # John requires a file, so we write the inline hash to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_hash_file:
        temp_hash_file.write(hash_string)
        temp_path = temp_hash_file.name

    try:
        # Run John against the temporary file
        result = run_cmd(["john", "--wordlist=" + wordlist, temp_path], timeout=900)
        return result
    finally:
        # Ensure the temporary file is deleted after execution
        if os.path.exists(temp_path):
            os.remove(temp_path)


@mcp.tool() 
def hashcat_crack(hash_string: str, hash_type: str = "0", wordlist: str = "/usr/share/wordlists/rockyou.txt") -> str: 
    """Run Hashcat to crack an inline hash string. Note: Hashcat can be very resource-intensive.""" 
    # Hashcat can accept the hash directly in the command line arguments
    return run_cmd(["hashcat", "-m", hash_type, "-a", "0", hash_string, wordlist, "--potfile-disable"], timeout=900)

# ==========================================
# 5. EXPLOITATION & SNIFFING
# ==========================================

@mcp.tool()
def searchsploit_query(query: str) -> str:
    """Search the Exploit Database using SearchSploit for known vulnerabilities."""
    return run_cmd(["searchsploit", query])

@mcp.tool()
def tcpdump_sniff(interface: str = "eth0", packet_count: str = "10") -> str:
    """Capture a specific number of network packets using tcpdump (Requires Root)."""
    return run_cmd(["tcpdump", "-i", interface, "-c", packet_count, "-n"])

@mcp.tool()
def metasploit_exploit(module: str, options: str) -> str:
    """
    Execute a Metasploit module against a target.
    Provide the module name (e.g., 'exploit/windows/smb/ms17_010_eternalblue').
    Provide options as a comma-separated string of KEY=VALUE pairs 
    (e.g., 'RHOSTS=192.168.1.100, LHOST=10.0.0.5, LPORT=4444').
    """
    # Build the msfconsole command sequence
    msf_commands = [f"use {module}"]
    
    # Parse the options and add 'set' commands
    if options:
        for opt in options.split(','):
            if '=' in opt:
                key, value = opt.split('=', 1)
                msf_commands.append(f"set {key.strip()} {value.strip()}")
                
    # Append the run/exploit command and exit so the process doesn't hang
    msf_commands.append("exploit")
    msf_commands.append("exit")
    
    # Join the commands with semicolons for the -x flag
    execution_script = "; ".join(msf_commands)
    
    # Run the command using the run_cmd helper we built earlier
    # Metasploit can take a while to initialize and run exploits, so a longer timeout is wise
    return run_cmd(["msfconsole", "-q", "-x", execution_script], timeout=600)

# ==========================================
# SERVER INITIALIZATION
# ==========================================

if __name__ == "__main__":
    # Let standard output know the server is healthy
    # Always run the MCP server via stdio / Streamable HTTP transport to be added later
    mcp.run(transport="stdio")