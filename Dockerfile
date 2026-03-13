# Use the official Kali Linux Rolling base image
FROM kalilinux/kali-rolling

# Set environment variable to prevent interactive prompts during apt installations
ENV DEBIAN_FRONTEND=noninteractive

# Bypass the failing HTTPS CDN by forcing a direct, reliable HTTP mirror
RUN echo "deb http://kali.download/kali kali-rolling main contrib non-free non-free-firmware" > /etc/apt/sources.list

# Update the system and install Python, pip, and the needed Kali Linux tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    whois \
    dnsenum \
    whatweb \
    amass \
    netdiscover \
    nmap \
    enum4linux \
    smbclient \
    nikto \
    gobuster \
    dirb \
    ffuf \
    wfuzz \
    sqlmap \
    wpscan \
    hydra \
    john \
    hashcat \
    exploitdb \
    tcpdump \
    wordlists \
    metasploit-framework \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Extract rockyou.txt wordlist as it is zipped by default and used by our tools
RUN gzip -d /usr/share/wordlists/rockyou.txt.gz || true

# Install the MCP Python SDK. 
# Note: Kali Linux uses PEP 668, so we use --break-system-packages in this isolated container, 
# or you could alternatively set up a Python virtual environment.
RUN pip3 install mcp --break-system-packages

# Set the working directory inside the container
WORKDIR /app

# Copy the kali-mcp-server.py script into the container
COPY kali-mcp-server.py /app/kali-mcp-server.py

# Ensure the script has execution permissions
RUN chmod +x /app/kali-mcp-server.py

# Run the MCP server when the container starts
CMD ["python3", "/app/kali-mcp-server.py"]