from concurrent.futures.process import _threads_wakeups
import pip
import pygame as pg
import neat
import time
import os
import random
from settings import *

class FlappyBird:
    def __init__(self) -> None:
        pg.init()
        self.window = pg.display.set_mode((WIDTH, HEIGHT))
        self.score = 0

    def draw_window(self, win, bird, pipes, base):
        # draw background
        win.blit(BACKGROUND_IMAGE, (0,0))

        ## draw pipes
        for pipe in pipes:
            pipe.draw(win)

        ## dfraw text for screen
        text = STAT_FONT.render("Score: " + str(self.score), 1, (255, 255, 255))
        win.blit(text, (WIDTH - 10 - text.get_width(), 10))

        ## draw base
        base.draw(win)

        ## draw bird
        bird.draw(win)
        pg.display.update()

    def main(self):
        bird = Bird(230, 350)
        base = Base(730)
        pipes = [Pipe(600)]
        
        clock = pg.time.Clock()

        run = True
        while run:
            clock.tick(30)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    run = False

            # bird.move()

            rem = []
            add_pipe = False

            for pipe in pipes:
                ## check for collision
                if pipe.collide(bird):
                    pass
                
                ## check if pipe is off the screen
                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem.append(pipe)

                ## check if bird has passed the pipe
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

                pipe.move()

            ## since we have passed the pipe we need to add a new one to the list and increment the score
            if add_pipe:
                self.score += 1
                pipes.append(Pipe(600))

            ## remove pipes in removal list
            for r in rem:
                pipes.remove(r)

            ## check if bird has hit the ground
            if bird.y + bird.image.get_height() >= 730:
                pass

            base.move()
            self.draw_window(self.window, bird, pipes, base)

        pg.quit()
        quit()

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


class Base:
    VELOCITY = 5
    WIDTH = BASE_IMAGE.get_width()
    IMAGE = BASE_IMAGE

    def __init__(self, y) -> None:
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        ## idea here is 2 images of base and so they can overlap
        ## as soon as the whole first image has gone off the screen we redraw it back on the right of the screen again
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMAGE, (self.x1, self.y))
        win.blit(self.IMAGE, (self.x2, self.y))


class Bird:
    IMAGES = BIRD_IMAGES
    MAX_ROTATION = 25
    ## bird rotation for tilting
    ROTATION_VELOCITY = 20
    ## how much we rotate on each frame
    ANIMATION_TIME = 5
    ## how long to show each bird animation

    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.velocity = 0
        self.height = self.y
        self.image_count = 0
        self.image = self.IMAGES[0]

    def jump(self):
        ## this will be the vertical velocity given to the bird when we jump
        self.velocity = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        ## tick count is a measure of how long we have been moving since we last jumped
        ## d below will be a measure of translation in the vertical axis
        d = self.velocity * self.tick_count + 1.5 * (self.tick_count**2)
        ## quadratic equation of velocity which will then draw the classic flappy bird arc

        ## worth noting now as time goes on our velocity increase downwards (positive direction due to pygame counting from top left corner) will be exponential
        ## we need to implement some terminal velocity so bird doesnt crash down into ground
        if d >= 16:
            d = 16

        elif d < 0:
            d -= 2

        self.y += d

        ## now deal with tilting of the bird sprite
        ## for tilt up check if bird is moving up or is above place where jump was initiated
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VELOCITY

    def draw(self, win):
        self.image_count += 1

        ## handling animation of the bird
        if self.image_count < self.ANIMATION_TIME:
            self.image = self.IMAGES[0]
        elif self.image_count < self.ANIMATION_TIME * 2:
            self.image = self.IMAGES[1]
        elif self.image_count < self.ANIMATION_TIME * 3:
            self.image = self.IMAGES[2]
        elif self.image_count < self.ANIMATION_TIME * 4:
            self.image = self.IMAGES[1]
        elif self.image_count == self.ANIMATION_TIME * 4 + 1:
            self.image = self.IMAGES[0]
            self.image_count = 0

        ## we dont want to use flapping animation if bird is in freefall
        ## we can check the tilt
        if self.tilt <= -80:
            self.image = self.IMAGES[1]
            ## imaghe of bird with level wings
            self.image_count = self.ANIMATION_TIME * 2

        ## rotate image around the centre
        rotated_image = pg.transform.rotate(self.image, self.tilt)
        new_rectange = rotated_image.get_rect(center=self.image.get_rect(topleft = (self.x, self.y)).center)

        ## blit rotated image onto window
        win.blit(rotated_image, new_rectange.topleft)

    def get_mask(self):
        return pg.mask.from_surface(self.image)
    
fb = FlappyBird()
fb.main()