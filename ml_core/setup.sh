#!/bin/bash
# Setup script for ML core - clones and builds llama.cpp

set -e

echo "====================================="
echo "ML Core Setup"
echo "====================================="

# Check if llama.cpp already exists
if [ -d "llama.cpp" ]; then
    echo "llama.cpp directory already exists."
    read -p "Do you want to remove and re-clone? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing llama.cpp directory..."
        rm -rf llama.cpp
    else
        echo "Keeping existing llama.cpp directory."
        echo "If you want to rebuild, run: cd llama.cpp && make clean && make"
        exit 0
    fi
fi

# Clone llama.cpp
echo "Cloning llama.cpp repository..."
git clone https://github.com/ggerganov/llama.cpp.git

# Build llama.cpp
echo "Building llama.cpp..."
cd llama.cpp
make

echo ""
echo "====================================="
echo "Setup complete!"
echo "====================================="
echo ""
echo "llama.cpp has been cloned and built successfully."
echo "You can now run training jobs that will convert models to GGUF format."
