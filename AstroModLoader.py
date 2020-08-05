import os
import numpy
import shutil
import json
from terminaltables import SingleTable
from PyPAKParser import PakParser

import cogs.AstroAPI as AstroAPI


class AstroModLoader():

    def __init__(self):
        print("Astro mod loader v0.1")

        # configure and store used paths
        self.downloadPath = os.getcwd()
        if not os.path.exists(os.path.join(self.downloadPath, "mods")):
            os.makedirs(os.path.join(self.downloadPath, "mods"))
        self.downloadPath = os.path.join(self.downloadPath, "mods")

        self.installPath = os.path.join(
            os.getenv('LOCALAPPDATA'), "Astro", "Saved")
        if not os.path.exists(os.path.join(self.installPath, "Paks")):
            os.makedirs(os.path.join(self.installPath, "Paks"))
        self.installPath = os.path.join(self.installPath, "Paks")

        if not os.path.exists(os.path.join(self.downloadPath, "modconfig.json")):
            with open(os.path.join(self.downloadPath, "modconfig.json"), 'w') as f:
                f.write('{"mods":[]}')

        self.modConfig = {}
        with open(os.path.join(self.downloadPath, "modconfig.json"), 'r') as f:
            self.modConfig = json.loads(f.read())

        # gather mod list (only files)
        print("gathering mod data...")
        self.mods = numpy.unique(self.getPaksInPath(
            self.downloadPath) + self.getPaksInPath(self.installPath))

        self.mods = list(map(lambda m: {"filename": m}, self.mods))

        def readModData(mod):
            # check mod if it is installed
            mod["installed"] = os.path.isfile(
                os.path.join(self.installPath, mod["filename"]))

            # copy mods only install dir to download dir
            if not os.path.isfile(os.path.join(self.downloadPath, mod["filename"])):
                shutil.copyfile(os.path.join(
                    self.installPath, mod["filename"]), os.path.join(self.downloadPath, mod["filename"]))

            # read metadata
            mod["metadata"] = {}
            metadata = self.getMetadata(os.path.join(
                self.downloadPath, mod["filename"]))

            if "name" in metadata:
                mod["metadata"]["name"] = metadata["name"]
            else:
                mod["metadata"]["name"] = mod["filename"]

            if "mod_id" in metadata:
                mod["metadata"]["mod_id"] = metadata["mod_id"]
            else:
                mod["metadata"]["mod_id"] = mod["filename"].split("_")[
                    0].split("-")[1]

            if "author" in metadata:
                mod["metadata"]["author"] = metadata["author"]
            else:
                mod["metadata"]["author"] = ""

            if "description" in metadata:
                mod["metadata"]["description"] = metadata["description"]
            else:
                mod["metadata"]["description"] = ""

            if "version" in metadata:
                mod["metadata"]["version"] = metadata["version"]
            else:
                if len(mod["filename"].split("_")[0].split("-")) == 3:
                    mod["metadata"]["version"] = mod["filename"].split("_")[
                        0].split("-")[2]
                else:
                    mod["metadata"]["version"] = "---"

            if "astro_build" in metadata:
                mod["metadata"]["astro_build"] = metadata["astro_build"]
            else:
                mod["metadata"]["astro_build"] = "1.13.129.0"

            if "priority" in metadata:
                mod["metadata"]["priority"] = metadata["priority"]
            else:
                mod["metadata"]["priority"] = mod["filename"].split("_")[
                    0].split("-")[0]

            if "sync" in metadata:
                mod["metadata"]["sync"] = metadata["sync"]
            else:
                mod["metadata"]["sync"] = "serverclient"

            if "homepage" in metadata:
                mod["metadata"]["homepage"] = metadata["homepage"]
            else:
                mod["metadata"]["homepage"] = ""

            if "download" in metadata:
                mod["metadata"]["download"] = metadata["download"]
            else:
                mod["metadata"]["download"] = {}

            if "linked_actor_components" in metadata:
                mod["metadata"]["linked_actor_components"] = metadata["linked_actor_components"]
            else:
                mod["metadata"]["linked_actor_components"] = []

            # read data from modconfig.json
            config = list(
                filter(lambda m: m["mod_id"] == mod["metadata"]["mod_id"], self.modConfig["mods"]))
            if len(config):
                config = config[0]
                if "update" in config:
                    mod["update"] = config["update"]
                else:
                    mod["update"] = True

                if "always_active" in config:
                    mod["always_active"] = config["always_active"]
                else:
                    mod["always_active"] = False
            else:
                mod["update"] = True
                mod["always_active"] = False

            return mod
        print("parsing metadata...")
        self.mods = list(map(readModData, self.mods))

        # print(self.mods)

        # TODO download updates

        while True:
            # clear install path
            for pak in self.getPaksInPath(self.installPath):
                os.remove(os.path.join(self.installPath, pak))

            # TODO do mod integration

            # load all previously active mods back into mod path (with changes)
            for mod in self.mods:
                if mod["installed"] or mod["always_active"]:
                    shutil.copyfile(os.path.join(
                        self.downloadPath, mod["filename"]), os.path.join(self.installPath, mod["filename"]))

            # write modconfig.json
            config = []
            for mod in self.mods:
                config.append({
                    "mod_id": mod["metadata"]["mod_id"],
                    "update": mod["update"],
                    "always_active": mod["always_active"]
                })
            with open(os.path.join(self.downloadPath, "modconfig.json"), 'r+') as f:
                f.truncate(0)
            with open(os.path.join(self.downloadPath, "modconfig.json"), 'w') as f:
                f.write(json.dumps({"mods": config}))

            # list mods and commands
            tabelData = []
            tabelData.append(
                ["active", "mod name", "version", "author", "mod id", "update", "always active"])

            for mod in self.mods:
                tabelData.append([
                    mod["installed"],
                    mod["metadata"]["name"],
                    mod["metadata"]["version"],
                    mod["metadata"]["author"],
                    mod["metadata"]["mod_id"],
                    mod["update"],
                    mod["always_active"]
                ])

            table = SingleTable(tabelData, "Available mods")
            print("")
            print(table.table)
            print("commands: exit, (activate, deactivate, server)")

            # TODO start cli for moving mods and server config
            cmd = input("> ")

            if cmd == "exit":
                break

        print("exiting...")

    def getPaksInPath(self, path):
        paks = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)) and os.path.splitext(os.path.join(path, f))[1] == ".pak":
                paks.append(f)
        return paks

    def getMetadata(self, path):
        PP = PakParser(path)
        metadataFile = [
            x.Data for x in PP.records if x.fileName == "metadata.json"]

        if len(metadataFile) > 0:
            return json.loads(metadataFile[0])
        else:
            return {}


if __name__ == "__main__":
    try:
        os.system("title AstroLauncher - Unofficial Dedicated Server Launcher")
    except:
        pass
    try:
        AstroModLoader()
    except KeyboardInterrupt:
        pass
    # except Exception as err:
     #   print("ERROR")
      #  print(err)
