# Quarto

[Quarto](https://en.wikipedia.org/wiki/Quarto_(board_game)) is a 2-player strategy board game.

With [quarto.py](quarto.py), you can play against a computer playing at random.

With [quarto_multi.py](quarto_multi.py), you can play against another human through an MQTT broker.

## Rules

To win, a player must align 4 pieces with a common characteristics. Each piece has a color (blue or red), a shape (square or circle), a size (small or big) and a top (solid or hollow).

The first player selects a piece that the second has to place in the grid. Then the second player selects a piece for the first one. This process continues until all pieces have been placed or a player wins.

## Requirements

- Python 3 or higher
- Python modules: `pygame`
- For the [LAN version](quarto_multi.py) only:
  - An additional module is required: `paho-mqtt`
  - An MQTT broker must be set up and accessible by both players.
  - Change the IP address in `Client.__init__` to the address of the broker.