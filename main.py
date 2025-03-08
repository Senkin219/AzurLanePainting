import UnityPy
from PIL import Image
import os
from pathlib import Path
import re
import math
import json

root = "AssetBundles"


def get_id_dict():
    painting2id = {}
    if os.path.exists("ship_skin_template.json") and os.path.exists("ship_data_group.json") and os.path.exists("secretary_special_ship.json"):
        group2id = {}
        with open("ship_data_group.json", "r", encoding="utf8") as f1:
            group_map = json.load(f1)
        for key in group_map:
            group_type = group_map[key]["group_type"]
            group2id[group_type] = key
        with open("ship_skin_template.json", "r", encoding="utf8") as f2:
            skin_map = json.load(f2)
        for key in dict(reversed(list(skin_map.items()))):
            painting_name = skin_map[key]["painting"].lower()
            if group2id.get(skin_map[key]["ship_group"]):
                painting2id[painting_name] = group2id[skin_map[key]["ship_group"]]
        for key in dict(reversed(list(skin_map.items()))):
            painting_name = skin_map[key]["painting"].lower()
            if painting2id.get(painting_name) == None:
                painting2id[painting_name] = str(skin_map[key]["ship_group"])
        with open("secretary_special_ship.json", "r", encoding="utf8") as f3:
            child_map = json.load(f3)
        for key in child_map:
            if key.isnumeric():
                child_painting = child_map[key].get("painting")
                painting2id[child_painting] = str(child_map[key]["group"])
    return painting2id


def custom_round(n):
    floor_value = math.floor(n)
    decimal_part = n - floor_value
    if decimal_part == 0.5:
        return floor_value + 1
    else:
        return round(n)


def get_vertices(mesh, texture):
    v_raw = []  # mesh vertices
    vt_raw = []  # texture vertices
    # unused: g (group names), f (faces)
    for line in mesh.export().splitlines():
        if line.startswith("v "):
            vertex = line.split(" ")[1:]
            v_raw.append([int(n) for n in vertex])
        if line.startswith("vt "):
            vertex = line.split(" ")[1:]
            vt_raw.append([float(n) for n in vertex])
    assert len(v_raw) == len(vt_raw), "Unequal number of mesh vertices to texture vertices."
    xmax = max(x for x, y, z in v_raw)
    ymax = max(y for x, y, z in v_raw)
    v = [(xmax - x, ymax - y) for x, y, z in v_raw]
    w = texture.image.width
    h = texture.image.height
    vt = [(w * x, h - h * y) for x, y in vt_raw]
    return v, vt


def get_patches(texture, vt):
    patches = []
    n = int(len(vt) / 4)
    for i in range(n):
        a = i * 4
        b = a + 4
        xmin = min(x for x, y in vt[a:b])
        xmax = max(x for x, y in vt[a:b])
        ymin = min(y for x, y in vt[a:b])
        ymax = max(y for x, y in vt[a:b])
        patch = texture.image.crop((xmin, ymin, xmax, ymax))
        patches.append(patch)
    return patches


def stitch_patches(patches, v, mesh, size):
    xmin = min(x for x, y in v)
    xmax = max(x for x, y in v)
    ymin = min(y for x, y in v)
    ymax = max(y for x, y in v)
    dx = 1 + xmax - xmin
    dy = 1 + ymax - ymin
    canvas = Image.new("RGBA", (custom_round(size["x"]), custom_round(size["y"])))
    for i, patch in enumerate(patches):
        a = i * 4
        b = a + 4
        xmin = min(x for x, y in v[a:b])
        ymin = min(y for x, y in v[a:b])
        # yanusi_4
        if canvas.width < patch.width + custom_round(
            xmin + mesh.read_typetree()["m_LocalAABB"]["m_Center"]["x"] - mesh.read_typetree()["m_LocalAABB"]["m_Extent"]["x"]
        ) or canvas.height < patch.height + custom_round(-ymin - patch.height + mesh.read_typetree()["m_LocalAABB"]["m_Center"]["y"] + mesh.read_typetree()["m_LocalAABB"]["m_Extent"]["y"]):
            new_canvas = Image.new(
                "RGBA",
                (
                    max(canvas.width, patch.width + custom_round(xmin + mesh.read_typetree()["m_LocalAABB"]["m_Center"]["x"] - mesh.read_typetree()["m_LocalAABB"]["m_Extent"]["x"])),
                    max(canvas.height, patch.height + custom_round(-ymin - patch.height + mesh.read_typetree()["m_LocalAABB"]["m_Center"]["y"] + mesh.read_typetree()["m_LocalAABB"]["m_Extent"]["y"])),
                ),
            )
            new_canvas.alpha_composite(canvas, (0, 0))
            canvas = new_canvas
        canvas.paste(
            patch.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
            (
                custom_round(xmin + mesh.read_typetree()["m_LocalAABB"]["m_Center"]["x"] - mesh.read_typetree()["m_LocalAABB"]["m_Extent"]["x"]),
                custom_round(-ymin - patch.height + mesh.read_typetree()["m_LocalAABB"]["m_Center"]["y"] + mesh.read_typetree()["m_LocalAABB"]["m_Extent"]["y"]),
            ),
        )
    # qiabayefu_2_n
    if canvas.width > size["x"] or canvas.height > size["y"]:
        bbox = canvas.getbbox()
        if bbox:
            left, upper, right, lower = bbox
            new_bbox = (0, 0, max(right, size["x"]), max(lower, size["y"]))
        else:
            new_bbox = (0, 0, size["x"], size["y"])
        canvas = canvas.crop(new_bbox)
    canvas = canvas.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    del v
    del patches
    return canvas


