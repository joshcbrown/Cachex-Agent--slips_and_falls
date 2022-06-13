# Champion Cachex Agent
## A game playing agent for 'Cachex', a variant of 'Hex'

This project was completed as part of the subject `AI` (COMP30024). 128 teams
of 2 submitted an agent to the tournament, and this was the winner!

![Trophy](./trophy.png)

Our approach was based on Negamax, with several optimisations to reduce the 
search space and prune the Negamax-tree, including transposition tables using
Zobrist hash keys. Our report describing our full process can be found [here](https://github.com/ljdoig/Cachex-Agent/blob/main/report.pdf).

The game itself is identical to [Hex](https://en.wikipedia.org/wiki/Hex_(board_game)), except that opponent pieces may be captured.
