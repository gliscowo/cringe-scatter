import json
import amtSemVer
import requests

import utils


def upload(url, payload_field, payload, file, token_header, token):
    payload = {payload_field: json.dumps(payload)}
    files = {"file": file}

    print("Sending request...")
    r = requests.post(
        url,
        data=payload, files=files, headers={token_header: token})

    print("Got Response: [" + str(r.status_code) + "] " + r.text)


def upload_modrinth(filename, token, mod_config, metadata_container, debug):
    modrinth_data = {}

    modrinth_data["mod_id"] = mod_config["modrinth_id"]
    modrinth_data["file_parts"] = [filename]
    modrinth_data["version_number"] = metadata_container["version"]
    modrinth_data["version_title"] = utils.format_version_string(mod_config, metadata_container["version"])
    modrinth_data["version_body"] = metadata_container["changelog"]
    modrinth_data["dependencies"] = []
    modrinth_data["game_versions"] = mod_config["minecraft_versions"]
    modrinth_data["release_channel"] = metadata_container["releaseType"]
    modrinth_data["loaders"] = [mod_config["modloader"]]
    modrinth_data["featured"] = True

    if debug:
        print("The following request will be sent to Modrinth: ")
        print(json.dumps(modrinth_data, indent=4))

        abort = input("Proceed? y/n \n")
        if not abort == "y":
            print("Aborting...")
            return

    upload("https://api.modrinth.com/api/v1/version", "data", modrinth_data, open(filename, "rb"), "Authorization", token)


def upload_curseforge(filename, token, mod_config, metadata_container, debug):
    versions = mod_config["minecraft_versions"].copy()
    versions.append(mod_config["modloader"].capitalize())

    if amtSemVer.SemanticVersion.parse(versions[0]).minor >= 17:
        versions.append("Java 16")

    # Get matching minecraft versions from CF
    cf_minecraft_versions = json.loads(
        requests.get("https://minecraft.curseforge.com/api/game/versions?token=" + token).text)
    cf_matching_versions = [element for element in cf_minecraft_versions if
                            element["name"] in versions]

    cf_metadata = {}
    cf_metadata["changelog"] = metadata_container["changelog"]

    cf_version_ids = []
    for element in cf_matching_versions:
        cf_version_ids.append(element["id"])

    cf_metadata["game_versions"] = cf_version_ids

    if debug:
        cf_metadata["displayName"] = utils.format_version_string(mod_config, metadata_container["version"])
        cf_metadata["relations"] = {"projects": mod_config["related_projects"]} if "related_projects" in mod_config else {}

        print("The following request will be sent to CurseForge: ")
        print(json.dumps(cf_metadata, indent=4))

        abort = input("Proceed? y/n \n")
        if not abort == "y":
            print("Aborting...")
            return

    upload("https://minecraft.curseforge.com/api/projects/" + mod_config["curseforge_id"] + "/upload-file", "metadata", cf_metadata, open(filename, "rb"), "X-Api-Token", token)