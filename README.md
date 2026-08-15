# Introduction

This repository is created to fix Linux Audio on the Lenovo Legion Pro 7i Gen 10 (16IAX10H) and similar devices with kernel-level patches.

# Instructions

1. Clone this repository
   ```bash
   git clone https://github.com/imitoy/linux-PKGBUILD.git
   cd linux-PKGBUILD
   ```

2. Set parallel job count (Optional)
   ```bash
   export MAKEFLAGS=-j$(nproc)
   ```
   
3. Build & Install
   ```bash
   makepkg -si --skippgpcheck
   ```

   The `--skippgpcheck` parameter is needed since we are building a custom kernel.

4. To fix your audio, you need to install [the aw88399 firmware](https://github.com/imitoy/aw88399_acf-PKGBUILD).
5. Update grub config
```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```
6. Reboot
```bash
sudo reboot
```
