# Azur Lane Painting Reconstruction

This script is a modification of [Krazete's script](https://github.com/Krazete/azur-paint) and primarily addresses issues related to the positioning of faces and various special cases.

## Usage

### Setup

Arrange your files in the following structure:

```
Working Directory/
├── main.py
├── AssetBundles/
│   ├── dependencies
│   ├── painting/
│   │   ├── changfeng_2_n         # Example painting asset
│   │   ├── changfeng_2_n_tex     # Corresponding texture asset
│   │   ├── touming_tex           # Transparency texture (recommended)
│   ├── paintingface/
│   │   └── changfeng_2           # Face asset for the painting
├── ship_skin_template.json       # Optional, for structured output
├── ship_data_group.json          # Optional, for structured output
└── secretary_special_ship.json   # Optional, for structured output
```

   - Place `main.py` in the root of your working directory.
   - Store painting assets under `AssetBundles/painting`.
   - Store face assets under `AssetBundles/paintingface`.
   - Ensure the `dependencies` file is included in the `AssetBundles` directory.
   - It is recommended to also include the `touming_tex` file in `AssetBundles/painting` as it is used in many paintings.

### Running the Script

- **To process all available files:**
  
  ```bash
  python main.py
  ```
  
- **To process a specific file:**
  
  ```bash
  python main.py changfeng_2_n
  ```

### Output

- Reconstructed paintings are saved in the `output2` folder.
- To generate numbered filenames, add `ship_skin_template.json`, `ship_data_group.json`, and `secretary_special_ship.json` to your working directory. These files can be found [here](https://github.com/AzurLaneTools/AzurLaneData/tree/main/CN/ShareCfg).

## Tips

- The iOS client typically offers higher quality for `painting` assets.
- The quality of `paintingface` assets varies between platforms; some are better on iOS, while others on Android.

## Known Issues

- `jinluhao_hx` is missing the character texture.
- Some paintings (e.g., `xiao_5` and `xiao_5_n`) show face positioning differences between versions with/without the background (consistent with in-game behavior).
- `xiaoyue_2` incorrectly places a body variant at the face position.
- Some assets contain both censored and uncensored versions of paintings (e.g., `npcshengluyisi_5_n`); the script only processes the first version encountered.

