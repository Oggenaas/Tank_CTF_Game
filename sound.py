import pygame

"""Contains all the functions that handle diffrent sound events"""

def background_music():

    pygame.mixer.music.load("data/sounds/background_music.mp3")

    pygame.mixer.music.play(0,0,0)

    pygame.mixer.music.set_volume(0.2)


def shoot_sound():

    shoot_sound = pygame.mixer.Sound("data/sounds/shoot_sound.wav")

    shoot_sound.play()


def victory_sound():

    victory_sound = pygame.mixer.Sound("data/sounds/victory_sound.wav")

    victory_sound.play()


def grab_flag_sound():

    grab_flag_sound = pygame.mixer.Sound("data/sounds/flag_grab_sound.wav")

    grab_flag_sound.play()


def explosion_sound():

    explosion_sound = pygame.mixer.Sound("data/sounds/explosion_sound.ogg")

    explosion_sound.play()


def shoot_second_sound():

    shoot_second_sound = pygame.mixer.Sound("data/sounds/shoot_second_sound.wav")

    shoot_second_sound.play()