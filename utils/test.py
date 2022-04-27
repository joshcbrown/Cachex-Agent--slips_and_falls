import pandas as pd
import numpy as np
from referee.game import play
from datetime import datetime


def test(options, p1, p2):
    red_wins = np.zeros(13, dtype=np.int)
    blue_wins = np.zeros(13, dtype=np.int)
    for n in range(3, 16):
        for i in range(options.testing_rounds):
            result = play(
                [p1, p2],
                n=options.n,
                delay=options.delay,
                print_state=(options.verbosity > 1),
                use_debugboard=(options.verbosity > 2),
                use_colour=options.use_colour,
                use_unicode=options.use_unicode,
                log_filename=options.logfile,
            )
            if result == "winner: blue":
                blue_wins[n - 3] += 1
            else:
                red_wins[n - 3] += 1
    print(f"{red_wins=}\n{blue_wins=}")
    df = pd.DataFrame(data={'red': red_wins, 'blue': blue_wins}, index=pd.Series(range(3, 16), name="n"))
    df.to_csv(f'results-{datetime.now().strftime("%H:%M:%S")}.csv')
    print(df)
    print(f"blue acc: {df['blue'].sum() / (options.testing_rounds * 13)}"
          f"red acc: {df['red'].sum() / (options.testing_rounds * 13)}")
