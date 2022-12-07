import json
import githubTool

mods_folder = "mods/"
sound_folder = "sound/"
tiles_folder = "gfx/"


def read_json(json_path):
    json_data = ""
    with open(json_path) as json_file:
        json_data = json.load(json_file)

    return json_data


def get_tile_set(data):
    url = data["url"]
    name = data["name"]
    if name is not None:
        match name:
            case "Undead++":
                githubTool.getRepo(gh_url=url, path_to_folder=tiles_folder)
            case _:
                githubTool.getRepo(gh_url=url, path_to_folder=tiles_folder)


def get_sound_pack(data):
    url = data["url"]
    name = data["name"]
    if name is not None:
        match name:
            case "CC-Sounds":
                githubTool.get_release(gh_url=url, path_to_folder=sound_folder, release_name="CC-Sounds.zip")
            case _:
                githubTool.getRepo(gh_url=url, path_to_folder=sound_folder)


def get_mods(mod_list):
    for mod in mod_list:
        type = mod["type"]
        url = mod["url"]
        name = mod["name"]
        if name is not None:
            match type:
                case "mod_pack":
                    githubTool.getRepo(gh_url=url, path_to_folder=mods_folder, is_mod_pack=True)
                case "mod":
                    githubTool.getRepo(gh_url=url, path_to_folder=mods_folder)


def main():
    resources = read_json("mods.json")
    # TODO добавить токен для увеличения лимита запросов к гиту или переделать скачивание
    get_tile_set(resources["Tile_set"])
    # get_sound_pack(resources["Sound_pack"])
    get_mods(resources["Mod_list"])


if __name__ == '__main__':
    main()
