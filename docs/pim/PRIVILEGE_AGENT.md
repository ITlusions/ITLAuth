# Privilege Elevation Agent

**Local privilege management voor Windows, Linux en macOS workstations**

De Privilege Agent is een achtergrond service die draait op eindgebruiker machines en synchroniseert PIM elevations van Keycloak naar lokale gebruikersgroepen. Engineers krijgen tijdelijke admin rechten zonder permanente privileges.

---

## Inhoudsopgave

1. [Overzicht](#overzicht)
2. [Architectuur](#architectuur)
3. [Installatie](#installatie)
4. [Configuratie](#configuratie)
5. [Agent Implementatie](#agent-implementatie)
6. [Machine Enrollment](#machine-enrollment)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
8. [Security](#security)
9. [Production Deployment](#production-deployment)

---

## Overzicht

### Use Cases

**Scenario 1: Software Installatie**
```bash
itlc elevate --type=local-group --name=local-admin --duration=30m --reason="Install Docker Desktop"

# Agent detecteert binnen 30 seconden
# → Voegt user toe aan Administrators groep
# → Na 30 minuten: automatic removal
```

**Scenario 2: Troubleshooting**
```bash
itlc elevate --type=local-group --name=local-docker --duration=1h --reason="Debug container issue"

# Agent voegt toe aan docker groep
# → Toegang tot Docker daemon
# → Geen volledige admin rechten nodig
```

**Scenario 3: Emergency Access**
```bash
itlc elevate --type=local-group --name=local-admin --duration=4h \
  --reason="Security incident SEC-2026-001" \
  --ticket=SEC-2026-001

# Requires approval
# → Bij goedkeuring: Local admin access
# → Alle acties gelogd naar SIEM
```

**Scenario 4: Software Installatie (ZONDER admin rechten)**
```bash
# User wil Docker Desktop installeren
itlc install --app=docker-desktop --reason="Need Docker for development"

# Agent workflow:
# 1. Check whitelist → docker-desktop is approved voor developers
# 2. Download installer (van approved source)
# 3. Execute silent install als SYSTEM
# 4. User heeft NOOIT admin rechten gehad
# 5. Complete audit trail

# Advanced: Installatie met approval
itlc install --app=wireshark --reason="Network debugging INC-5678" --ticket=INC-5678
# → Requires approval van security team
# → Na approval: Agent installeert automatisch
```

**Scenario 5: Custom Package Installatie (Niet in Whitelist)**
```bash
# User heeft custom software nodig die niet in whitelist staat
itlc install --custom --package="./SpecializedTool-v3.2.msi" \
  --reason="Customer-specific debugging tool for Project-X" \
  --ticket=PROJ-X-456

# Agent workflow:
# 1. Upload package naar PIM controller (encrypted)
# 2. Controller scans met antivirus
# 3. MANDATORY approval van security team
# 4. Approver kan package downloaden & inspecteren
# 5. Bij approval: Agent installeert
# 6. Package + metadata bewaard voor audit (6 maanden)

# Of: Direct executable starten
itlc exec --command="C:\\Tools\\CustomScript.exe" \
  --args="--repair --database=prod" \
  --reason="Emergency database repair" \
  --ticket=INC-9999

# → ALWAYS requires approval voor custom packages/commands
# → Complete process output captured in audit log
```

### Waarom Niet Permanent Admin?

| Permanent Local Admin | Temp Admin (PIM) | Privileged Install Service | Custom Package Mode |
|-----------------------|------------------|----------------------------|---------------------|
| ✗ 24/7 attack surface | ✓ Time-boxed | ✓✓ Gebruiker NOOIT admin | ✓✓ User NOOIT admin |
| ✗ No justification | ✓ Reason required | ✓✓ Reason + approval | ✓✓✓ Reason + MANDATORY approval |
| ✗ No audit trail | ✓ Complete audit | ✓✓ Complete audit | ✓✓✓ Enhanced audit + package retention |
| ✗ Forgotten privileges | ✓ Auto-expire | ✓✓ Per-install basis | ✓✓ Single-use only |
| ✗ Can install anything | ✗ Can install anything | ✓✓ Whitelist only | ✓✓✓ Security team review |
| ✗ Compliance nightmare | ✓ Audit-ready | ✓✓ Compliance-by-design | ✓✓✓ Audit + package archival |
| ✗ Insider threat | ⚠ Reduced risk | ✓✓ Minimized (no admin) | ✓✓ Minimized + AV scan |

---

## Architectuur

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud / Datacenter                       │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         Keycloak + PIM Controller                     │ │
│  │  - Centrale approval workflow                         │ │
│  │  - Assignment database                                │ │
│  │  - Audit logging                                      │ │
│  └─────────────────────┬─────────────────────────────────┘ │
│                        │                                   │
└────────────────────────┼───────────────────────────────────┘
                         │
                         │ HTTPS (REST API)
                         │ Poll elke 30s
                         │ mTLS authenticatie
                         │
         ┌───────────────┼────────────────────┐
         │               │                    │
         ▼               ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Windows PC     │ │   Linux Laptop  │ │   macOS         │
│  john-laptop    │ │   alice-dev     │ │   bob-macbook   │
│                 │ │                 │ │                 │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │  Agent    │  │ │  │  Agent    │  │ │  │  Agent    │  │
│  │  Service  │  │ │  │  Daemon   │  │ │  │  Daemon   │  │
│  │  (SYSTEM) │  │ │  │  (root)   │  │ │  │  (root)   │  │
│  └─────┬─────┘  │ │  └─────┬─────┘  │ │  └─────┬─────┘  │
│        │        │ │        │        │ │        │        │
│   Manages       │ │   Manages       │ │   Manages       │
│        ▼        │ │        ▼        │ │        ▼        │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ Local     │  │ │  │ Local     │  │ │  │ Local     │  │
│  │ Groups:   │  │ │  │ Groups:   │  │ │  │ Groups:   │  │
│  │           │  │ │  │           │  │ │  │           │  │
│  │ Admin [+] │  │ │  │ sudo  [+] │  │ │  │ admin [+] │  │
│  │ Docker    │  │ │  │ docker    │  │ │  │ docker    │  │
│  │ Power Usr │  │ │  │ wheel     │  │ │  │ staff     │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
│                 │ │                 │ │                 │
│  User: john@... │ │  User: alice@...│ │  User: bob@...  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Agent Workflow

```
┌─────────────────────────────────────────┐
│ 1. Poll PIM Controller (elke 30s)      │
│    GET /api/v1/machines/{hostname}/     │
│        assignments                      │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ 2. Compare met current state            │
│    - Nieuwe assignments?                │
│    - Expired assignments?               │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴────────────┐
    │                      │
    ▼                      ▼
┌─────────┐          ┌──────────┐
│ ADD     │          │ REMOVE   │
│ to      │          │ from     │
│ group   │          │ group    │
└────┬────┘          └────┬─────┘
     │                    │
     ▼                    ▼
┌─────────────────────────────────────────┐
│ 3. Execute OS-specific commands         │
│    Windows: net localgroup ...          │
│    Linux:   usermod -aG ...             │
│    macOS:   dseditgroup ...             │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ 4. Audit Logging                        │
│    - Local log file                     │
│    - Windows Event Log / syslog         │
│    - Remote SIEM (optional)             │
└─────────────────────────────────────────┘

Alternative Flow: Privileged Installation
┌─────────────────────────────────────────┐
│ 1. User requests software install       │
│    itlc install --app=docker-desktop    │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ 2. PIM Controller validates             │
│    ✓ App in whitelist?                  │
│    ✓ User eligible?                     │
│    ✓ Approval required?                 │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ 3. Agent executes installation          │
│    - Download from approved source      │
│    - Verify signature/checksum          │
│    - Silent install as SYSTEM/root      │
│    - User blijft standard user          │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ 4. Complete audit log                   │
│    - Who requested                      │
│    - What was installed                 │
│    - Version + checksum                 │
│    - Installation result (success/fail) │
└─────────────────────────────────────────┘
```

### Core Features

✅ **Automatic Group Management**
- Add/remove users from local groups
- Multi-group support per role
- Rollback bij fouten

✅ **Privileged Installation Service**
- Install software ZONDER gebruiker admin te maken
- Whitelist van approved applications
- Silent installs met pre-configured parameters
- **Custom package support** (met mandatory approval)
- **Ad-hoc process execution** (voor edge cases)
- Veiliger dan tijdelijke admin rechten

✅ **Polling Architecture**
- Poll PIM controller elke 30s (configureerbaar)
- Alternatief: WebSocket voor real-time (advanced)
- Offline mode: Cache laatste state

✅ **Comprehensive Audit**
- Alle group changes gelogd
- Alle software installaties gelogd
- Local logs + remote SIEM
- Windows Event Log / Linux syslog integration

✅ **Security by Design**
- Draait als SYSTEM/root (nodig voor group mgmt + installs)
- mTLS authenticatie naar controller
- Certificate-based machine identity
- Whitelist enforcement voor software

✅ **Self-Healing**
- Detecteert manual group changes
- Herstel na reboot
- Automatic retry bij API failures

---

## Installatie

### Windows

#### Optie 1: MSI Installer (Aanbevolen)

```powershell
# Download installer
Invoke-WebRequest -Uri "https://releases.itlusions.com/pim-agent/latest/pim-agent-windows.msi" `
  -OutFile "$env:TEMP\pim-agent.msi"

# Install
msiexec /i "$env:TEMP\pim-agent.msi" `
  PIM_CONTROLLER_URL="https://pim.company.com" `
  MACHINE_CERT_PATH="C:\ProgramData\pim-agent\machine.pfx" `
  /quiet /l*v install.log

# Verify
Get-Service -Name "ITL-PIM-Agent"
```

#### Optie 2: Manual Install

```powershell
# Create directory
New-Item -ItemType Directory -Path "C:\Program Files\ITL-PIM-Agent" -Force

# Download binary
Invoke-WebRequest -Uri "https://releases.itlusions.com/pim-agent/latest/pim-agent.exe" `
  -OutFile "C:\Program Files\ITL-PIM-Agent\pim-agent.exe"

# Configuration
@"
controller_url: https://pim.company.com
poll_interval: 30
machine_cert: C:\ProgramData\pim-agent\machine.pfx
machine_cert_password_env: PIM_AGENT_CERT_PASSWORD
log_level: info
log_path: C:\ProgramData\pim-agent\logs
audit_remote: true
audit_syslog_server: syslog.company.com:514

# Role mappings
role_mappings:
  local-admin:
    - Administrators
  local-docker:
    - docker-users
  local-power-users:
    - "Power Users"
    - "Remote Desktop Users"
"@ | Out-File "C:\Program Files\ITL-PIM-Agent\config.yaml" -Encoding UTF8

# Install as service
sc.exe create "ITL-PIM-Agent" `
  binPath= "C:\Program Files\ITL-PIM-Agent\pim-agent.exe --config C:\Program Files\ITL-PIM-Agent\config.yaml" `
  start= auto `
  DisplayName= "ITL PIM Agent" `
  obj= "LocalSystem"

# Start
sc.exe start "ITL-PIM-Agent"
```

#### GPO Deployment

```powershell
# Deploy-PIMAgent.ps1 (via Group Policy Startup Script)
$ErrorActionPreference = "Stop"

# Check if already installed
if (Get-Service -Name "ITL-PIM-Agent" -ErrorAction SilentlyContinue) {
    Write-Host "Already installed"
    exit 0
}

# Download
$msiUrl = "https://releases.company.com/pim-agent/pim-agent-windows.msi"
$msiPath = "$env:TEMP\pim-agent.msi"
Invoke-WebRequest -Uri $msiUrl -OutFile $msiPath

# Request machine certificate from AD CS
$cert = Get-Certificate -Template "PIM-Agent-Machine" `
  -CertStoreLocation Cert:\LocalMachine\My -Url ldap:

# Install
msiexec /i $msiPath `
  PIM_CONTROLLER_URL="https://pim.company.com" `
  MACHINE_CERT_THUMBPRINT=$cert.Certificate.Thumbprint `
  /quiet /l*v "$env:TEMP\pim-agent-install.log"

# Verify
Start-Service -Name "ITL-PIM-Agent"
```

---

### Linux

#### Optie 1: Automated Script

```bash
# Download and run installer
curl -fsSL https://releases.itlusions.com/pim-agent/install-linux.sh | sudo bash
```

#### Optie 2: Manual Install

```bash
# Download binary
sudo curl -o /usr/local/bin/pim-agent \
  https://releases.itlusions.com/pim-agent/latest/pim-agent-linux-amd64
sudo chmod +x /usr/local/bin/pim-agent

# Configuration
sudo mkdir -p /etc/pim-agent
sudo tee /etc/pim-agent/config.yaml > /dev/null <<EOF
controller_url: https://pim.company.com
poll_interval: 30
machine_cert: /etc/pim-agent/machine.crt
machine_key: /etc/pim-agent/machine.key
log_level: info
log_path: /var/log/pim-agent
audit_remote: true
audit_syslog_server: syslog.company.com:514

role_mappings:
  local-admin:
    - sudo
    - wheel  # RHEL/CentOS
  local-docker:
    - docker
  local-dev:
    - docker
    - libvirt
    - wireshark
EOF

# Systemd service
sudo tee /etc/systemd/system/pim-agent.service > /dev/null <<EOF
[Unit]
Description=ITL PIM Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/pim-agent --config /etc/pim-agent/config.yaml
Restart=always
RestartSec=10
User=root
Group=root

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/pim-agent

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable pim-agent
sudo systemctl start pim-agent

# Verify
sudo systemctl status pim-agent
```

#### Ansible Playbook

```yaml
# playbook-pim-agent.yml
---
- name: Install PIM Agent
  hosts: workstations
  become: yes
  tasks:
    - name: Download agent
      get_url:
        url: https://releases.itlusions.com/pim-agent/latest/pim-agent-linux-amd64
        dest: /usr/local/bin/pim-agent
        mode: '0755'
    
    - name: Create config directory
      file:
        path: /etc/pim-agent
        state: directory
    
    - name: Deploy config
      template:
        src: config.yaml.j2
        dest: /etc/pim-agent/config.yaml
    
    - name: Install systemd service
      template:
        src: pim-agent.service.j2
        dest: /etc/systemd/system/pim-agent.service
      notify: restart pim-agent
    
    - name: Enable service
      systemd:
        name: pim-agent
        enabled: yes
        daemon_reload: yes
  
  handlers:
    - name: restart pim-agent
      systemd:
        name: pim-agent
        state: restarted
```

---

### macOS

```bash
# Download agent
curl -o /usr/local/bin/pim-agent \
  https://releases.itlusions.com/pim-agent/latest/pim-agent-darwin-amd64
chmod +x /usr/local/bin/pim-agent

# Configuration
sudo mkdir -p /etc/pim-agent
sudo tee /etc/pim-agent/config.yaml > /dev/null <<EOF
controller_url: https://pim.company.com
poll_interval: 30
machine_cert: /etc/pim-agent/machine.crt
machine_key: /etc/pim-agent/machine.key
log_level: info
log_path: /var/log/pim-agent

role_mappings:
  local-admin:
    - admin
  local-docker:
    - docker
EOF

# LaunchDaemon
sudo tee /Library/LaunchDaemons/com.itlusions.pim-agent.plist > /dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.itlusions.pim-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/pim-agent</string>
        <string>--config</string>
        <string>/etc/pim-agent/config.yaml</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/pim-agent/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/pim-agent/stderr.log</string>
</dict>
</plist>
EOF

# Load and start
sudo launchctl load /Library/LaunchDaemons/com.itlusions.pim-agent.plist
sudo launchctl start com.itlusions.pim-agent
```

---

## Configuratie

### config.yaml Reference

```yaml
# PIM Controller URL (verplicht)
controller_url: https://pim.company.com

# Poll interval in seconden (default: 30)
poll_interval: 30

# Machine authentication
machine_cert: /etc/pim-agent/machine.crt  # Of .pfx op Windows
machine_key: /etc/pim-agent/machine.key   # Niet nodig bij .pfx
machine_cert_password_env: PIM_AGENT_CERT_PASSWORD  # Voor encrypted certs

# Logging
log_level: info  # debug, info, warn, error
log_path: /var/log/pim-agent

# Remote audit logging (optional)
audit_remote: true
audit_syslog_server: syslog.company.com:514

# Role naar lokale groep mapping
role_mappings:
  # Keycloak role name → Local OS groups
  local-admin:
    - Administrators  # Windows
    - sudo            # Linux
    - admin           # macOS
  
  local-docker:
    - docker-users    # Windows
    - docker          # Linux/macOS
  
  local-power-users:
    - "Power Users"           # Windows
    - "Remote Desktop Users"  # Windows
    - staff                   # macOS
  
  local-dev-tools:
    - wireshark
    - libvirt
    - kvm

# Privileged Installation Service
installation_service:
  enabled: true
  
  # Permission model (least privilege)
  permissions:
    # Level 1: Managed application installation (whitelist only)
    managed_install:
      display_name: "Managed Application Installation"
      description: "Install pre-approved applications from whitelist"
      eligible_groups: [developers, qa-engineers, support-staff]
      approval_required: false  # Self-service voor whitelisted apps
      risk_level: low
    
    # Level 2: Managed process execution (whitelist only)
    managed_exec:
      display_name: "Managed Process Execution"
      description: "Execute pre-approved processes/scripts"
      eligible_groups: [sre-team, devops, database-admins]
      approval_required: false  # Self-service voor approved commands
      risk_level: medium
    
    # Level 3: Unmanaged package installation (DANGEROUS)
    unmanaged_install:
      display_name: "Custom Package Installation"
      description: "Install packages not in whitelist (REQUIRES SECURITY REVIEW)"
      eligible_groups: [sre-team, security-engineers]
      approval_required: true  # ALWAYS
      approver_groups: [security-team, infra-leads]
      min_approvers: 1
      require_ticket: true
      require_security_scan: true
      risk_level: high
    
    # Level 4: Unmanaged process execution (MOST DANGEROUS)
    unmanaged_exec:
      display_name: "Ad-hoc Process Execution"
      description: "Execute arbitrary commands (HIGHEST RISK)"
      eligible_groups: [sre-leads, security-incident-responders]
      approval_required: true  # ALWAYS
      approver_groups: [security-team, c-level]
      min_approvers: 2  # Requires 2 approvals!
      require_ticket: true
      require_justification: true
      mfa_revalidation: true  # Force fresh MFA
      risk_level: critical
  
  # Approved applications whitelist (managed_install permission)
    # Self-service (no approval)
    docker-desktop:
      display_name: "Docker Desktop"
      permission_required: managed_install  # Level 1
      eligible_groups: [developers, devops]
      approval_required: false
      windows:
        installer_url: "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        installer_hash: "sha256:abc123..."
        install_command: "Docker Desktop Installer.exe install --quiet --accept-license"
      linux:
        install_command: "apt-get install -y docker-ce docker-ce-cli containerd.io"
      macos:
        installer_url: "https://desktop.docker.com/mac/main/amd64/Docker.dmg"
        install_command: "hdiutil attach Docker.dmg && cp -R /Volumes/Docker/Docker.app /Applications/"
    
    vscode:
      display_name: "Visual Studio Code"
      eligible_groups: [developers, employees]
      approval_required: false
      windows:
        installer_url: "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"
        install_command: "VSCodeUserSetup.exe /VERYSILENT /MERGETASKS=!runcode"
      linux:
        install_command: "snap install code --classic"
      macos:
        installer_url: "https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal"
        install_command: "unzip VSCode.zip -d /Applications/"
    
    # Requires approval (security sensitive tool)
    wireshark:
      display_name: "Wireshark"
      permission_required: managed_install  # Level 1 (maar met approval)
      eligible_groups: [sre-team, network-engineers]
      approval_required: true  # Security sensitive
      approver_groups: [security-team]
      windows:
        installer_url: "https://1.na.dl.wireshark.org/win64/Wireshark-win64-latest.exe"
        install_command: "Wireshark-win64-latest.exe /S"
      linux:
        install_command: "apt-get install -y wireshark"
    
    postman:
      display_name: "Postman"
      eligible_groups: [developers, qa-engineers]
      approval_required: false
      windows:
        installer_url: "https://dl.pstmn.io/download/latest/win64"
        install_command: "Postman-win64-Setup.exe -s"
    
    # Custom internal app
    company-vpn:
      display_name: "Company VPN Client"
      eligible_groups: [employees]
      approval_required: false
      windows:
        installer_url: "https://internal-repo.company.com/vpn-client-v2.1.msi"
        installer_hash: "sha256:def456..."
        install_command: "msiexec /i vpn-client-v2.1.msi /quiet /norestart"
      linux:
        installer_url: "https://internal-repo.company.com/vpn-client_2.1_amd64.deb"
        install_command: "dpkg -i vpn-client_2.1_amd64.deb"
  
  # Installation policies
  policies:
    max_concurrent_installs: 1  # Per machine
    download_timeout: 600  # 10 minutes
    install_timeout: 1800  # 30 minutes
    verify_signatures: true
    allow_downgrades: false
    
  # Custom package support (niet in whitelist)
  # Requires: unmanaged_install permission (Level 3)
  custom_packages:
    enabled: true
    permission_required: unmanaged_install  # Level 3
    require_approval: true  # ALWAYS true (security)
    require_security_team_approval: true
    max_package_size_mb: 500
    
    # Antivirus scanning
    antivirus_scan:
      enabled: true
      providers:
        - windows_defender  # Windows
        - clamav           # Linux/macOS
      timeout: 300  # 5 minutes
    
    # Package retention (voor audit)
    retention:
      duration_days: 180  # 6 maanden
      storage_location: "s3://company-pim-packages/"  # Of local path
    
    # Allowed file types
    allowed_extensions:
      - .msi
      - .exe
      - .deb
      - .rpm
      - .pkg  # macOS
      - .dmg  # macOS
    
    # Forbidden patterns (extra security)
    forbidden_patterns:
      - "*.vbs"  # VBScript
      - "*.ps1"  # PowerShell (use exec instead)
      - "*.bat"  # Batch files
      - "*.cmd"  # Command files
  
  # Ad-hoc process execution
  # Managed: whitelist-based (Level 2: managed_exec)
  # Unmanaged: arbitrary commands (Level 4: unmanaged_exec)
  process_execution:
    enabled: true
    
    # Managed process whitelist (Level 2: managed_exec, self-service)
    approved_commands:
      database_backup:
        command: "/usr/local/bin/backup-db.sh"
        allowed_args: ["--database=*", "--output=*"]
        permission_required: managed_exec
        approval_required: false
        eligible_groups: [database-admins, sre-team]
      
      log_analysis:
        command: "C:\\Program Files\\LogAnalyzer\\analyze.exe"
        allowed_args: ["--file=*", "--output=*"]
        permission_required: managed_exec
        approval_required: false
        eligible_groups: [sre-team, support-staff]
      
      cache_clear:
        command: "/opt/company/scripts/clear-cache.sh"
        allowed_args: ["--service=*", "--force"]
        permission_required: managed_exec
        approval_required: false
        eligible_groups: [sre-team, devops]
    
    # Unmanaged execution (Level 4: unmanaged_exec, REQUIRES 2 APPROVALS)
    unmanaged:
      permission_required: unmanaged_exec  # Level 4 (highest)
      require_approval: true  # ALWAYS true
      min_approvers: 2  # TWO approvals required!
      
      # Allowed directories (whitelist)
      allowed_paths:
        - "C:\\Program Files\\"
        - "C:\\Program Files (x86)\\"
        - "/usr/bin/"
        - "/usr/local/bin/"
        - "/opt/"
    
    # Timeout
    max_execution_time: 3600  # 1 hour
    
    # Capture output
    capture_output: true
    max_output_size_mb: 10
    
  # Installation cache
  cache:
    enabled: true
    path: /var/cache/pim-agent/installers  # Linux/macOS
    # C:\ProgramData\pim-agent\cache  # Windows
    max_size_gb: 10
    retention_days: 30

# Failsafe mode (optional)
# Bij controller outage: behoud huidige group memberships
failsafe_mode: true

# Emergency local admin (bypass PIM)
emergency_local_admin: emergency-admin

# WebSocket mode (advanced, default: false)
use_websocket: false
websocket_url: wss://pim.company.com/ws

# Self-healing (detect manual group changes)
self_healing: true
healing_interval: 300  # Check every 5 minutes

# Prometheus metrics (optional)
metrics_enabled: true
metrics_port: 9090
```

---

## Agent Implementatie

Zie de volledige Python implementatie in [LOCAL_PRIVILEGE_AGENT.md](LOCAL_PRIVILEGE_AGENT.md), sectie "Agent Implementatie".

### Core Components

**1. Assignment Fetcher**
```python
def fetch_assignments(self):
    """Poll PIM controller voor active assignments"""
    response = requests.get(
        f"{self.config['controller_url']}/api/v1/machines/{self.hostname}/assignments",
        cert=(self.config['machine_cert'], self.config['machine_key']),
        timeout=10
    )
    return response.json() if response.status_code == 200 else []
```

**2. Group Manager (OS-specific)**
```python
def add_user_to_groups_windows(self, username, groups):
    """Windows: net localgroup"""
    for group in groups:
        cmd = f'net localgroup "{group}" "{username}" /add'
        subprocess.run(cmd, shell=True)

def add_user_to_groups_unix(self, username, groups):
    """Linux/macOS: usermod/dseditgroup"""
    for group in groups:
        if self.os_type == 'darwin':
            cmd = ['dseditgroup', '-o', 'edit', '-a', username, '-t', 'user', group]
        else:
            cmd = ['usermod', '-aG', group, username]
        subprocess.run(cmd)
```

**3. State Synchronizer**
```python
def sync_assignments(self, assignments):
    """Reconcile desired state met actual state"""
    target_state = {}  # username → set(groups)
    
    for assignment in assignments:
        username = assignment['username']
        role_name = assignment['role_name']
        groups = self.config['role_mappings'].get(role_name, [])
        target_state[username] = target_state.get(username, set()) | set(groups)
    
    # Add new memberships
    for username, groups in target_state.items():
        new_groups = groups - self.current_state.get(username, set())
        if new_groups:
            self.add_user_to_groups(username, list(new_groups))
    
    # Remove expired memberships
    for username, groups in self.current_state.items():
        removed_groups = groups - target_state.get(username, set())
        if removed_groups:
            self.remove_user_from_groups(username, list(removed_groups))
    
    self.current_state = target_state
```

**4. Installation Manager**
```python
def install_application(self, app_name, username, reason, ticket=None):
    """Execute privileged installation as SYSTEM/root"""
    
    # Validate app in whitelist
    app_config = self.config['installation_service']['approved_apps'].get(app_name)
    if not app_config:
        raise ValueError(f"Application {app_name} not in whitelist")
    
    # Check user has required permission
    required_permission = app_config.get('permission_required', 'managed_install')
    if not self.user_has_permission(username, required_permission):
        raise PermissionError(f"User lacks '{required_permission}' permission for {app_name}")
    
    # Download installer (met caching)
    installer_path = self.download_installer(app_config)
    
    # Verify signature/checksum
    if not self.verify_installer(installer_path, app_config.get('installer_hash')):
        raise SecurityError("Installer verification failed")
    
    # Execute installation
    self.logger.info(f"Installing {app_name} for user {username}")
    
    install_cmd = app_config[self.os_type]['install_command']
    install_cmd = install_cmd.replace('${INSTALLER}', installer_path)
    
    result = subprocess.run(
        install_cmd,
        shell=True,
        capture_output=True,
        timeout=self.config['installation_service']['policies']['install_timeout']
    )
    
    # Audit log
    self.audit_log_installation(
        action='software_install',
        username=username,
        app_name=app_name,
        app_version=app_config.get('version'),
        success=result.returncode == 0,
        reason=reason,
        ticket=ticket
    )
    
    return result.returncode == 0

def download_installer(self, app_config):
    """Download installer met caching"""
    cache_dir = self.config['installation_service']['cache']['path']
    installer_url = app_config[self.os_type]['installer_url']
    
    # Check cache
    cache_path = os.path.join(cache_dir, os.path.basename(installer_url))
    if os.path.exists(cache_path):
        self.logger.info(f"Using cached installer: {cache_path}")
        return cache_path
    
    # Download
    self.logger.info(f"Downloading installer from {installer_url}")
    response = requests.get(installer_url, stream=True, timeout=600)
    
    with open(cache_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return cache_path

def verify_installer(self, installer_path, expected_hash):
    """Verify installer checksum"""
    if not expected_hash:
        return True  # No verification required
    
    algo, expected = expected_hash.split(':', 1)
    
    import hashlib
    hasher = hashlib.new(algo)
    with open(installer_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    
    actual = hasher.hexdigest()
    
    if actual != expected:
        self.logger.error(f"Hash mismatch: expected {expected}, got {actual}")
        return False
    
    return True

def install_custom_package(self, package_path, username, reason, ticket):
    """Install custom package (niet in whitelist) - REQUIRES unmanaged_install permission"""
    
    # Check permission (Level 3: unmanaged_install)
    if not self.user_has_permission(username, 'unmanaged_install'):
        raise PermissionError(
            "User lacks 'unmanaged_install' permission. "
            "Custom package installation requires security clearance."
        )
    
    # Validate file extension
    allowed_exts = self.config['installation_service']['custom_packages']['allowed_extensions']
    if not any(package_path.endswith(ext) for ext in allowed_exts):
        raise ValueError(f"File type not allowed. Allowed: {allowed_exts}")
    
    # Check file size
    max_size = self.config['installation_service']['custom_packages']['max_package_size_mb'] * 1024 * 1024
    if os.path.getsize(package_path) > max_size:
        raise ValueError(f"Package exceeds maximum size of {max_size / 1024 / 1024}MB")
    
    # Calculate checksum
    package_hash = self.calculate_sha256(package_path)
    
    # Upload to PIM controller (encrypted)
    self.logger.info(f"Uploading custom package: {package_path}")
    
    with open(package_path, 'rb') as f:
        response = requests.post(
            f"{self.config['controller_url']}/api/v1/custom-packages/upload",
            files={'package': f},
            data={
                'username': username,
                'reason': reason,
                'ticket': ticket,
                'package_hash': package_hash,
                'package_name': os.path.basename(package_path)
            },
            cert=(self.config['machine_cert'], self.config['machine_key']),
            timeout=600
        )
    
    if response.status_code == 202:
        request_id = response.json()['request_id']
        self.logger.info(f"Custom package upload successful. Request ID: {request_id}")
        self.logger.info("Waiting for security team approval...")
        
        # Poll voor approval
        return self.wait_for_approval(request_id, poll_interval=60, timeout=86400)  # 24h
    else:
        raise Exception(f"Upload failed: {response.text}")

def execute_process(self, command, args, username, reason, ticket, command_alias=None):
    """Execute process met elevated privileges"""
    
    # Check if this is a managed (whitelisted) command
    approved_commands = self.config['installation_service']['process_execution'].get('approved_commands', {})
    
    if command_alias and command_alias in approved_commands:
        # Managed execution (Level 2: managed_exec)
        cmd_config = approved_commands[command_alias]
        required_permission = 'managed_exec'
        
        # Validate user has permission
        if not self.user_has_permission(username, required_permission):
            raise PermissionError(f"User lacks '{required_permission}' permission")
        
        # Use pre-defined command
        command = cmd_config['command']
        
        # Validate args against allowed patterns
        self.validate_command_args(args, cmd_config.get('allowed_args', []))
        
        # Check if approval needed (some managed commands may still require it)
        if cmd_config.get('approval_required', False):
            approved = self.request_and_wait_approval(
                username, 'managed_process', command, args, reason, ticket
            )
            if not approved:
                raise Exception("Process execution denied")
    else:
        # Unmanaged execution (Level 4: unmanaged_exec) - MOST DANGEROUS
        required_permission = 'unmanaged_exec'
        
        # Check user has highest permission level
        if not self.user_has_permission(username, required_permission):
            raise PermissionError(
                f"User lacks '{required_permission}' permission. "
                f"Ad-hoc process execution requires highest security clearance."
            )
        
        # Validate command path
        unmanaged_config = self.config['installation_service']['process_execution']['unmanaged']
        allowed_paths = unmanaged_config['allowed_paths']
        if not any(command.startswith(path) for path in allowed_paths):
            raise ValueError(f"Command path not in allowed directories: {allowed_paths}")
    
    # Check if file exists en is executable
    if not os.path.isfile(command):
        raise ValueError(f"Command not found: {command}")
    
    # Request approval
    response = requests.post(
        f"{self.config['controller_url']}/api/v1/process-execution/request",
        json={
            'username': username,
            'command': command,
            'args': args,
            'reason': reason,
            'ticket': ticket,
            'hostname': self.hostname
        },
        cert=(self.config['machine_cert'], self.config['machine_key'])
    )
    
    if response.status_code != 202:
        raise Exception(f"Request failed: {response.text}")
    
    request_id = response.json()['request_id']
    self.logger.info(f"Process execution request submitted. Request ID: {request_id}")
    
    # Wait for approval
    approved = self.wait_for_approval(request_id)
    
    if not approved:
        raise Exception("Process execution denied")
    
    # Execute
    self.logger.info(f"Executing: {command} {args}")
    
    full_command = [command] + args.split()
    
    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            timeout=self.config['installation_service']['process_execution']['max_execution_time'],
            text=True
        )
        
        # Audit log met output
        self.audit_log(
            action='process_execution',
            username=username,
            command=command,
            args=args,
            exit_code=result.returncode,
            stdout=result.stdout[:10000],  # Max 10KB
            stderr=result.stderr[:10000],
            reason=reason,
            ticket=ticket,
            request_id=request_id
        )
        
        return result
        
    except subprocess.TimeoutExpired:
        self.logger.error(f"Process execution timeout: {command}")
        raise

def user_has_permission(self, username, permission_name):
    """Check if user has required permission based on Keycloak groups"""
    
    # Get user's Keycloak groups
    user_groups = self.get_user_keycloak_groups(username)
    
    # Get permission config
    permissions_config = self.config['installation_service']['permissions']
    permission = permissions_config.get(permission_name)
    
    if not permission:
        self.logger.error(f"Unknown permission: {permission_name}")
        return False
    
    # Check if user is in any eligible group
    eligible_groups = permission.get('eligible_groups', [])
    has_permission = any(group in user_groups for group in eligible_groups)
    
    if not has_permission:
        self.logger.warning(
            f"User {username} lacks permission '{permission_name}'. "
            f"User groups: {user_groups}, Required: {eligible_groups}"
        )
    
    return has_permission

def get_user_keycloak_groups(self, username):
    """Fetch user's Keycloak groups from PIM controller"""
    try:
        response = requests.get(
            f"{self.config['controller_url']}/api/v1/users/{username}/groups",
            cert=(self.config['machine_cert'], self.config['machine_key']),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['groups']
        else:
            self.logger.error(f"Failed to fetch user groups: {response.text}")
            return []
    except Exception as e:
        self.logger.error(f"Error fetching user groups: {e}")
        return []

def validate_command_args(self, args, allowed_patterns):
    """Validate command arguments against allowed patterns"""
    # Simple wildcard matching for now
    # allowed_patterns: ["--database=*", "--output=*", "--force"]
    
    args_list = args.split()
    
    for arg in args_list:
        # Check if arg matches any allowed pattern
        matches = False
        for pattern in allowed_patterns:
            if pattern == arg:  # Exact match
                matches = True
                break
            elif pattern.endswith('=*'):  # Wildcard match (--database=*)
                prefix = pattern[:-1]  # Remove *
                if arg.startswith(prefix):
                    matches = True
                    break
        
        if not matches:
            raise ValueError(f"Argument '{arg}' not allowed. Allowed patterns: {allowed_patterns}")
    
    return True

def calculate_sha256(self, file_path):
    """Calculate SHA256 hash of file"""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def wait_for_approval(self, request_id, poll_interval=60, timeout=86400):
    """Poll PIM controller voor approval status"""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"{self.config['controller_url']}/api/v1/requests/{request_id}/status",
            cert=(self.config['machine_cert'], self.config['machine_key'])
        )
        
        if response.status_code == 200:
            status = response.json()['status']
            
            if status == 'approved':
                return True
            elif status == 'denied':
                return False
            elif status == 'pending':
                time.sleep(poll_interval)
            else:
                raise Exception(f"Unknown status: {status}")
        else:
            self.logger.error(f"Failed to check approval status: {response.text}")
            time.sleep(poll_interval)
    
    raise TimeoutError("Approval timeout")
```

**5. Audit Logger**
```python
def audit_log(self, action, username, group=None, assignment_id=None, **kwargs):
    """Log naar local + remote"""
    entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'hostname': self.hostname,
        'action': action,  # group_add, group_remove, software_install
        'username': username,
        'group': group,
        'assignment_id': assignment_id,
        **kwargs  # Extra fields voor software installs
    }
    
    # Local log
    if action == 'software_install':
        self.logger.info(f"AUDIT: {action} - {username} installed {kwargs.get('app_name')}")
    else:
        self.logger.info(f"AUDIT: {action} - {username} → {group}")
    
    # Remote syslog (optional)
    if self.config.get('audit_remote'):
        self.send_to_syslog(entry)

def audit_log_installation(self, action, username, app_name, app_version, success, reason, ticket=None):
    """Specialized audit voor software installaties"""
    self.audit_log(
        action=action,
        username=username,
        app_name=app_name,
        app_version=app_version,
        success=success,
        reason=reason,
        ticket=ticket,
        installer_hash=self.last_installer_hash
    )
```

---

## Machine Enrollment

Machines hebben een certificaat nodig voor mTLS authenticatie.

### Optie 1: Ansible Enrollment

```yaml
# playbook-enroll-machines.yml
---
- name: Enroll machines with PIM Agent
  hosts: workstations
  become: yes
  tasks:
    - name: Generate private key
      openssl_privatekey:
        path: /etc/pim-agent/machine.key
        size: 2048
        mode: '0600'
    
    - name: Generate CSR
      openssl_csr:
        path: /etc/pim-agent/machine.csr
        privatekey_path: /etc/pim-agent/machine.key
        common_name: "{{ inventory_hostname }}"
        organization_name: "{{ company_name }}"
    
    - name: Submit to internal CA (HashiCorp Vault)
      shell: |
        vault write -format=json pki/issue/pim-agent \
          common_name="{{ inventory_hostname }}" \
          ttl=8760h | jq -r '.data.certificate' > /etc/pim-agent/machine.crt
      environment:
        VAULT_ADDR: "{{ vault_url }}"
        VAULT_TOKEN: "{{ vault_token }}"
```

### Optie 2: Windows AD CS

```powershell
# Request-PIMCertificate.ps1
$certRequest = Get-Certificate `
  -Template "PIM-Agent-Machine" `
  -CertStoreLocation Cert:\LocalMachine\My `
  -Url ldap: `
  -SubjectName "CN=$env:COMPUTERNAME"

# Export naar PFX
$pfxPassword = ConvertTo-SecureString -String "SecurePassword" -Force -AsPlainText
Export-PfxCertificate `
  -Cert $certRequest.Certificate `
  -FilePath "C:\ProgramData\pim-agent\machine.pfx" `
  -Password $pfxPassword
```

### Optie 3: Let's Encrypt (voor internet-facing machines)

```bash
# Generate cert met certbot
sudo certbot certonly --standalone \
  -d $(hostname -f) \
  --agree-tos \
  --email admin@company.com

# Copy naar agent dir
sudo cp /etc/letsencrypt/live/$(hostname -f)/fullchain.pem /etc/pim-agent/machine.crt
sudo cp /etc/letsencrypt/live/$(hostname -f)/privkey.pem /etc/pim-agent/machine.key
sudo chmod 600 /etc/pim-agent/machine.key
```

---

## Monitoring & Troubleshooting

### Check Agent Status

**Windows:**
```powershell
# Service status
Get-Service -Name "ITL-PIM-Agent"
sc.exe query "ITL-PIM-Agent"

# Logs
Get-Content "C:\ProgramData\pim-agent\logs\pim-agent.log" -Tail 50 -Wait

# Recent audit events
Get-EventLog -LogName Application -Source "ITL-PIM-Agent" -Newest 20 | Format-List

# Test connectivity
Test-NetConnection -ComputerName pim.company.com -Port 443
```

**Linux:**
```bash
# Service status
systemctl status pim-agent
systemctl is-active pim-agent

# Logs
journalctl -u pim-agent -f
tail -f /var/log/pim-agent/pim-agent.log

# Recent audit events
grep AUDIT /var/log/pim-agent/pim-agent.log | tail -20

# Test connectivity
curl -v --cert /etc/pim-agent/machine.crt \
     --key /etc/pim-agent/machine.key \
     https://pim.company.com/api/v1/health
```

**macOS:**
```bash
# Service status
sudo launchctl list | grep pim-agent

# Logs
tail -f /var/log/pim-agent/stdout.log
tail -f /var/log/pim-agent/stderr.log

# Test connectivity
curl -v --cert /etc/pim-agent/machine.crt \
     --key /etc/pim-agent/machine.key \
     https://pim.company.com/api/v1/health
```

### Common Issues

**1. Agent kan PIM controller niet bereiken**

```bash
# Check DNS
nslookup pim.company.com

# Check firewall
telnet pim.company.com 443

# Check certificate
openssl s_client -connect pim.company.com:443 \
  -cert /etc/pim-agent/machine.crt \
  -key /etc/pim-agent/machine.key

# Verify cert not expired
openssl x509 -in /etc/pim-agent/machine.crt -noout -enddate
```

**2. User wordt niet toegevoegd aan groep**

```bash
# Linux: Check if group exists
getent group docker

# Linux: Check user
id username

# Windows: Check group
net localgroup Administrators

# Windows: Check user in group
net localgroup Administrators | findstr username

# Check agent permissions (MOET root/SYSTEM zijn)
ps aux | grep pim-agent  # Linux
sc.exe qc "ITL-PIM-Agent"  # Windows
```

**3. Elevation werkt niet na approval**

```bash
# Force immediate poll (restart agent)
sudo systemctl restart pim-agent  # Linux
Restart-Service "ITL-PIM-Agent"   # Windows

# Check logs voor errors
journalctl -u pim-agent --since "5 minutes ago"
Get-Content "C:\ProgramData\pim-agent\logs\pim-agent.log" -Tail 50

# Manually test group add
# Linux:
sudo usermod -aG sudo testuser
# Windows:
net localgroup Administrators testuser /add
```

**4. Agent crasht bij startup**

```bash
# Check config syntax
python -c "import yaml; yaml.safe_load(open('/etc/pim-agent/config.yaml'))"

# Check permissions
ls -la /etc/pim-agent/
# Should be: -rw------- (600) for cert/key

# Check dependencies
ldd /usr/local/bin/pim-agent  # Linux
```

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'pim-agent'
    static_configs:
      - targets: ['*:9090']  # If metrics_enabled: true
```

**Available metrics:**
```
pim_agent_assignments_active - Current active elevations
pim_agent_group_add_total - Counter of group additions
pim_agent_group_remove_total - Counter of group removals
pim_agent_errors_total - Counter of errors
pim_agent_controller_latency_seconds - API call latency
pim_agent_last_sync_timestamp - Last successful sync
pim_agent_state_drift_detected - Manual group changes detected
```

---

## Security

### 1. Permission Model (Least Privilege)

**Four levels van privileges:**

| Level | Permission | Risk | Approval | Use Case |
|-------|-----------|------|----------|----------|
| **1** | `managed_install` | 🟢 Low | Self-service | Whitelist apps (Docker, VS Code) |
| **2** | `managed_exec` | 🟡 Medium | Self-service | Whitelist commands (backups, scripts) |
| **3** | `unmanaged_install` | 🟠 High | 1 approver | Custom packages (not in whitelist) |
| **4** | `unmanaged_exec` | 🔴 Critical | 2 approvers | Ad-hoc commands (highest risk) |

**Permission Inheritance:**
- Level 4 (unmanaged_exec) includes ALL lower levels
- Level 3 (unmanaged_install) includes Level 1 & 2
- Level 2 (managed_exec) includes Level 1
- Level 1 (managed_install) is base level

**Assignment Strategy:**
```yaml
# Conservative approach:
groups:
  developers: [managed_install]  # Level 1 only
  devops: [managed_install, managed_exec]  # Level 1+2
  sre-team: [managed_install, managed_exec, unmanaged_install]  # Level 1+2+3
  sre-leads: [managed_install, managed_exec, unmanaged_install, unmanaged_exec]  # ALL
  security-incident-responders: [unmanaged_exec]  # Level 4 (emergency)
```

**Why Strict Separation?**
- `unmanaged_install`: User kan malware uploaden (maar security team reviewed)
- `unmanaged_exec`: User kan ARBITRARY commands uitvoeren (2 approvals required!)
- Level 4 = root shell equivalent → Requires 2 senior approvals

### 2. Agent Runs as Privileged User

**Why:** Group management requires admin/root privileges

**Mitigation:**
- Minimal code surface (single-purpose agent)
- Permission-based access control (4 levels)
- Input validation (username/group whitelisting)
- Certificate-based authentication
- Read-only access to controller (no write)
- Systemd security hardening (Linux):
  ```ini
  [Service]
  NoNewPrivileges=true
  PrivateTmp=true
  ProtectSystem=strict
  ProtectHome=true
  ```

### 2. Certificate Security

**Best practices:**
- Certificates rotated annually
- Private keys never leave machine (not in backup)
- Strong encryption (2048-bit RSA minimum)
- Certificate pinning in agent config (optional)

```yaml
# Certificate pinning
controller_cert_fingerprint: "SHA256:abc123..."
verify_mode: strict  # Fail if fingerprint mismatch
```

### 3. Input Validation

```python
# Whitelist allowed groups
ALLOWED_GROUPS = {
    'windows': ['Administrators', 'docker-users', 'Power Users'],
    'linux': ['sudo', 'wheel', 'docker', 'libvirt'],
    'macos': ['admin', 'docker', 'staff']
}

def validate_group(group_name):
    """Prevent injection attacks"""
    allowed = ALLOWED_GROUPS.get(platform.system().lower(), [])
    if group_name not in allowed:
        raise ValueError(f"Group {group_name} not in whitelist")

# Whitelist voor software installaties
def validate_application(app_name):
    """Only install whitelisted applications"""
    approved_apps = config['installation_service']['approved_apps']
    if app_name not in approved_apps:
        raise ValueError(f"Application {app_name} not in approved list")
    
    # Check user eligibility
    user_groups = get_user_keycloak_groups(username)
    eligible_groups = approved_apps[app_name]['eligible_groups']
    
    if not any(g in user_groups for g in eligible_groups):
        raise PermissionError(f"User not eligible to install {app_name}")
    
    return approved_apps[app_name]

# Extra validatie voor custom packages
def validate_custom_package(package_path):
    """Strict validation voor custom packages"""
    
    # File extension whitelist
    allowed_exts = config['installation_service']['custom_packages']['allowed_extensions']
    if not any(package_path.endswith(ext) for ext in allowed_exts):
        raise ValueError(f"File type not allowed")
    
    # Size limit
    max_size = config['installation_service']['custom_packages']['max_package_size_mb'] * 1024 * 1024
    if os.path.getsize(package_path) > max_size:
        raise ValueError(f"Package too large")
    
    # Forbidden patterns (extra security)
    forbidden = config['installation_service']['custom_packages']['forbidden_patterns']
    for pattern in forbidden:
        if fnmatch.fnmatch(package_path, pattern):
            raise SecurityError(f"Forbidden file type: {pattern}")
    
    # Antivirus scan (MANDATORY)
    if not scan_with_antivirus(package_path):
        raise SecurityError("Antivirus scan failed or detected threats")
    
    return True

def validate_process_execution(command, args):
    """Strict validation voor ad-hoc execution"""
    
    # Path whitelist
    allowed_paths = config['installation_service']['process_execution']['allowed_paths']
    if not any(command.startswith(path) for path in allowed_paths):
        raise ValueError(f"Command not in allowed directories")
    
    # Executable must exist
    if not os.path.isfile(command):
        raise ValueError(f"Command not found: {command}")
    
    # Check for shell injection patterns
    dangerous_chars = ['|', '&', ';', '>', '<', '`', '$', '(', ')']
    for char in dangerous_chars:
        if char in args:
            raise SecurityError(f"Potentially dangerous character in arguments: {char}")
    
    return True
```

### 4. Audit Requirements

**Moet gelogd worden:**

**Voor group elevations:**
- Timestamp (UTC)
- Username
- Group name
- Action (add/remove)
- Assignment ID (traceability)
- Machine hostname/IP
- Agent version
- Initiator (who requested elevation)
- Reason + ticket reference

**Voor software installaties:**
- Timestamp (UTC)
- Username (who requested)
- Application name + version
- Installer source URL
- Installer checksum (verification)
- Installation command executed
- Success/failure status
- Installation duration
- Approver (if approval required)
- Reason + ticket reference
- Machine hostname/IP

**Voor custom packages (extra velden):**
- Package filename + size
- SHA256 checksum
- File type / magic number
- Antivirus scan results (provider + timestamp)
- Digital signature info (if present)
- Approver username + timestamp
- Package retention location (S3/storage)
- Time from request to approval
- Installation output/errors

**Voor process execution:**
- Timestamp (UTC)
- Username (who requested)
- Command + full arguments
- Process working directory
- Exit code
- Stdout (first 10KB)
- Stderr (first 10KB)
- Execution duration
- Approver username + timestamp
- Reason + ticket reference
- Machine hostname/IP

**Log destinations:**
- Local log file (forensics)
- Windows Event Log / Linux syslog
- Remote SIEM (Splunk, ELK, etc.)
- S3/blob storage (long-term retention)

### 5. Rollback Strategy

```python
def add_user_to_groups_with_rollback(self, username, groups):
    """Add with automatic rollback on failure"""
    added_groups = []
    
    try:
        for group in groups:
            self.add_user_to_group(username, group)
            added_groups.append(group)
    except Exception as e:
        # Rollback: remove from groups we already added
        self.logger.error(f"Failed, rolling back: {e}")
        for group in added_groups:
            try:
                self.remove_user_from_group(username, group)
            except:
                pass  # Best effort
        raise
```

---

## Production Deployment

### 1. Gradual Rollout

**Fase 1: Pilot (Week 1-2)**
- Deploy op 10 developer laptops
- Monitor gedurende 1 week
- Gather feedback op UX
- Test emergency scenarios

**Fase 2: Engineering Teams (Week 3-4)**
- Rollout naar alle developers (50-100 users)
- Add support team
- Monitor approval latency
- Tune poll interval

**Fase 3: Company-wide (Week 5+)**
- Alle workstations
- Mandatory via GPO/MDM
- 24/7 support ready
- Incident response procedures

### 2. Emergency Break-Glass

Als agent faalt, users moeten kunnen werken:

```yaml
# config.yaml
failsafe_mode: true  # Bij controller outage: keep current memberships
emergency_local_admin: emergency-admin  # Local account bypass PIM
```

**Procedure:**
1. User kan niet elevaten → Merkt dat agent down is
2. IT Help Desk: Grant temporary via emergency account
3. Incident logged in separate system
4. Agent fix + rollout
5. Remove temporary access

### 3. Monitoring & Alerting

```yaml
# Prometheus alerting rules
groups:
  - name: pim-agent
    rules:
      - alert: PIMAgentDown
        expr: up{job="pim-agent"} == 0
        for: 5m
        annotations:
          summary: "PIM Agent down on {{ $labels.instance }}"
      
      - alert: PIMAgentHighErrors
        expr: rate(pim_agent_errors_total[5m]) > 0.1
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
      
      - alert: PIMAgentStaleSync
        expr: time() - pim_agent_last_sync_timestamp > 300
        annotations:
          summary: "Agent not syncing on {{ $labels.instance }}"
```

### 4. Backup & Recovery

```bash
# Backup agent config + certificates
tar czf pim-agent-backup.tar.gz \
  /etc/pim-agent/config.yaml \
  /etc/pim-agent/machine.crt \
  /etc/pim-agent/machine.key

# Store in secure location (NOT on same machine)
aws s3 cp pim-agent-backup.tar.gz s3://backups/pim-agent/$(hostname)/

# Restore
aws s3 cp s3://backups/pim-agent/$(hostname)/pim-agent-backup.tar.gz .
sudo tar xzf pim-agent-backup.tar.gz -C /
sudo systemctl restart pim-agent
```

### 5. Updates & Patching

```bash
# Automated update check (daily cron)
#!/bin/bash
CURRENT_VERSION=$(pim-agent --version)
LATEST_VERSION=$(curl -s https://releases.itlusions.com/pim-agent/latest/VERSION)

if [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
    echo "Update available: $LATEST_VERSION"
    # Download new version
    curl -o /tmp/pim-agent https://releases.itlusions.com/pim-agent/latest/pim-agent-linux-amd64
    # Verify signature
    curl -o /tmp/pim-agent.sig https://releases.itlusions.com/pim-agent/latest/pim-agent-linux-amd64.sig
    gpg --verify /tmp/pim-agent.sig /tmp/pim-agent
    # Install
    sudo systemctl stop pim-agent
    sudo mv /tmp/pim-agent /usr/local/bin/pim-agent
    sudo chmod +x /usr/local/bin/pim-agent
    sudo systemctl start pim-agent
fi
```

---

## Samenvatting

**Wat hebben we bereikt?**

✅ **Tijdelijke lokale admin** zonder permanente privileges  
✅ **Centrale approval workflow** via Keycloak PIM  
✅ **Automatic expiration** & cleanup  
✅ **Cross-platform** (Windows/Linux/macOS)  
✅ **Complete audit trail** (who/what/when/why)  
✅ **Self-healing** (detecteert manual changes)  
✅ **Production-ready** (monitoring, rollback, break-glass)

**Engineer Workflow:**
```bash
# 1. Request
itlc elevate --type=local-group --name=local-admin --duration=1h --reason="Install software"

# 2. Agent sync (binnen 30 seconden)
# → User toegevoegd aan Administrators

# 3. Install software met admin rechten

# 4. Auto-removal na 1 uur
```

**Security Benefits:**
- Geen permanente admin accounts
- Just-in-time access principle
- Approval voor gevoelige elevations
- Time-bound (max 24h, meestal 1-4h)
- Audit trail voor compliance
- Reduced attack surface

---

## Next Steps

1. **Deploy PIM Controller** - [KEYCLOAK_PIM_IMPLEMENTATIE.md](KEYCLOAK_PIM_IMPLEMENTATIE.md)
2. **Configure Eligible Roles** - Define local-admin, local-docker, etc.
3. **Configure Application Whitelist** - Define approved software
4. **Enroll Machines** - Generate certificates, deploy agents
5. **Test End-to-End** - Request elevation + software install
6. **Train Users** - Walkthrough itlc commands, approval process
7. **Monitor Adoption** - Track metrics, gather feedback

---

## ITLC CLI Commands voor Installation Service

### Software Installatie Aanvragen

```bash
# Basic installation (self-service)
itlc install --app=docker-desktop --reason="Need Docker for development"

# Met ticket reference
itlc install --app=vscode --reason="Development environment setup" --ticket=TASK-1234

# Applicatie die approval vereist
itlc install --app=wireshark --reason="Network debugging" --ticket=INC-5678
# → Pending approval from security-team
# → User krijgt notificatie bij approval
# → Agent installeert automatisch na approval

# Custom package (niet in whitelist) - Requires 'unmanaged_install' permission
itlc install --custom --package="./CustomerDebugTool-v2.1.msi" \
  --reason="Customer-specific debugging tool for Contract-ABC" \
  --ticket=PROJ-ABC-789

# Output (if user lacks permission):
# [✗] Permission denied: User lacks 'unmanaged_install' permission
#     Custom package installation requires Level 3 security clearance.
#     Current permissions: [managed_install, managed_exec]
#     Contact security team to request 'unmanaged_install' permission.

# Output (if user has permission):
# [*] Uploading package: CustomerDebugTool-v2.1.msi (45.2 MB)
# [*] Calculating SHA256 checksum...
# [✓] Upload complete: sha256:abc123...
# [*] Running antivirus scan...
# [✓] Antivirus: Clean (0 threats)
# [!] MANDATORY APPROVAL REQUIRED
#     → Notification sent to security-team
#     → Request ID: req_custom_abc123
#     → Package available for inspection at:
#       https://pim.company.com/packages/req_custom_abc123
# [*] Waiting for approval (timeout: 24h)...

# Managed process execution (self-service if in whitelist)
itlc exec --command-alias=database_backup \
  --args="--database=production --output=/backups/" \
  --reason="Scheduled production backup"

# Output:
# [*] Executing managed command: database_backup
# [*] Command: /usr/local/bin/backup-db.sh
# [✓] Permission check: managed_exec ✓
# [*] Executing as root...
# [stdout] Backup started...
# [✓] Completed (exit code: 0)

# Unmanaged process execution (REQUIRES 2 APPROVALS)
itlc exec --command="C:\\Program Files\\CustomApp\\repair.exe" \
  --args="--database=production --repair-indexes" \
  --reason="Emergency database repair after corruption" \
  --ticket=INC-CRITICAL-001

# Output (if user lacks permission):
# [✗] Permission denied: User lacks 'unmanaged_exec' permission
#     Ad-hoc process execution requires Level 4 security clearance.
#     This is the HIGHEST risk operation.
#     Contact security team + C-level for approval.

# Output (if user has permission):
# [!] UNMANAGED PROCESS EXECUTION (HIGHEST RISK)
#     Command: C:\Program Files\CustomApp\repair.exe
#     Arguments: --database=production --repair-indexes
#     Permission: unmanaged_exec (Level 4) ✓
# [!] REQUIRES 2 APPROVALS (security-team + c-level)
#     → Notification sent to sre-managers
#     → Request ID: req_exec_xyz789
# [*] Waiting for approval...
# [✓] Approved by: manager@company.com
# [*] Executing command...
# [stdout captured]
# Database repair started...
# Rebuilding indexes: 15/47 complete...
# [✓] Process completed (exit code: 0)
# [*] Full output saved to audit log

# Check status
itlc install status

# Output:
# Pending installations:
#   [1] wireshark - Waiting for approval
#       Requested: 5 minutes ago
#       Approvers: security-team
# 
# Completed installations (last 7 days):
#   ✓ docker-desktop - Installed 2 days ago
#   ✓ vscode - Installed 1 week ago

# Check welke apps beschikbaar zijn
itlc install list

# Output:
# Available applications for your role:
#   docker-desktop - Docker Desktop (self-service)
#   vscode - Visual Studio Code (self-service)
#   postman - Postman API Client (self-service)
#   wireshark - Wireshark Network Analyzer (requires approval)
#   company-vpn - Company VPN Client (self-service)
```

### Voor Approvers

```bash
# List pending installation requests
itlc approve list --type=installation

# Output:
# Pending installation requests:
#   [1] john@company.com → wireshark (managed_install + approval) 🟡
#       Reason: Network debugging production issue
#       Ticket: INC-5678
#       Requested: 10 minutes ago
#       Machine: john-laptop.company.com
#       Approvers needed: 1 (security-team)
#   
#   [2] alice@company.com → CUSTOM PACKAGE (unmanaged_install) 🟠 HIGH RISK
#       Package: CustomerDebugTool-v2.1.msi (45.2 MB)
#       SHA256: abc123def456...
#       Antivirus: Clean ✓
#       Reason: Customer-specific debugging for Project-ABC
#       Ticket: PROJ-ABC-789
#       Requested: 5 minutes ago
#       Machine: alice-workstation.company.com
#       📦 Download package: itlc approve inspect 2
#   
#   [3] bob@company.com → UNMANAGED PROCESS (unmanaged_exec) 🔴 CRITICAL RISK
#       Command: C:\Program Files\CustomApp\repair.exe
#       Args: --database=production --repair-indexes
#       Reason: Emergency database repair
#       Ticket: INC-CRITICAL-001
#       Requested: 2 minutes ago
#       Machine: db-server-01.company.com
#       Approvers needed: 2 (security-team + c-level)
#       Approvals so far: 1/2 (approved by: security-lead@company.com)

# Inspect custom package (download voor analyse)
itlc approve inspect 2

# Output:
# [*] Downloading package for inspection...
# [✓] Downloaded: CustomerDebugTool-v2.1.msi (45.2 MB)
# [*] Saved to: ~/pim-inspections/req_custom_abc123/
# [*] Package metadata:
#     SHA256: abc123def456...
#     Uploaded by: alice@company.com
#     Upload time: 2026-01-23 14:30:00 UTC
#     Antivirus: Clean (Windows Defender, ClamAV)
#     File type: MSI (Windows Installer)
# 
# [!] SECURITY REVIEW CHECKLIST:
#     [ ] Verified package source/vendor
#     [ ] Checked digital signature
#     [ ] Scanned with additional tools (VirusTotal?)
#     [ ] Validated business justification
#     [ ] Confirmed ticket reference

# Approve
itlc approve 1 --comment="Approved for incident response"

# Approve custom package (strengere check)
itlc approve 2 --comment="Verified: Official vendor package, digitally signed by CustomerCorp Inc."

# Approve process execution
itlc approve 3 --comment="Emergency approved, database team lead confirmed need"

# Deny
itlc deny 1 --reason="Use VPN instead, no local packet capture needed"
itlc deny 2 --reason="Package not digitally signed, request official vendor release"
```

### Installation History & Audit

```bash
# View eigen installation history
itlc install history

# Output:
# Installation history:
#   2026-01-23 14:30 - docker-desktop v4.26.1 - SUCCESS
#   2026-01-20 09:15 - vscode v1.85.0 - SUCCESS
#   2026-01-15 16:45 - postman v10.21.0 - SUCCESS

# View team installations (voor managers)
itlc install history --team=backend --last=30d

# Export audit log
itlc install audit --export=csv --output=installs-jan-2026.csv
```

---

**Privilege Agent** - Lokale admin rechten EN software management zoals het hoort: temporary, justified, auditable, secure.
