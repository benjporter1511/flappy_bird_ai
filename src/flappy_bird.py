from concurrent.futures.process import _threads_wakeups
import pip
import pygame as pg
import neat
import time
import os
import random
import pickle
from settings import *

class FlappyBirdNEAT:
    def __init__(self) -> None:
        pg.init()
        self.window = pg.display.set_mode((WIDTH, HEIGHT))
        self.score = 0

    def draw_window(self, win, birds, pipes, base):
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

        for bird in birds:
            ## draw birds
            bird.draw(win)
        pg.display.update()

    def main(self, genomes, config):
        ## fitness function for algorithm
        nets = []
        ge = []
        ## make our population of birds in one game
        birds = []

        ## genomes is a tuple that looks like (1, g) with id and actual genome object
        for _, g in genomes:
            ## for each genome we set up a neural network, with a corresponding bird object and genome 
            ## also setting all fitness values to 0
            net = neat.nn.FeedForwardNetwork.create(g, config)
            nets.append(net)
            birds.append(Bird(203, 350))
            g.fitness = 0
            ge.append(g)


        base = Base(730)
        pipes = [Pipe(600)]
        
        clock = pg.time.Clock()

        run = True
        while run:
            clock.tick(30)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    run = False
                    pg.quit()
                    quit()


            ## There is the possibility of there being two pipes on screen at one time when the game is running
            ## we want to be able to specify which pipe we want to be measuring against for the neural network
            ## to do this we can check:
            ## 1. are are there any birds left we are measuring
            ## 2. is there more than 2 pipes on screen
            ## 3. is our birds x position past the x position of the end of the first pipe (i.e. has the bird completely moved past the first pipe on screen in which case we want to measure using the second one)
            pipe_ind = 0
            if len(birds) > 0:
                if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                    pipe_ind = 1
            else:
                ## no birds left so we want to quit this generation
                run = False
                break

            ## MOVE OUR BIRDS :)
            for x, bird in enumerate(birds):
                bird.move()
                ## give the bird some fitness score for successfully moving ahead slightly
                ge[x].fitness += 0.1
                ## the value is small here because this loop should run 30 times a second

                ## output will be our node with output
                ## activate will take in the input nodes which for us will be 
                ## 1. birds y position (bird height on the screen)
                ## 2. vertical distance from bird to top pipe
                ## 3. vertical distance from bird to bottom pipe
                output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

                if output[0] > 0.5:
                    bird.jump()

            rem = []
            add_pipe = False

            for pipe in pipes:
                for bird in birds:
                    ## check for collision
                    if pipe.collide(bird):
                        ## this is where birds will fail in the algorithm, we want to remove them here and make sure the fitness score at this point is set and does not change
                        ## we add this as we want to favour birds who make it a distance without just flying right into a pipe
                        ge[birds.index(bird)].fitness -= 1
                        nets.pop(birds.index(bird))
                        ge.pop(birds.index(bird))
                        birds.pop(birds.index(bird))

                    ## check if bird has passed the pipe
                    if not pipe.passed and pipe.x < bird.x:
                        pipe.passed = True
                        add_pipe = True

                ## check if pipe is off the screen
                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem.append(pipe)

                pipe.move()

            ## since we have passed the pipe we need to add a new one to the list and increment the score
            if add_pipe:
                self.score += 1
                ## if bird gets through the pipe we will improve the fitness score by a good amount
                ## this is to incentivise birds that make a good distance but also by getting through pipes
                for g in ge:
                    g.fitness += 5
                pipes.append(Pipe(600))

            ## remove pipes in removal list
            for r in rem:
                pipes.remove(r)

            for bird in birds:
                ## check if bird has hit the ground or ceiling
                if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
                    ## again want to remove birds here but without the penalty to fitness as they will have just hit the ground
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            ## set 50 as our threshold for winning bird AI
            if self.score > 50:
                break

            base.move()
            self.draw_window(self.window, birds, pipes, base)

    def run(self, config_path):
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

        ## popluation
        p = neat.Population(config)

        ## stats reporters
        p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        p.add_reporter(stats)

        ## set fitness function for 50 generations
        winner = p.run(self.main, 50)

        ## save winning genome
        with open("winner.pkl", "wb") as f:
            pickle.dump(winner, f)
            f.close()
        

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
    

if __name__ == "__main__":
    fb = FlappyBirdNEAT()
    local_directory = os.path.dirname(__file__)
    config_path = os.path.join(local_directory, "config-feedforward.txt")
    fb.run(config_path)