#
# ITLAuth Zero-Click Installer for Windows (PowerShell)
#
# Usage:
#   iwr -useb https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.ps1 | iex
#   Invoke-WebRequest -Uri https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.ps1 -UseBasicParsing | Invoke-Expression
#

# Requires -Version 5.1

# Set error action preference
$ErrorActionPreference = "Stop"

# Color functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Header {
    Write-Host ""
    Write-ColorOutput "=======================================================" "Green"
    Write-ColorOutput "  ITLAuth Zero-Click Installer" "Green"
    Write-ColorOutput "  ITlusions Authentication Suite" "Green"
    Write-ColorOutput "=======================================================" "Green"
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "[>] $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[OK] $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Blue"
}

# Check if command exists
function Test-Command {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Check Python installation
function Test-Python {
    Write-Step "Checking Python installation..."
    
    $pythonCommands = @("python", "python3", "py")
    $pythonFound = $false
    
    foreach ($cmd in $pythonCommands) {
        if (Test-Command $cmd) {
            try {
                $version = & $cmd --version 2>&1 | Out-String
                if ($version -match "Python (\d+\.\d+\.\d+)") {
                    $script:PythonCommand = $cmd
                    $pythonVersion = $matches[1]
                    Write-Success "Python $pythonVersion found ($cmd)"
                    $pythonFound = $true
                    break
                }
            }
            catch {
                continue
            }
        }
    }
    
    if (-not $pythonFound) {
        Write-Error "Python 3.8+ is required but not found"
        Write-Info "Install Python from: https://www.python.org/downloads/"
        Write-Info "Or use Windows Store: ms-windows-store://pdp/?productid=9NRWMJP3717K"
        return $false
    }
    
    return $true
}

# Check pip installation
function Test-Pip {
    Write-Step "Checking pip installation..."
    
    try {
        $pipVersion = & $script:PythonCommand -m pip --version 2>&1 | Out-String
        if ($pipVersion -match "pip") {
            Write-Success "pip found"
            return $true
        }
    }
    catch {
        Write-Warning "pip not found"
    }
    
    # Try to install pip
    Write-Step "Installing pip..."
    try {
        $getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
        $getPipScript = Join-Path $env:TEMP "get-pip.py"
        
        Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipScript -UseBasicParsing
        & $script:PythonCommand $getPipScript --user
        
        # Clean up temporary file
        if (Test-Path $getPipScript) {
            Remove-Item $getPipScript -Force -ErrorAction SilentlyContinue
        }
        
        Write-Success "pip installed"
        return $true
    }
    catch {
        Write-Error "Failed to install pip: $_"
        
        # Attempt cleanup even on error
        if (Test-Path $getPipScript) {
            Remove-Item $getPipScript -Force -ErrorAction SilentlyContinue
        }
        
        return $false
    }
}

# Install the package
function Install-Package {
    Write-Step "Installing itl-kubectl-oidc-setup..."
    
    try {
        # Try user installation first
        $installArgs = @("-m", "pip", "install", "--user", "itl-kubectl-oidc-setup")
        
        $stdoutFile = Join-Path $env:TEMP "pip-stdout-$([guid]::NewGuid()).txt"
        $stderrFile = Join-Path $env:TEMP "pip-stderr-$([guid]::NewGuid()).txt"
        
        $process = Start-Process -FilePath $script:PythonCommand -ArgumentList $installArgs -Wait -NoNewWindow -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
        
        # Clean up temp files
        Remove-Item $stdoutFile -Force -ErrorAction SilentlyContinue
        Remove-Item $stderrFile -Force -ErrorAction SilentlyContinue
        
        if ($process.ExitCode -eq 0) {
            Write-Success "Package installed successfully"
            return $true
        }
        else {
            # Try without --user flag
            $installArgs = @("-m", "pip", "install", "itl-kubectl-oidc-setup")
            $process = Start-Process -FilePath $script:PythonCommand -ArgumentList $installArgs -Wait -NoNewWindow -PassThru
            
            if ($process.ExitCode -eq 0) {
                Write-Success "Package installed successfully"
                return $true
            }
            else {
                Write-Error "Failed to install package"
                Write-Info "Try manually: $script:PythonCommand -m pip install itl-kubectl-oidc-setup"
                return $false
            }
        }
    }
    catch {
        Write-Error "Failed to install package: $_"
        return $false
    }
}

# Verify installation
function Test-Installation {
    Write-Step "Verifying installation..."
    
    # Refresh PATH for current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    if (Test-Command "itl-kubectl-oidc-setup") {
        try {
            $version = & itl-kubectl-oidc-setup --version 2>&1 | Out-String
            if ($version -match "(\d+\.\d+\.\d+)") {
                Write-Success "itl-kubectl-oidc-setup $($matches[1]) is installed and ready"
                return $true
            }
        }
        catch {
            Write-Warning "Command found but version check failed"
        }
    }
    
    Write-Warning "Command not found in PATH"
    Write-Info "You may need to restart PowerShell or add Python Scripts to PATH"
    
    # Try to find the installation
    $pythonUserBase = & $script:PythonCommand -c "import site; print(site.USER_BASE)" 2>$null
    if ($pythonUserBase) {
        $scriptsPath = Join-Path $pythonUserBase "Scripts"
        Write-Info "Possible location: $scriptsPath"
    }
    
    return $false
}

