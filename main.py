#importing needed modules
import pygame
import neat
import time
import random
import os
#setting up size of the window
WIN_WIDTH = 500
WIN_HEIGHT = 800
#variable for generation
gen = 0
#importing the images
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load('imgs/bird1.png')), pygame.transform.scale2x(pygame.image.load('imgs/bird2.png')), pygame.transform.scale2x(pygame.image.load('imgs/bird3.png'))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load('imgs/pipe.png'))
BASE_IMG = pygame.transform.scale2x(pygame.image.load('imgs/base.png'))
BG_IMG = pygame.transform.scale2x(pygame.image.load('imgs/bg.png'))
ICON = pygame.image.load('icon.ico')
#setting up the window title and icon
pygame.display.set_caption('AI learning Flappy Bird')
pygame.display.set_icon(ICON)
#importing fonts for score
pygame.font.init()
STAT_FONT = pygame.font.SysFont("veranda", 30)
#making a class bird to spawn the birds
class Bird:
    IMGS = BIRD_IMGS
    #angle at which bird will tilt while jumping
    MAX_ROTATION = 25
    #how much tilting per frame
    ROT_VEL = 20
    #number for frames for the flap animation
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        #starting position of the bird
        self.x = x
        self.y = y
        #the realtime tilt of the bird
        self.tilt = 0
        self.tick_count = 0
        #bird is stationary at the start 
        self.vel = 0
        self.height = self.y
        #counter for which bird image to show
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        #the velocity is negative because the top of the window approaches 0
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y
    
    def move(self):
        self.tick_count += 1
        #displacement
        d = self.vel * self.tick_count + 1.5 * self.tick_count**2
        #setting up a terminal velocity
        if d >= 16:
            d = 16
        #smoothen the jump
        if d < 0:
            d -= 2
        #making the movement
        self.y += d
        #if the bird is going up
        if d < 0 or self.y < self.height + 50:
            #making sure to not over-rotate the bird  
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        #if the bird is going down
        else:
            #this just makes the flappy bird nose downward when falling
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
    
    def draw(self, win):
        self.img_count += 1
        #selecting which bird image to show and making a smooth 0,1,2,1,0 animation for each jump
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            #reset the image count after one animation
            self.img_count = 0
        #choosing what image to show when bird is falling
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            #making sure jumping doesn't skip frames
            self.img_count = self.ANIMATION_TIME*2
        #setting up image rotation for jump
        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        #adding the image to the screen
        win.blit(rotated_img, new_rect.topleft)
    
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

#making a class pipe to spawn the pipes
class Pipe:
    #space between the pipes
    GAP = 200
    #velocity of approaching
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        #these are just to know where the top and bottom pip are drawn
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        #for collision purposes
        self.passed = False
        self.set_height()
    
    def set_height(self):
        #picking random height for pipe
        self.height = random.randrange(50, 450)
        #basically just spawning a portion of the pipe out of the screen to crop it
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        #distance from top pipe and bottom pipe respectively (rounded off since it does not allow non-integer values)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        #find point of collision with the pipes (returns 'None' if does not exist)
        top_point = bird_mask.overlap(top_mask, top_offset)
        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
        #checking if point of collision exists
        if top_point or bottom_point:
            return True
        return False

#making a class base to spawn the base
class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        #this is a rather simple move method where i place the base image next to itself in the code in the window and when
        #one completely goes out of the frame, the next one shifts behind it and the animtaion continues
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH
    
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

#function to draw a window
def draw_window(win, birds, pipes, base, score, gen):
    #background
    win.blit(BG_IMG, (0, 0))
    #pipes
    for pipe in pipes:
        pipe.draw(win)
    #ground
    base.draw(win)
    #birds
    for bird in birds:
        bird.draw(win)
    #score
    text = STAT_FONT.render(f"Score: {score}", 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    #generation
    text1 = STAT_FONT.render(f"Generation {gen}", 1, (255, 255, 255))
    win.blit(text1, (10, 10))
    #refresh
    pygame.display.update()
#the function to run the main loop
def main(genomes, config):
    #variable to generation
    global gen
    gen += 1
    #these three lists are neural networks for neat
    nets = []
    ge = []
    birds = []
    #setting up the neural network
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(180,350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True

    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
        #making sure only one pipe is read at a time
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break
        #getting the fitness calculated
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1
            #applying the activation function (tanh in this case)
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        #bird.move()
        base.move()
        #this list is to remove used pipes
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
            
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.x +pipe.PIPE_TOP.get_width() < -100:
                rem.append(pipe)
            
            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))
        
        for r in rem:
            pipes.remove(r)

        #check if the bird touches the ground or the ceiling
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() > 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        if score > 50:
            break

        draw_window(win, birds, pipes, base, score, gen)



#this is the function to run the ai
def run(config_path):
    #loading the config file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    #setting up a population
    p = neat.Population(config)
    #setting up outputs for console
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #setting win condition with the fitness function main()
    winner = p.run(main, 50)

#this is just fancy stuff neat wants me to do in the docs so i will do that
if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat-config.txt")
    run(config_path) 