import datetime
import sys
import subprocess
import pathlib
import shlex
import json
import argparse
from typing import Optional, TypedDict, cast

CONF_PATH = pathlib.Path("s3-project-backup.json")
GLOBAL_CONF_PATH = (
    pathlib.Path("~", ".config", "s3-project-backup").expanduser() / CONF_PATH
)
EXCLUDE_ITEMS = [
    ".gitignore",
    "s3-project-backup.json",
    "s3-project-backup.py",
    "_DS_Store",
]
DUPLICATED_ITEMS = ["README.md"]

GIT_IGNORE = """
/*
!.gitignore
!README.md
!s3-project-backup.json
"""


class Config(TypedDict):
    aws_profile: str
    s3_bucket: str
    s3_path_prefix: str
    s3_storage_class: str


def run_command(cmd: list[str]):
    print("$", shlex.join(cmd))
    subprocess.run(cmd, check=True, text=True)


def load_conf() -> Config:
    if not CONF_PATH.exists():
        raise Exception("s3-project-backup.json not found")

    with CONF_PATH.open("r", encoding="UTF-8") as f:
        return cast(Config, json.load(f))


def load_global_conf() -> Optional[Config]:
    if not GLOBAL_CONF_PATH.exists():
        return None

    with GLOBAL_CONF_PATH.open("r", encoding="UTF-8") as f:
        return cast(Config, json.load(f))


def build_s3_path(conf: Config) -> str:
    return f"s3://{conf['s3_bucket']}/{conf['s3_path_prefix']}/"


def check_no_local_files() -> bool:
    for d in pathlib.Path(".").glob("*"):
        if d.name not in EXCLUDE_ITEMS and d.name not in DUPLICATED_ITEMS:
            return False
    return True


def check_no_conf() -> bool:
    return CONF_PATH.exists()


def upload(dryrun: bool = False):
    conf = load_conf()
    s3_path = build_s3_path(conf)

    print(f"upload from local directory to {s3_path} .")

    cmd = [
        "aws",
        f"--profile={conf['aws_profile']}",
        "s3",
        "sync",
        ".",
        s3_path,
        f"--storage-class={conf['s3_storage_class']}",
        "--delete",
    ] + [f"--exclude={e}" for e in EXCLUDE_ITEMS]

    if dryrun:
        cmd.append("--dryrun")

    run_command(cmd)


def download(dryrun: bool):
    conf = load_conf()
    s3_path = build_s3_path(conf)

    print(f"download from {s3_path} to local directory.")

    cmd = [
        "aws",
        f"--profile={conf['aws_profile']}",
        "s3",
        "sync",
        s3_path,
        ".",
        "--delete",
    ] + [f"--exclude={e}" for e in EXCLUDE_ITEMS]

    if dryrun:
        cmd.append("--dryrun")

    run_command(cmd)


def init():
    if CONF_PATH.exists():
        print("s3-project-backup.json already exists")
        sys.exit(1)

    conf = load_global_conf()
    if conf is None:
        conf = {
            "aws_profile": "",
            "s3_bucket": "",
            "s3_path_prefix": "",
            "s3_storage_class": "",
        }

    if conf["aws_profile"] == "":
        conf["aws_profile"] = input("aws profile: ")

    if conf["s3_bucket"] == "":
        conf["s3_bucket"] = input("s3 bucket name: ")

    if conf["s3_path_prefix"] == "":
        yyyymmdd = datetime.datetime.now().strftime("%Y%m%d")
        dir_name = pathlib.Path(".").resolve().name
        default_prefix = f"{yyyymmdd}-{dir_name}"

        conf["s3_path_prefix"] = input(f's3 path prefix (default:\"{default_prefix}\"): ')

        if conf["s3_path_prefix"] == "":
            conf["s3_path_prefix"] = default_prefix

    if conf["s3_storage_class"] == "":
        conf["s3_path_prefix"] = input("s3 storage class: ")

    with CONF_PATH.open("w", encoding="UTF-8") as f:
        json.dump(conf, f, indent=2)

    with pathlib.Path(".gitignore").open("w", encoding="UTF-8") as f:
        f.write(GIT_IGNORE)

    if not pathlib.Path("README.md").exists():
        with pathlib.Path("README.md").open("w", encoding="UTF-8") as f:
            f.writelines([f"# s3://{conf['s3_bucket']}/{conf['s3_path_prefix']}\n", ""])

    print("created s3-project-backup.json")


def run():
    parser = argparse.ArgumentParser(description="simple s3 directory backup")
    parser.add_argument(
        "command",
        type=str,
        help="command: init, delete-local, download, upload",
        nargs="?",
        default="",
    )
    parser.add_argument(
        "-d",
        action="store_true",
        help="dry run",
    )
    args = parser.parse_args()
    command = args.command

    if command == "":
        if check_no_local_files():
            command = "download"
        else:
            command = "upload"

    if command == "init":
        init()
        return

    if not check_no_conf():
        print("s3-project-backup.json not found.")
        print("please run `s3-project-backup init` .")
        sys.exit(1)

    if command == "download":
        download(dryrun=args.d)
    if command == "upload":
        upload(dryrun=args.d)
    if command == "init":
        init()


if __name__ == "__main__":
    run()
