# Instructions

1. Clone this repository
   ```bash
   git clone https://github.com/imitoy/linux-PKGBUILD
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
