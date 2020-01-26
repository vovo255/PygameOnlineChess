class TurnLogger:
    def __init__(self):
        self.w_turns = []
        self.b_turns = []

    def get_turns(self):
        turns = []
        for i in range(len(self.w_turns)):
            try:
                turn = '{}. {} - {}'.format(str(i + 1), self.w_turns[i],
                                            self.b_turns[i])
            except IndexError:
                turn = '{}. {}'.format(str(i + 1), self.w_turns[i])
            turns.append(turn)
        return turns

    def register_turn(self, color, turn):
        if color == 'w':
            self.w_turns.append(turn[:2] + '-' + turn[2:])
        elif color == 'b':
            self.b_turns.append(turn[:2] + '-' + turn[2:])
