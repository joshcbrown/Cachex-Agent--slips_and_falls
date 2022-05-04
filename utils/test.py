import pandas as pd
import numpy as np
from tqdm import trange
from referee.game import play
from datetime import datetime


def test(options, p1, p2):
    if options.test_all:
        board_sizes = trange(3, 16)
    else:
        board_sizes = range(options.n, options.n + 1)
    num_sizes = len(board_sizes)
    p1_red_wins = np.zeros(num_sizes, dtype=np.int)
    p2_blue_wins = np.zeros(num_sizes, dtype=np.int)
    p2_red_wins = np.zeros(num_sizes, dtype=np.int)
    p1_blue_wins = np.zeros(num_sizes, dtype=np.int)
    for n in board_sizes:
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
                p2_blue_wins[n - 3] += 1
            else:
                p1_red_wins[n - 3] += 1
            if result2 == "winner: blue":
                p1_blue_wins[n - 3] += 1
            else:
                p2_red_wins[n - 3] += 1
    df = pd.DataFrame(
        data={
            'red_1': p1_red_wins, 
            'blue_1': p1_blue_wins, 
            'red_2': p2_red_wins, 
            'blue_2': p2_blue_wins,
            'total_1': p1_red_wins + p1_blue_wins,
            'total_2': p2_red_wins + p2_blue_wins
        },
        index=pd.Series(board_sizes, name="n")
    )
    df.to_csv(f'results-{datetime.now().strftime("%H:%M:%S")}.csv')
    print(df)
    print(f"p1 acc: {df['total_1'].sum() / (2 * options.testing_rounds * num_sizes)}\n"
          f"p2 acc: {df['total_2'].sum() / (2 * options.testing_rounds * num_sizes)}")
