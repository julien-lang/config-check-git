
import argparse
import logging
import os
import subprocess
import urllib.parse
import yaml

def main():
    excluded_components = {
        "tk-framework-lmv":  "v0.",
        "tk-framework-shotgunutils": "v4.",
        "tk-framework-widget": "v0.",
    }

    ssh_components = [
        "tk-flame-projectconnect",
    ]

    lh = logging.StreamHandler()
    lh.setLevel(logging.DEBUG)
    #lh.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    lh.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger()
    logger.addHandler(lh)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("--folder")
    parser.add_argument("--debug", "-d", action="store_true", default=False)
    parser.add_argument("--show-files", action="store_true", default=False)
    args = parser.parse_args()

    if not args.folder:
       args.folder = os.path.abspath(os.path.curdir)

    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    changes = []
    for yml_file in find_yml_files(args.folder):
        if args.show_files:
            logger.debug("File: {}".format(yml_file))

        data = yaml.safe_load(open(yml_file))
        for item in find_location_entry(data):
            name = os.path.basename(item["path"]) if "path" in item else item["name"]
            if name.endswith(".git"):
                name = name[:-4]

            logger.debug("")
            logger.debug("[{}]".format(name))
            if item["type"] != "git_branch":
                if item["type"] == "app_store" and item["version"].startswith(excluded_components.get(item["name"], "__invalid__")):
                    logger.debug("Ignore {name} - {version}".format(**item))
                else:
                    logger.error("Error: item should be git_branch {}".format(item))

                continue

            if name in ssh_components:
                u =  urllib.parse.urlparse(item["path"])
                repo_url = "git@{hostname}:{path}".format(
                    hostname = u.hostname,
                    path = u.path[1:], # remove leading /
                )
            else:
                repo_url = item["path"]

            p = subprocess.run(
                ["git", "ls-remote", repo_url, item["branch"]],
                check=True, capture_output=True
            )

            out = p.stdout.decode()
            commit = out[: out.find("\t")]
            if item["version"] == commit:
                logger.debug("Up-to-date; nothing to do")
                continue

            logger.debug("New commit: {}".format(commit))
            changes.append(dict(item))
            changes[-1]["my_name"] = name
            changes[-1]["commit_hash"] = commit
            changes[-1]["file"] = yml_file

    logger.debug("")
    files_changed = set()
    for item in changes:
        print(
            "Repo {my_name}\n"
            "  Old commit: {version}\n"
            "  New commit: {commit_hash}\n"
            "".format(**item),
        )
        files_changed.add(yml_file)

    print("Number of file changed:", len(files_changed))
    for filename in sorted(files_changed):
        print("  ", filename)


def find_location_entry(data):
    if not isinstance(data, dict):
        return

    for key in data:
        if not isinstance(data[key], dict):
            continue

        if key == "location" or key.endswith(".location"):
            yield data[key]
        else:
            yield from find_location_entry(data[key])


def find_yml_files(root_dir):
    for (root,dirs,files) in os.walk(root_dir):
        if root.startswith(os.path.join(root_dir, ".git")):
            continue

        for filename in files:
            if filename.endswith(".yml"):
                yield os.path.join(root, filename)


if __name__ == "__main__":
    main()
