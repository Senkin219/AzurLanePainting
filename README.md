# Azur Lane Painting Reconstruction

This script is a modification of [Krazete's script](https://github.com/Krazete/azur-paint) and primarily addresses issues related to the positioning of faces and various special cases.

## Usage

Place `main.py` and `AssetBundles` in the same directory. Put the character paintings to be extract in `AssetBundles/painting` and the corresponding face files in `AssetBundles/paintingface`. Place `dependencies` in `AssetBundles`.

Note: Many no-background version paintings rely on textures in `touming_tex`, so it's best to also place it in `AssetBundles/painting`.

For more information about the directory structure, check out [Krazete's original repository](https://github.com/Krazete/azur-paint).

Run `python main.py`. The extracted paintings will be output to the `output2` folder. If you need numbered outputs, place `ship_skin_template.json`, `ship_data_group.json`, and `secretary_special_ship.json` in the same directory as the script. These files can be found [here](https://github.com/AzurLaneTools/AzurLaneData/tree/main/CN/ShareCfg).

## Known Issues

- `jinluhao_hx` lacks character textures.
- Some paintings have a background version with no face offset, while the no-background version has an offset, such as `xiao_5`. This offset also exists in the game.
- `xiaoyue_2` has body variant incorrectly placed in the position of the face.
- Some files contain both censored and uncensored versions of paintings, such as `npcshengluyisi_5_n`. The script will only extract the first one in order.