# Print next steps
function Write-NextSteps {
    Write-Host ""
    Write-ColorOutput "=======================================================" "Green"
    Write-ColorOutput "           Installation Complete!                     " "Green"
    Write-ColorOutput "=======================================================" "Green"
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor White
    Write-Host ""
    Write-ColorOutput "  1. Restart PowerShell (to refresh PATH)" "Cyan"
    Write-Host ""
    Write-ColorOutput "  2. Run the setup tool:" "Cyan"
    Write-Host "     itl-kubectl-oidc-setup" -ForegroundColor White
    Write-Host ""
    Write-ColorOutput "  3. Follow the interactive prompts" "Cyan"
    Write-Host ""
    Write-ColorOutput "  4. Authenticate with your ITlusions credentials" "Cyan"
    Write-Host ""
    Write-Host "Need Help?" -ForegroundColor White
    Write-Host "  [DOCS] Documentation: https://github.com/ITlusions/ITLAuth"
    Write-Host "  [BUGS] Issues: https://github.com/ITlusions/ITLAuth/issues"
    Write-Host "  [WEB]  Website: https://www.itlusions.com"
    Write-Host ""
}

# Main installation process
function Install-ITLAuth {
    Write-Header
    
    # Check if running as administrator (not required, just info)
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($isAdmin) {
        Write-Info "Running as Administrator"
    }
    else {
        Write-Info "Running as standard user (this is fine)"
    }
    Write-Host ""
    
    # Check Python
    if (-not (Test-Python)) {
        Write-Host ""
        Write-Error "Installation failed: Python not found"
        return
    }
    
    # Check pip
    if (-not (Test-Pip)) {
        Write-Host ""
        Write-Error "Installation failed: pip not available"
        return
    }
    
    Write-Host ""
    
    # Install package
    if (-not (Install-Package)) {
        Write-Host ""
        Write-Error "Installation failed: package installation error"
        return
    }
    
    Write-Host ""
    
    # Verify installation
    $pathNeedsRefresh = $false
    if (-not (Test-Installation)) {
        $pathNeedsRefresh = $true
    }
    
    Write-Host ""
    
    # Print next steps
    Write-NextSteps
    
    # Reminder about PATH if needed
    if ($pathNeedsRefresh) {
        Write-ColorOutput "[WARNING] IMPORTANT:" "Yellow"
        Write-ColorOutput "  Please restart PowerShell to refresh your PATH" "Yellow"
        Write-Host ""
    }
}

# Run main function
try {
    Install-ITLAuth
}
catch {
    Write-Host ""
    Write-Error "Installation failed with error: $_"
    Write-Host ""
    Write-Info "For manual installation, run:"
    Write-Info "  pip install itl-kubectl-oidc-setup"
    Write-Host ""
}
