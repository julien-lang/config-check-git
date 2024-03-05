
import os
import sys
import subprocess
import yaml

def main():
   
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder")
    args = parser.parse_args()

    if not args.folder:
       args.folder = os.path.abspath(os.path.dirname(__file__))

    files_changed = []
    for yml_file in find_yml_files(args.folder):
        #print("File:", yml_file)
        file_need_update = False

        data = yaml.safe_load(open(yml_file))
        for item in find_location_entry(data):
            #print("item:", item)
            if item["type"] != "git_branch":
                continue
                print("Error: item should be git_branch", item)
                sys.exit(1)

            p = subprocess.run(
                ["git", "ls-remote", item["path"], item["branch"]],
                check=True, capture_output=True
            )

            out = p.stdout.decode()
            commit = out[: out.find("\t")]
            if item["version"] == commit:
                # nothing to do
                continue

            # Must update
            file_need_update = True
            print(
                "Repo {r}\nOld commit: {c1}\nNew commit: {c2}".format(
                    r=os.path.basename(item["path"]),
                    c1 = item["version"],
                    c2 = commit,
                )
            )
            item["version"] = commit

        if file_need_update:
            files_changed.append(yml_file)

    print()
    print("Number of file changed:", len(files_changed))
    for i in files_changed:
        print("  ", i)


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
