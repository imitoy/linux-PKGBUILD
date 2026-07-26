# Instructions

1. Clone this respository
   ```bash
   git clone https://github.com/imitoy/linux-PKGBUILD
   cd linux-PKGBUILD
   ```
   
2. Build & Install
   ```bash
   makepkg -si --skippgpcheck
   ```

   The `--skippgpcheck` parameter is needed since we are building a custom kernel.
