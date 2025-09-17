# Windows ISO Downloader

Downloads Windows for VMs. Two scripts with different trade-offs.

## For QEMU/VirtualBox/VMware - Use download_iso.py

```bash
python3 download_iso.py
```

- Downloads **bootable ISO** ready for VMs
- ~4.7GB
- Gets Windows Server/Enterprise Evaluation
- **This is what you want for QEMU**

## For Specific Editions - Use download_esd.py

```bash
# Setup
uv sync
brew install cabextract wimlib  # macOS
sudo apt install cabextract wimtools  # Ubuntu

# Run
uv run python download_esd.py
```

- Downloads Enterprise N (lightest, no media bloat)
- Creates `win.wim` file (**NOT BOOTABLE**)
- ~3.5GB download

### To Make ESD/WIM Bootable

You need Windows boot files. Options:

1. **Download Windows PE ISO** (500MB)
   - Get from: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/download-winpe--windows-pe
   - Extract it, add win.wim to sources/, recreate ISO

2. **Use existing Windows ISO as donor**
   ```bash
   # Extract donor ISO
   7z x some-windows.iso -o./iso_files/
   # Replace install.wim
   cp win.wim ./iso_files/sources/install.wim
   # Recreate ISO (needs oscdimg or mkisofs with proper boot flags)
   ```

3. **Use Ventoy USB**
   - Ventoy can boot WIM files directly
   - Copy win.wim to Ventoy USB

4. **PXE Boot**
   - WIM files work with network boot

## TL;DR

**Want ISO for QEMU?** Use `download_iso.py`

**Want Enterprise N?** Use `download_esd.py` but you'll need to find boot files elsewhere

## Why Two Scripts?

- Microsoft's catalog has more editions but only as ESD/WIM (no boot files)
- Microsoft's CDN has full ISOs but limited editions
- Can't create bootable ISO from ESD alone - this is Microsoft's bullshit, not mine