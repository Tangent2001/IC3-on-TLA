import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

from spec_info import SpecInfo
from file_utils import GEN_TLA_DIR

APALACHE_BIN = None
JVM_ARGS = "JVM_ARGS='-Xss16M'"
SPEC_INFO = None

pool = ThreadPoolExecutor(max_workers=1)

acceptable_return_code = [0, 10, 11, 12, 13, 14]


def find_lines(pattern, output):
    return [ln for ln in output.splitlines() if re.search(pattern, ln)]


def get_state(file_content, i):
    if file_content is None:
        return None
    lines = file_content.strip().splitlines()
    start = lines.index('State' + str(i) + ' ==')
    end = 0
    for i in range(start + 1, len(lines)):
        if not lines[i].strip():
            end = i
            break
    state_str = '\n'.join(lines[start + 1:end + 1])
    return state_str


def get_value(output):
    lines = find_lines(r"State \d+: state invariant \d+ violated.", output)
    return len(lines) == 0


def check_get_file(output):
    lines = find_lines("Output directory:", output)
    res = re.match(r"Output directory: (.+)", lines[0])
    file_dir = res.group(1)
    if not os.path.exists(os.path.join(file_dir, "violation1.tla")):
        return None
    f = open(os.path.join(file_dir, "violation1.tla"))
    file_content = f.read()
    f.close()
    return file_content


def apalache_check(run_dir, init, invariants, length, file):
    args = []
    if isinstance(invariants, list):
        for i in invariants:
            args.append((run_dir, init, i, length, file))
    elif isinstance(invariants, str):
        args.append((run_dir, init, invariants, length, file))
    results = list(pool.map(__apalache_check, args))
    if len(results) == 1:
        return results[0]
    return results


def __apalache_check(arg):
    run_dir = arg[0]
    init = arg[1]
    invariants = arg[2]
    length = arg[3]
    file = arg[4]
    if SPEC_INFO is None:
        raise RuntimeError("SPEC_INFO is not set.")
    if not isinstance(SPEC_INFO, SpecInfo):
        raise RuntimeError("SPEC_INFO is not in correct type.")
    inv_str = ""
    if isinstance(invariants, str):
        inv_str = invariants
    elif isinstance(invariants, list):
        inv_str = ",".join(invariants)
    if APALACHE_BIN is None:
        raise RuntimeError("Didn't set Apalache position.")
    cmd = f"{APALACHE_BIN} check --run-dir={os.path.join(GEN_TLA_DIR, run_dir)} --init={init} " \
          f"--cinit={SPEC_INFO.constants} --inv={inv_str} --length={length} " \
          f"{os.path.join(GEN_TLA_DIR, file)}"
    # result = os.popen(cmd)
    result = subprocess.run(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode("utf-8")
    if result.returncode not in acceptable_return_code:
        raise RuntimeError("Apalache has something wrong.\n" + output)
    return output