def get_primary(asset):
    # Returns typetree of the primary asset (as reported by the AssetBundle).
    bundle = asset.objects[1]  # m_PathID is always 1 for the AssetBundle
    if bundle.type.name != "AssetBundle":  # in case the above isn't true
        # print("Object at m_PathID=1 is not an AssetBundle.\nSearching for AssetBundle...")
        found = False
        for value in asset.values():
            if value.type.name == "AssetBundle":
                bundle = value
                # print("AssetBundle found at m_PathID=", bundle.path_id, ".", sep="")
                found = True
                break
        assert found, "No AssetBundle found."
    bundletree = bundle.read_typetree()
    primaryid = bundletree["m_Container"][0][1]["asset"]["m_PathID"]
    primary = asset.objects[primaryid]
    return primaryid, primary.read_typetree()


def get_dependencies():
    # Returns dependency map linking asset files to their texture files.
    env = UnityPy.load(str(Path(root, "dependencies")))
    id, primary = get_primary(env.assets[0])
    del env
    dependencies = {}
    for m_Value in primary["m_Values"]:
        m_FileName = re.sub(r"^.*?(/painting/.*)?$", r"\g<1>", m_Value["m_FileName"])[1:]
        # m_FileName = re.sub('^.*?(/painting(?:face)?/.*)?$', '\g<1>', m_Value['m_FileName'])[1:] # includes paintingface
        if m_FileName:
            # if m_FileName.endswith('_tex'):
            #     if m_Value['m_Dependencies']:
            #         print('Texture file includes dependencies:',  m_FileName)
            # elif not m_Value['m_Dependencies']:
            #     print('Non-texture file without dependencies:', m_FileName)
            dependencies.setdefault(m_FileName, m_Value["m_Dependencies"])
    return dependencies


