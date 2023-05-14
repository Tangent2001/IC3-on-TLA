import argparse
import os

import apalache_utils
import file_utils
from ic3 import IC3
from spec_info import SpecInfo
from tla_rel_dict import TLARelDict
import time


if __name__ == '__main__':
    # 处理命令行参数
    start_time = time.time()
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--spec', help="Name of the protocol benchmarks to run (given as 'benchmarks/<spec_name>').",
                        required=True, type=str)

    args = vars(parser.parse_args())

    spec_info = SpecInfo(args)
    apalache_utils.APALACHE_BIN = os.getenv("apalache-mc")
    apalache_utils.SPEC_INFO = spec_info

    file_utils.copy_original_file(spec_info.spec_name + '.tla')

    rel_dict = TLARelDict(spec_info)

    algorithm = IC3(rel_dict, spec_info)
    algorithm.fol_ic3()
    end_time = time.time()
    run_time = end_time - start_time
    print("It takes {} seconds to get the inductive invariants".format(run_time))

