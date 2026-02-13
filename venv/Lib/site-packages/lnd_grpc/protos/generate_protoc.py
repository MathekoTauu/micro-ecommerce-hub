import os
from pathlib import Path
from grpc_tools import protoc


def generate_msgs():

    change_working_directory()

    protoc.main(
        (
            "",
            "--proto_path=lnd_grpc/protos/googleapis:.",
            "--python_out=.",
            "--grpc_python_out=.",
            "lnd_grpc/protos/rpc.proto",
        )
    )


def change_working_directory():
    # change working directory up two levels for proper proto imports
    p = Path(Path.cwd())
    # print(f"original WD: {p}")
    os.chdir(p.parent.parent)
    # print(f"new WD: {Path.cwd()}")


if __name__ == "__main__":
    generate_msgs()