def get_layers(asset, textures, layers={}, id=None, parent=None, face=None):
    if id is None:
        id, gameobject = get_primary(asset)
    else:
        gameobject = asset[id].read_typetree()

    if gameobject["m_Name"] == "shop_hx":
        return
    if gameobject["m_Name"] == "shadow":
        return
    if "m_Component" not in gameobject:
        return

    children = None
    mesh_id = None
    entry = {}
    entry["name"] = gameobject["m_Name"]
    for ptr in gameobject["m_Component"]:
        component_id = ptr["component"]["m_PathID"]
        component = asset[component_id]
        tree = component.read_typetree()
        # print(gameobject["m_Name"],component.type.name,tree,"\n")
        if component.type.name == "RectTransform":
            entry["scale"] = tree["m_LocalScale"]
            if parent == None:
                entry["scale"] = {"x": 1, "y": 1, "z": 1}
            entry["delta"] = tree["m_SizeDelta"]
            # jinluhao, dafeng_idol
            if gameobject["m_Name"] == "layers":
                entry["delta"] = {"x": 0, "y": 0}
            entry["pivot"] = tree["m_Pivot"]

            # calculate true m_LocalPosition
            anchormin = tree["m_AnchorMin"]
            anchormax = tree["m_AnchorMax"]
            anchorpos = tree["m_AnchoredPosition"]
            if parent is None:
                entry["bound"] = entry["delta"]
                entry["anchor"] = {"x": entry["delta"]["x"] * entry["pivot"]["x"], "y": entry["delta"]["y"] * entry["pivot"]["y"]}
                entry["position"] = anchorpos
            else:
                pl = layers[parent]
                entry["bound"] = {
                    "x": pl["bound"]["x"] * (anchormax["x"] - anchormin["x"]) + max(entry["delta"]["x"], 0) * entry["scale"]["x"],
                    "y": pl["bound"]["y"] * (anchormax["y"] - anchormin["y"]) + max(entry["delta"]["y"], 0) * entry["scale"]["y"],
                }  # bounding box width and height
                entry["anchor"] = {
                    "x": pl["bound"]["x"] * (anchormax["x"] - anchormin["x"]) * entry["pivot"]["x"] + pl["bound"]["x"] * anchormin["x"],
                    "y": pl["bound"]["x"] * (anchormax["y"] - anchormin["y"]) * entry["pivot"]["y"] + pl["bound"]["y"] * anchormin["y"],
                }  # bounding box anchor in relation to box corner
                entry["position"] = {
                    "x": entry["anchor"]["x"] - pl["anchor"]["x"] + anchorpos["x"],
                    "y": entry["anchor"]["y"] - pl["anchor"]["y"] + anchorpos["y"],
                }  # anchor in relation to parent anchor
            if gameobject["m_Name"] == "face" and "parent" not in layers[parent]:
                entry["size"] = entry["delta"]
            children = tree["m_Children"]
        # bisimaiz
        if component.type.name == "Transform" and children == None and "m_Children" in tree:
            entry["scale"] = tree["m_LocalScale"]
            if parent == None:
                entry["scale"] = {"x": 1, "y": 1, "z": 1}
            entry["delta"] = {"x": 0, "y": 0}
            entry["pivot"] = {"x": 0.5, "y": 0.5}
            entry["bound"] = {"x": 0, "y": 0}
            entry["anchor"] = {"x": 0, "y": 0}
            entry["position"] = {"x": 0, "y": 0}
            children = tree["m_Children"]
        if "mMesh" in tree:
            mesh_id = tree["mMesh"]["m_PathID"]
            sprite_id = tree["m_Sprite"]["m_PathID"]
            entry["size"] = tree["mRawSpriteSize"]
        # xiefeierde_3
        elif "m_Sprite" in tree and entry["name"] != "face":
            entry["isImage"] = True
            mesh_id = 0
            sprite_id = tree["m_Sprite"]["m_PathID"]
            entry["size"] = entry["delta"]
    if mesh_id is not None:
        texas = {}
        for i in range(len(textures.assets)):
            texas = texas | textures.assets[i].objects
        try:
            entry["mesh"] = texas[mesh_id].read()
        except:
            # print("No mesh found.")
            pass
        try:
            sprite = texas[sprite_id].read_typetree()
            texture_id = sprite["m_RD"]["texture"]["m_PathID"]
            entry["texture"] = texas[texture_id].read()
        except:
            print("missing texture file")
    if parent is not None:
        entry["parent"] = parent

    layers[id] = entry

    if children is not None:
        for rt_ptr in children:
            rt_id = rt_ptr["m_PathID"]
            rt = asset[rt_id].read_typetree()
            child_id = rt["m_GameObject"]["m_PathID"]
            get_layers(asset, textures, layers, child_id, id, face)


