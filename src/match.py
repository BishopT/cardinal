import math
import json


class Match():

    def __init__(self, bo, blue_team, red_team):
        self.bo = bo
        self.blue_team = blue_team
        self.red_team = red_team
        self.blue_score: int = []
        self.red_score: int = []
        self.bo_blue_score = 0
        self.bo_red_score = 0
        self.ended = False

    def __repr__(self):
        return f'{self.blue_team} : {self.bo_blue_score} - {self.bo_red_score} : {self.red_team}'

    def __json__(self, **options):
        return {self.blue_team: self.bo_blue_score, self.red_team: self.bo_red_score}

    def add_game_result(self, blue_score, red_score):
        if (len(self.blue_score) < bo & self.ended):
            self.blue_score.append(blue_score)
            self.red_score.append(red_score)
        else:
            raise Exception("BO is over, cannot add more games.")

    def set_result(self, game, blue_score, red_score):
        self.blue_score[game - 1] = blue_score
        self.red_score[game - 1] = red_score

    def get_result(self):
        return [self.blue_team, self.blue_score,
                self.red_team, self.red_score,
                self.get_winner()]

    def compute_bo(self):
        self.bo_blue_score = 0
        self.bo_red_score = 0
        for i in len(blue_score):
            self.bo_blue_score += 1 if (blue_score > red_score) else 0
            self.bo_red_score += 1 if (red_score > blue_score) else 0
        if self.bo_blue_score == math.ceil(self.bo / 2):
            self.ended = True

    def get_winner(self):
        if (self.bo_blue_score == self.bo_red_score):
            return None
        if (self.bo_blue_score > self.bo_red_score):
            return self.blue_team
        else:
            return self.red_team
