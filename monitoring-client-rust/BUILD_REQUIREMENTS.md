# Build Requirements

## Windows

To build on Windows, you need one of the following:

### Option 1: Visual Studio Build Tools (Recommended)
1. Download from: https://visualstudio.microsoft.com/downloads/
2. Install "Build Tools for Visual Studio 2022"
3. Select "Desktop development with C++" workload
4. Restart your terminal after installation

### Option 2: Visual Studio Community
1. Download from: https://visualstudio.microsoft.com/vs/community/
2. During installation, select "Desktop development with C++"
3. Restart your terminal after installation

### Option 3: Use GNU toolchain (MinGW)
```bash
# Install rustup with GNU toolchain
rustup toolchain install stable-x86_64-pc-windows-gnu
rustup default stable-x86_64-pc-windows-gnu
```

## Linux

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential pkg-config libssl-dev libx11-dev

# Fedora/RHEL
sudo dnf install gcc pkg-config openssl-devel libX11-devel

# Arch
sudo pacman -S base-devel openssl libx11
```

## macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Or install full Xcode from App Store
```

## Verifying Installation

After installing the required tools, verify with:

```bash
# Check Rust installation
rustc --version
cargo --version

# Check C++ compiler (Windows)
cl.exe

# Check C++ compiler (Linux/macOS)
gcc --version
```

## Building the Project

Once requirements are installed:

```bash
# Debug build
cargo build

# Release build
cargo build --release

# Run
cargo run
```

## Troubleshooting

### Windows: "linker `link.exe` not found"
- Install Visual Studio Build Tools as described above
- Restart your terminal/IDE after installation
- Verify `cl.exe` is in your PATH

### Linux: "cannot find -lX11"
- Install X11 development libraries: `sudo apt-get install libx11-dev`

### macOS: "xcrun: error: invalid active developer path"
- Run: `xcode-select --install`

## Cross-Compilation

To build for other platforms:

```bash
# Install cross-compilation tool
cargo install cross

# Build for Windows from Linux
cross build --target x86_64-pc-windows-gnu --release

# Build for Linux from Windows (requires Docker)
cross build --target x86_64-unknown-linux-gnu --release
```
