#!/bin/bash

echo "========================================"
echo "TopicalForge Setup Script"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "[X] Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "Python 3 found! :D"
echo ""

# Check if chromium-chromedriver is installed
echo "Checking for ChromeDriver..."
if command -v chromedriver &> /dev/null; then
    echo "ChromeDriver found at: $(which chromedriver)"
else
    echo "!! ChromeDriver not found !!"
    echo "/̵͇̿̿/’̿’̿"
    read -p "Would you like to install chromium-chromedriver? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install -y chromium-chromedriver
    else
        echo "Please install ChromeDriver manually:"
        echo "sudo apt install chromium-chromedriver"
        echo "Or download from: https://chromedriver.chromium.org/downloads"
        exit 1
    fi
fi

echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "[X] Failed to install dependencies"
    exit 1
fi

echo "Dependencies installed :D"
echo ""

# Create data directories
echo "Creating data directories..."
mkdir -p data/pdfs data/raw_questions data/sorted_questions logs

echo "Directories created"
echo ""

echo "========================================"
echo "Setup complete!"
echo "========================================"
echo ""
echo "To start the tool, run:"
echo "  python3 main.py"
echo ""
echo "For more information, see README.md"
echo "If you'd like to report an issue please contact me at:"
echo "myst1cso4p on Discord"
echo " or "
echo "Open an issue on GitHub: https://github.com/Myst1cS04p/TopicalForge/issues"
echo " or, (if you're an unc) "
echo "Email: myst1cs04p@gmail.com"
echo "========================================"