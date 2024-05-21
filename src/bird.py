from settings import *

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