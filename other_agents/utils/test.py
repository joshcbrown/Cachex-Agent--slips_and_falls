import pandas as pd
import numpy as np
from referee.game import play
from datetime import datetime


def test(options, p1, p2):
    if options.test_range is None:
        board_sizes = range(options.n, options.n + 1)
    elif options.test_range == "all":
        board_sizes = range(3, 16)
    elif options.test_range == "small":
        board_sizes = range(3, 9)
    elif len(options.test_range.split()) == 2:
        lower, upper = [int(bound) for bound in options.test_range.split()]
        board_sizes = range(lower, upper + 1)
    else:
        print("test range is invalid. exiting")
        exit()
    num_sizes = len(board_sizes)
    p1_red_wins = np.zeros(num_sizes, dtype=np.int)
    p2_blue_wins = np.zeros(num_sizes, dtype=np.int)
    p2_red_wins = np.zeros(num_sizes, dtype=np.int)
    p1_blue_wins = np.zeros(num_sizes, dtype=np.int)
    csv_str = f'stats/{options.player1_loc[0]}_vs_{options.player2_loc[0]}_{datetime.now().strftime("%H:%M:%S")}.csv'
    for row, n in enumerate(board_sizes):
        for i in range(options.testing_rounds):
            result1 = play(
                [p1, p2],
                n=n,
                delay=options.delay,
                print_state=(options.verbosity > 1),
                use_debugboard=(options.verbosity > 2),
                use_colour=options.use_colour,
                use_unicode=options.use_unicode,
                log_filename=options.logfile,
            )
            result2 = play(
                [p2, p1],
                n=n,
                delay=options.delay,
                print_state=(options.verbosity > 1),
                use_debugboard=(options.verbosity > 2),
                use_colour=options.use_colour,
                use_unicode=options.use_unicode,
                log_filename=options.logfile,
            )
            if result1 == "winner: blue":
                p2_blue_wins[row] += 1
            else:
                p1_red_wins[row] += 1
            if result2 == "winner: blue":
                p1_blue_wins[row] += 1
            else:
                p2_red_wins[row] += 1
        df = save_results(options, board_sizes, csv_str, p1_red_wins, p1_blue_wins, p2_red_wins, p2_blue_wins)
    print(
        f"{options.player1_loc[0]}1 acc: {df[f'total_{options.player1_loc[0]}1'].sum() / (2 * options.testing_rounds * num_sizes)}\n"
        f"{options.player2_loc[0]}2 acc: {df[f'total_{options.player2_loc[0]}2'].sum() / (2 * options.testing_rounds * num_sizes)}")


def save_results(options, board_sizes, csv_str, p1_red_wins, p1_blue_wins, p2_red_wins, p2_blue_wins):
    df = pd.DataFrame(
        data={
            f'red_{options.player1_loc[0]}1': p1_red_wins,
            f'blue_{options.player1_loc[0]}1': p1_blue_wins,
            f'red_{options.player2_loc[0]}2': p2_red_wins,
            f'blue_{options.player2_loc[0]}2': p2_blue_wins,
            f'total_{options.player1_loc[0]}1': p1_red_wins + p1_blue_wins,
            f'total_{options.player2_loc[0]}2': p2_red_wins + p2_blue_wins
        },
        index=pd.Series(board_sizes, name="n")
    )
    df.to_csv(csv_str)
    return df
