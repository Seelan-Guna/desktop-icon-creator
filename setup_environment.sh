#!/bin/bash

# Desktop Icon Creator - Virtual Environment Setup Script
# This script creates a Python virtual environment and installs all required dependencies

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup function
main() {
    echo "=============================================="
    echo "  Desktop Icon Creator - Environment Setup  "
    echo "=============================================="
    echo

    # Check if Python 3 is installed
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install it first:"
        echo "  sudo apt update && sudo apt install python3 python3-pip python3-venv python3-tk"
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_status "Found Python version: $PYTHON_VERSION"

    # Check if venv module is available
    if ! python3 -m venv --help >/dev/null 2>&1; then
        print_error "Python venv module is not available. Installing..."
        sudo apt update && sudo apt install python3-venv
    fi

    # Check if tkinter is available
    print_status "Checking for tkinter (GUI library)..."
    if ! python3 -c "import tkinter" 2>/dev/null; then
        print_warning "tkinter not found. Installing python3-tk..."
        sudo apt update && sudo apt install python3-tk
        
        # Verify tkinter installation
        if ! python3 -c "import tkinter" 2>/dev/null; then
            print_error "Failed to install tkinter. Please install manually:"
            echo "  sudo apt update && sudo apt install python3-tk"
            exit 1
        else
            print_success "tkinter installed successfully!"
        fi
    else
        print_success "tkinter found!"
    fi

    # Set virtual environment directory name
    VENV_DIR="venv"
    
    # Check if virtual environment already exists
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment '$VENV_DIR' already exists."
        read -p "Do you want to remove it and create a new one? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
        else
            print_status "Using existing virtual environment..."
        fi
    fi

    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creating virtual environment in '$VENV_DIR'..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created successfully!"
    fi

    # Activate virtual environment
    print_status "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip

    # Install required dependencies
    print_status "Installing required dependencies..."
    
    # List of required packages
    PACKAGES=(
        "pillow"
        "cairosvg"
    )

    # Install each package
    for package in "${PACKAGES[@]}"; do
        print_status "Installing $package..."
        pip install "$package"
    done

    # Create custom directories
    print_status "Creating custom directories..."
    mkdir -p CustomScripts CustomIcons
    print_success "Custom directories created: CustomScripts/ and CustomIcons/"

    # Verify installations
    print_status "Verifying installations..."
    
    python3 -c "
import sys
try:
    import tkinter as tk
    print('✓ tkinter (GUI library) imported successfully')
except ImportError as e:
    print('✗ Failed to import tkinter:', e)
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
    print('✓ Pillow (PIL) imported successfully')
except ImportError as e:
    print('✗ Failed to import Pillow:', e)
    sys.exit(1)

try:
    import cairosvg
    print('✓ cairosvg imported successfully')
except ImportError as e:
    print('✗ Failed to import cairosvg:', e)
    sys.exit(1)

print('✓ All dependencies verified successfully!')
"

    # Check for system dependencies
    print_status "Checking system dependencies..."
    
    SYSTEM_DEPS=("gio" "fc-list" "update-desktop-database")
    MISSING_DEPS=()
    
    for dep in "${SYSTEM_DEPS[@]}"; do
        if command_exists "$dep"; then
            echo "✓ $dep found"
        else
            echo "✗ $dep missing"
            MISSING_DEPS+=("$dep")
        fi
    done
    
    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        print_warning "Some system dependencies are missing. Installing..."
        case "${MISSING_DEPS[@]}" in
            *"gio"*)
                sudo apt update && sudo apt install glib2.0-bin
                ;;
            *"fc-list"*)
                sudo apt update && sudo apt install fontconfig
                ;;
            *"update-desktop-database"*)
                sudo apt update && sudo apt install desktop-file-utils
                ;;
        esac
    fi

    # Create activation script
    print_status "Creating activation script..."
    cat > activate_env.sh << 'EOF'
#!/bin/bash
# Activation script for Desktop Icon Creator environment

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated!"
    echo "Custom directories:"
    echo "  - CustomScripts/  (shell scripts)"
    echo "  - CustomIcons/    (generated icons)"
    echo ""
    echo "You can now run: python3 desktop_icon_creator.py"
    echo "Or use the desktop icon if available!"
else
    echo "Error: Virtual environment not found!"
    echo "Run setup_environment.sh first."
    exit 1
fi
EOF

    chmod +x activate_env.sh

    # Create requirements.txt for future reference
    print_status "Creating requirements.txt..."
    pip freeze > requirements.txt

    # Create desktop icon for the Desktop Icon Creator itself
    print_status "Creating desktop icon for Desktop Icon Creator..."
    if [ -f "desktop_icon_creator.py" ]; then
        python3 desktop_icon_creator.py --create-self-icon
        if [ $? -eq 0 ]; then
            print_success "Desktop Icon Creator icon created successfully!"
        else
            print_warning "Could not create desktop icon automatically"
        fi
    else
        print_warning "desktop_icon_creator.py not found. Please ensure it's in the current directory."
        echo "You can create the desktop icon manually after copying the Python script here."
    fi

    # Final success message
    echo
    echo "=============================================="
    print_success "Setup completed successfully!"
    echo "=============================================="
    echo
    echo "Virtual environment created in: $(pwd)/$VENV_DIR"
    echo "Custom directories created:"
    echo "  - CustomScripts/      (for shell scripts)"
    echo "  - CustomIcons/        (for generated icons)"
    echo
    echo "To use the environment:"
    echo "  1. Activate it: source venv/bin/activate"
    echo "     Or run: ./activate_env.sh"
    echo "  2. Run the application: python3 desktop_icon_creator.py"
    echo "     Or click the Desktop Icon Creator icon on your desktop!"
    echo "  3. Deactivate when done: deactivate"
    echo
    echo "Command Line Usage Examples:"
    echo "  # GUI mode"
    echo "  python3 desktop_icon_creator.py"
    echo ""
    echo "  # CLI mode - simple icon"
    echo "  python3 desktop_icon_creator.py --text \"My App\" --script-content \"echo 'Hello!'\""
    echo ""
    echo "  # CLI mode - gradient icon"
    echo "  python3 desktop_icon_creator.py --text \"Gradient\" --script ./test.sh \\"
    echo "    --gradient --bg-color red --gradient-color2 yellow --gradient-direction horizontal"
    echo ""
    echo "  # Get full help"
    echo "  python3 desktop_icon_creator.py --help"
    echo
    echo "Files created:"
    echo "  - $VENV_DIR/                              (virtual environment)"
    echo "  - activate_env.sh                         (convenience activation script)"  
    echo "  - requirements.txt                        (installed packages list)"
    echo "  - CustomScripts/                          (directory for shell scripts)"
    echo "  - CustomIcons/                           (directory for generated icons)"
    if [ -f "CustomScripts/desktop_icon_creator_launcher.sh" ]; then
        echo "  - CustomScripts/desktop_icon_creator_launcher.sh (launcher script)"
        echo "  - CustomIcons/desktop_icon_creator.png          (application icon)"
    fi
    echo
    print_success "Environment is ready to use!"
    print_status "Look for 'Desktop Icon Creator' on your desktop or in Show Apps!"
}

# Handle script interruption
trap 'print_error "Setup interrupted by user"; exit 1' INT

# Run main function
main "$@"
