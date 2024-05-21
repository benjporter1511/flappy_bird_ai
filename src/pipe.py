import pygame as pg
import random
from settings import *

class Pipe:
    GAP = 200
    VELOCITY = 5

    def __init__(self, x) -> None:
        self.x = x
        self.height = 0
        self.y_gap = 100

        ## we will be considering both top and bottom pipe as one combined object
        ## these are locations from top left of image (as per pygame) of top and bottom pipes
        self.top = 0
        self.bottom = 0

        ## top and bottom pipe images
        self.PIPE_TOP = pg.transform.flip(PIPE_IMAGE, False, True)
        self.PIPE_BOTTOM = PIPE_IMAGE

        # have we passed the pipe yet?
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        ## move pipes from right to left instead of moving bird
        self.x -= self.VELOCITY

    def draw(self, win):
        ## drows both top and bottom pipe, we are counting them as one thing
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    ## using masks to do pixel perfect collison
    ## mask can look at image and create list of pixels 
    def collide(self, bird):
        bird_mask = bird.get_mask()

        ## create masks for top and bottom pipe
        top_mask = pg.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pg.mask.from_surface(self.PIPE_BOTTOM)

        ## calculate offset which is how far one mask is from another
        
        ## offset from bird to top pipe
        top_offset = (self.x - bird.x, self.top - round(bird.y)) ## can't have decimals here
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset) ## if no collision this function returns None
        top_point = bird_mask.overlap(top_mask, top_offset)

        if top_point or bottom_point:
            ## we have collision
            return True
        
        return False