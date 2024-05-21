"""
Settings contained here.
"""
import pygame as pg
pg.font.init()

WIDTH = 550
HEIGHT = 800

BIRD_IMAGES = [
    ## load bird images from image folder and double the size
    pg.transform.scale2x(pg.image.load(r'D:\projects\pygame\flappy_bird_ai\src\images\bird1.png')),
    pg.transform.scale2x(pg.image.load(r'D:\projects\pygame\flappy_bird_ai\src\images\bird2.png')),
    pg.transform.scale2x(pg.image.load(r'D:\projects\pygame\flappy_bird_ai\src\images\bird3.png'))
]

## other sprites
PIPE_IMAGE = pg.transform.scale2x(pg.image.load(r'D:\projects\pygame\flappy_bird_ai\src\images\pipe.png'))
BASE_IMAGE = pg.transform.scale2x(pg.image.load(r'D:\projects\pygame\flappy_bird_ai\src\images\base.png'))
BACKGROUND_IMAGE = pg.transform.scale2x(pg.image.load(r'D:\projects\pygame\flappy_bird_ai\src\images\bg.png'))

STAT_FONT = pg.font.SysFont("comicsans", 50)