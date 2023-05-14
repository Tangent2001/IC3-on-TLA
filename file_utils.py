import os

GEN_TLA_DIR = "gen_tla"
BENCHMARK = "benchmarks"


def write_gen_tla(name: str, content: str):
    dir_name = GEN_TLA_DIR
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    file = f"{os.path.join(GEN_TLA_DIR, name)}"
    f = open(file, 'w')
    f.write(content)
    f.close()


def copy_original_file(name: str):
    # 将原协议复制到工作区(gen_tla)
    copy_cmd = f"cp {os.path.join(BENCHMARK, name)} " \
               f"{os.path.join(GEN_TLA_DIR, name)}"
    os.popen(copy_cmd)

