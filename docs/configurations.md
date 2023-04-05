# Muse Configurations

List of Environmnet variables

- `SD_VARIANT`: You can select the stable diffusion model name.
  - If the value is undefined, default value is "sd1".
  - Possilbe value
    - Stable diffusion v1.4: sd1.4
    - Stable diffusion v1.5: sd1.5, sd1, sd
    - Stable diffusion v2-base: sd2, sd2_base
    - Stable diffusion v2-high: sd2_high
    - Any other url for downloading chkpt file
    - Any other local path
- `SD_VERSION`: Specific version of stable diffusion model.
  - If the value is undefined, default value is 1.
  - Possible value: 1 or 2
  - This varaible can be affects only configuration of stable diffusion.
