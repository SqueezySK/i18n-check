import cProfile
import pstats
from pstats import SortKey
from unittest.mock import patch

from i18n_check.cli.main import main as cli_main


def cprofile_run():
    profiler = cProfile.Profile()
    profiler.enable()
    with patch("sys.argv", ["i18n-check", "-nsk"]):
        cli_main()
    profiler.disable()
    profiler.dump_stats("profiling/after/cprofile_main_non_source_keys.prof")

    with open("profiling/after/cprofile_main_non_source_keys_pstats.txt", "w") as f:
        stats = pstats.Stats(
            "profiling/after/cprofile_main_non_source_keys.prof", stream=f
        )
        stats.sort_stats(SortKey.CUMULATIVE).print_stats(15)
        stats.sort_stats(SortKey.TIME).print_stats(10)

    # cProfile.run("with patch('sys.argv', ['i18n-check', '--nonexistent-keys']): cli_main()", sort="cumtime")


@patch("sys.exit")
def main(mock_sys_exit):
    cprofile_run()


if __name__ == "__main__":
    main()