def wrapped(painting_name, id_dict={}, debug=False):
    print("\nstart", painting_name)

    depmap = get_dependencies()
    textures = UnityPy.load(*["{}/{}".format(root, fn) for fn in depmap["painting/{}".format(painting_name)]])

    env = UnityPy.load(str(Path(root, "painting", painting_name)))
    layers = {}
    get_layers(env.assets[0], textures, layers, face=None)

    def get_position_box(layer, x=None, y=None, w=None, h=None):
        # scale: xianggelila_3
        if x is None or y is None:
            x = layer["delta"]["x"] * layer["pivot"]["x"] * layer["scale"]["x"] - layer["position"]["x"]
            y = layer["delta"]["y"] * layer["pivot"]["y"] * layer["scale"]["x"] - layer["position"]["y"]
            w = layer["delta"]["x"] * layer["scale"]["x"]
            h = layer["delta"]["y"] * layer["scale"]["x"]
        if "parent" in layer:
            parent = layers[layer["parent"]]
            # w *= parent['scale']['x']
            # h *= parent['scale']['y']
            x = x - parent["position"]["x"]
            y = y - parent["position"]["y"]
            return get_position_box(parent, x, y, w, h)
        return -x, -y, w - x, h - y

    from math import inf

    x0 = inf
    y0 = inf
    x1 = -inf
    y1 = -inf
    x2 = 0
    y2 = 0
    for i in layers:
        layer = layers[i]
        if "size" in layer:
            xi, yi, xj, yj = get_position_box(layer)
            layer["box"] = [xi, yi, xj, yj]
            x0 = min(x0, xi)
            y0 = min(y0, yi)
            x1 = max(x1, xj)
            y1 = max(y1, yj)
            if "parent" not in layer:
                x2 = xi
                y2 = yi
    fix = [0, 0]
    rw_flag = False
    for i in layers:
        layer = layers[i]
        if "box" in layer:
            layer["box"][0] -= x2
            layer["box"][1] -= y2
            layer["box"][2] -= x2
            layer["box"][3] -= y2
            if "_rw" in layer["name"]:
                fix[0] = custom_round(layer["box"][0]) - layer["box"][0]
                fix[1] = custom_round(layer["box"][1]) - layer["box"][1]
                rw_flag = True
    # wuzang_n, wuzang_s, qiabayefu_2
    if rw_flag == False:
        for i in layers:
            layer = layers[i]
            if "box" in layer and "parent" not in layer:
                name = layer["name"]
                for i in layers:
                    layer = layers[i]
                    if "box" in layer and "parent" in layer and (layer["name"] == name or layer["name"] == "paint"):
                        fix[0] = custom_round(layer["box"][0]) - layer["box"][0]
                        fix[1] = custom_round(layer["box"][1]) - layer["box"][1]
                        break
                break
    for i in layers:
        layer = layers[i]
        if "box" in layer:
            if layer["name"] == "face":
                layer["box"][0] += fix[0]
                layer["box"][1] += fix[1]
                layer["box"][2] += fix[0]
                layer["box"][3] += fix[1]
            layer["box"][2] = custom_round(layer["box"][0]) + layer["box"][2] - layer["box"][0]
            layer["box"][3] = custom_round(layer["box"][1]) + layer["box"][3] - layer["box"][1]
            layer["box"][0] = custom_round(layer["box"][0])
            layer["box"][1] = custom_round(layer["box"][1])
    for i in layers:
        layer = layers[i]
        if "box" in layer:
            layer["box"][0] = layer["box"][0] - (x0 - x2)
            layer["box"][1] = layer["box"][1] - (y0 - y2)
            layer["box"][2] = layer["box"][2] - (x0 - x2)
            layer["box"][3] = layer["box"][3] - (y0 - y2)
            if debug:
                print("box", layer["name"], layer["box"])
    try:
        master = Image.new("RGBA", (custom_round(x1 - x0), custom_round(y1 - y0)))
    except:
        print(painting_name, "failed")
        return

    if painting_name == "changfeng_2":
        front_layer = None
        for key, value in layers.items():
            if value.get("name") == "changfeng_2_bj":
                front_layer = key
                break
        if front_layer:
            layers[front_layer] = layers.pop(front_layer)

    canvases = []
    for i in layers:
        layer = layers[i]
        if "mesh" in layer and "texture" in layer:
            v, vt = get_vertices(layer["mesh"], layer["texture"])
            patches = get_patches(layer["texture"], vt)
            canvas = stitch_patches(patches, v, layer["mesh"], layer["size"])
            canvas = canvas.resize(
                (
                    custom_round(canvas.width * ((layer["box"][2] - layer["box"][0]) or layer["size"]["x"]) / layer["size"]["x"]),
                    custom_round(canvas.height * ((layer["box"][3] - layer["box"][1]) or layer["size"]["y"]) / layer["size"]["y"]),
                )
            ).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            canvases.append([canvas, layer])
        elif "texture" in layer:
            canvas = layer["texture"].image
            # xiefeierde_3
            if "isImage" in layer:
                canvas = canvas.resize(
                    (
                        custom_round((layer["box"][2] - layer["box"][0]) or canvas.width),
                        custom_round((layer["box"][3] - layer["box"][1]) or canvas.height),
                    )
                ).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            else:
                canvas = canvas.resize(
                    (
                        custom_round(canvas.width * ((layer["box"][2] - layer["box"][0]) or layer["size"]["x"]) / layer["size"]["x"]),
                        custom_round(canvas.height * ((layer["box"][3] - layer["box"][1]) or layer["size"]["y"]) / layer["size"]["y"]),
                    )
                ).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            canvases.append([canvas, layer])
        elif layer["name"] == "face":
            canvas = "face"
            canvases.append([canvas, layer])

    os.makedirs("output2", exist_ok=True)
    face0_flag = False
    faces = UnityPy.load(str(Path(root, "paintingface", painting_name.replace("_npc", "__nnpc").replace("_n", "").replace("_ex", ""))))
    if len(faces.assets) == 0 and "_hx" in painting_name:
        faces = UnityPy.load(str(Path(root, "paintingface", painting_name.replace("_hx", "").replace("_npc", "__nnpc").replace("_n", "").replace("_ex", ""))))
    if len(faces.assets) == 0 and "_wjz" in painting_name:
        faces = UnityPy.load(str(Path(root, "paintingface", painting_name.replace("_hx", "").replace("_npc", "__nnpc").replace("_n", "").replace("_ex", "").replace("_wjz", ""))))
    if len(faces.assets) == 0 and "_idolns" in painting_name:
        faces = UnityPy.load(str(Path(root, "paintingface", painting_name.replace("_hx", "").replace("_npc", "__nnpc").replace("_n", "").replace("_ex", "").replace("_idolns", "_idol"))))
    filename = painting_name
    if id_dict:
        filename = (
            id_dict.get(painting_name.replace("_wjz", "").replace("_hx", "").replace("_ex", "").replace("_idolns", "_idol").replace("_npc", "__nnpc").replace("_n", ""), "999999") + "_" + painting_name
        )
    if len(faces.assets) != 0:
        for value in faces.assets[0].values():
            if value.type.name == "Texture2D":
                face = value.read()
                if face.name == "0":
                    face0_flag = True
                if debug and face.name != "1":
                    continue
                copy = master.copy()
                for canvaslayer in canvases:
                    layer = canvaslayer[1]
                    canvas = canvaslayer[0]
                    if canvas == "face":
                        canvas = face.image
                        # bolisi
                        canvas = canvas.resize(
                            (
                                custom_round((layer["box"][2] - layer["box"][0]) or canvas.width),
                                custom_round((layer["box"][3] - layer["box"][1]) or canvas.height),
                            )
                        ).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    # qiye_4
                    if copy.width < canvas.width + custom_round(layer["box"][0]) or copy.height < canvas.height + custom_round(layer["box"][1]):
                        new_copy = Image.new("RGBA", (max(copy.width, canvas.width + custom_round(layer["box"][0])), max(copy.height, canvas.height + custom_round(layer["box"][1]))))
                        new_copy.alpha_composite(copy, (0, 0))
                        copy = new_copy
                    copy.alpha_composite(canvas.convert("RGBA"), (custom_round(layer["box"][0]), custom_round(layer["box"][1])))
                copy = copy.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                if False:
                    bbox = copy.getbbox()
                    if bbox:
                        copy = copy.crop(bbox)
                copy.save("output2/{}.png".format(filename + "." + face.name))
                del copy
    else:
        print(painting_name, "no face found\n")
        face0_flag = True
    for canvaslayer in canvases:
        layer = canvaslayer[1]
        canvas = canvaslayer[0]
        if canvas == "face":
            continue
        if master.width < canvas.width + custom_round(layer["box"][0]) or master.height < canvas.height + custom_round(layer["box"][1]):
            new_master = Image.new("RGBA", (max(master.width, canvas.width + custom_round(layer["box"][0])), max(master.height, canvas.height + custom_round(layer["box"][1]))))
            new_master.alpha_composite(master, (0, 0))
            master = new_master
        master.alpha_composite(canvas, (custom_round(layer["box"][0]), custom_round(layer["box"][1])))
    master = master.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    if face0_flag:
        master.save("output2/{}.png".format(filename))
    else:
        master.save("output2/{}.png".format(filename + ".0"))

    del master
    del layers
    del canvases
    del depmap
    del env
    del textures


if __name__ == "__main__":
    import multiprocessing
    from functools import partial

    id_dict = get_id_dict()
    paintingfiles = []
    for root2, dirs, files in os.walk(Path(root, "painting")):
        for file in files:
            if file[-4:] != "_tex":
                paintingfiles.append(file)

    debug = False
    mp = False
    if mp:
        multiprocessing.Pool().map(partial(wrapped, id_dict=id_dict, debug=debug), paintingfiles)
    else:
        for file in paintingfiles:
            wrapped(file, id_dict, debug)
