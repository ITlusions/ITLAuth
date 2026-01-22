#!/bin/bash
#
# ITLAuth Zero-Click Installer for Linux/macOS
# 
# Usage: 
#   curl -fsSL https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.sh | bash
#   wget -qO- https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${GREEN}${BOLD}"
    echo "═══════════════════════════════════════════════════════"
    echo "  ITLAuth Zero-Click Installer"
    echo "  ITlusions Authentication Suite"
    echo "═══════════════════════════════════════════════════════"
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Check Python installation
check_python() {
    print_step "Checking Python installation..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python $PYTHON_VERSION found"
        return 0
    elif command_exists python; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
        print_success "Python $PYTHON_VERSION found"
        return 0
    else
        print_error "Python 3.8+ is required but not found"
        return 1
    fi
}

# Check pip installation
check_pip() {
    print_step "Checking pip installation..."
    
    if $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
        print_success "pip found"
        return 0
    else
        print_warning "pip not found, attempting to install..."
        
        # Try to install pip
        if command_exists curl; then
            curl -fsSL https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
        elif command_exists wget; then
            wget -qO- https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
        else
            print_error "Cannot install pip: curl or wget required"
            return 1
        fi
        
        print_success "pip installed"
        return 0
    fi
}

# Install the package
install_package() {
    print_step "Installing itl-kubectl-oidc-setup..."
    
    # Try to install in user space first
    if $PYTHON_CMD -m pip install --user itl-kubectl-oidc-setup >/dev/null 2>&1; then
        print_success "Package installed successfully (user)"
    elif $PYTHON_CMD -m pip install itl-kubectl-oidc-setup >/dev/null 2>&1; then
        print_success "Package installed successfully"
    else
        print_error "Failed to install package"
        print_info "Try manually: $PYTHON_CMD -m pip install itl-kubectl-oidc-setup"
        return 1
    fi
    
    return 0
}

# Verify installation
verify_installation() {
    print_step "Verifying installation..."
    
    # Check if command is available
    if command_exists itl-kubectl-oidc-setup; then
        VERSION=$(itl-kubectl-oidc-setup --version 2>&1 | awk '{print $2}')
        print_success "itl-kubectl-oidc-setup $VERSION is installed and ready"
        return 0
    else
        print_warning "Command not found in PATH"
        print_info "You may need to add Python's bin directory to your PATH"
        
        OS_TYPE=$(detect_os)
        if [[ "$OS_TYPE" == "linux" ]]; then
            print_info "Add to ~/.bashrc or ~/.zshrc:"
            print_info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        elif [[ "$OS_TYPE" == "macos" ]]; then
            print_info "Add to ~/.bash_profile or ~/.zshrc:"
            print_info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi
        
        return 1
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║           Installation Complete! 🎉                  ║${NC}"
    echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Next Steps:${NC}"
    echo ""
    echo -e "  ${CYAN}1. Run the setup tool:${NC}"
    echo -e "     ${BOLD}itl-kubectl-oidc-setup${NC}"
    echo ""
    echo -e "  ${CYAN}2. Follow the interactive prompts${NC}"
    echo ""
    echo -e "  ${CYAN}3. Authenticate with your ITlusions credentials${NC}"
    echo ""
    echo -e "${BOLD}Need Help?${NC}"
    echo -e "  📖 Documentation: https://github.com/ITlusions/ITLAuth"
    echo -e "  🐛 Issues: https://github.com/ITlusions/ITLAuth/issues"
    echo -e "  🌐 Website: https://www.itlusions.com"
    echo ""
}

# Main installation process
main() {
    print_header
    
    # Detect OS
    OS_TYPE=$(detect_os)
    if [[ "$OS_TYPE" == "unknown" ]]; then
        print_error "Unsupported operating system"
        exit 1
    fi
    print_info "Detected OS: $OS_TYPE"
    echo ""
    
    # Check Python
    if ! check_python; then
        print_error "Please install Python 3.8+ first"
        
        if [[ "$OS_TYPE" == "linux" ]]; then
            print_info "Try: sudo apt-get install python3 python3-pip"
            print_info "  or: sudo yum install python3 python3-pip"
        elif [[ "$OS_TYPE" == "macos" ]]; then
            print_info "Try: brew install python3"
            print_info "  or download from: https://www.python.org/downloads/"
        fi
        
        exit 1
    fi
    
    # Check pip
    if ! check_pip; then
        print_error "pip is required but could not be installed"
        exit 1
    fi
    
    echo ""
    
    # Install package
    if ! install_package; then
        exit 1
    fi
    
    echo ""
    
    # Verify installation
    PATH_UPDATED=0
    if ! verify_installation; then
        # Try to update PATH for current session
        if [[ -d "$HOME/.local/bin" ]]; then
            export PATH="$HOME/.local/bin:$PATH"
            PATH_UPDATED=1
            
            if verify_installation; then
                print_success "PATH updated for current session"
            fi
        fi
    fi
    
    echo ""
    
    # Print next steps
    print_next_steps
    
    # Reminder about PATH if needed
    if [[ $PATH_UPDATED -eq 1 ]]; then
        echo -e "${YELLOW}${BOLD}⚠ IMPORTANT:${NC}"
        echo -e "${YELLOW}  For permanent access, add the following to your shell config:${NC}"
        echo -e "${BOLD}  export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        echo ""
    fi
}

# Run main function
main
