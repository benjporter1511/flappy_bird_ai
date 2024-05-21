from concurrent.futures.process import _threads_wakeups
import pip
import pygame as pg
import neat
import time
import os
import random
import pickle
from settings import *
from pipe import Pipe
from base import Base
from bird import Bird

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
    

if __name__ == "__main__":
    fb = FlappyBirdNEAT()
    local_directory = os.path.dirname(__file__)
    config_path = os.path.join(local_directory, "config-feedforward.txt")
    fb.run(config_path)