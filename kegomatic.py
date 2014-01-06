#!/usr/bin/python
import os
import time
import math
import logging
import pygame, sys
from pygame.locals import *
import RPi.GPIO as GPIO
from twitter import *
from flowmeter import *
from adabot import *
from seekrits import *

t = Twitter( auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET, CONSUMER_KEY, CONSUMER_SECRET) )

boardRevision = GPIO.RPI_REVISION
GPIO.setmode(GPIO.BCM) # use real GPIO numbering
GPIO.setup(22,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(23,GPIO.IN, pull_up_down=GPIO.PUD_UP)

# set up pygame
pygame.init()

# set up the window
VIEW_WIDTH = 1248
VIEW_HEIGHT = 688
pygame.display.set_caption('KEGBOT')

# hide the mouse
pygame.mouse.set_visible(False)

# set up the flow meters
fm = FlowMeter('metric')
fm2 = FlowMeter('metric')
fm2.enabled = False
tweet = ''

# set up the colors
BLACK = (0,0,0)
WHITE = (255,255,255)

# set up the window surface
windowSurface = pygame.display.set_mode((VIEW_WIDTH,VIEW_HEIGHT), FULLSCREEN, 32) 
windowInfo = pygame.display.Info()
FONTSIZE = 48
LINEHEIGHT = 28
basicFont = pygame.font.SysFont(None, FONTSIZE)

# set up the background
bg = pygame.image.load('beer-bg.png')

# set up the adabots
back_bot = adabot(361, 151, 361, 725)
middle_bot = adabot(310, 339, 310, 825)
front_bot = adabot(220, 527, 220, 888)

def renderThings(flowMeter, flowMeter2, tweet, windowSurface, basicFont):
  # Clear the screen
  windowSurface.blit(bg,(0,0))
  
  # draw the adabots
  back_bot.update()
  windowSurface.blit(back_bot.image,(back_bot.x, back_bot.y))
  middle_bot.update()
  windowSurface.blit(middle_bot.image,(middle_bot.x, middle_bot.y))
  front_bot.update()
  windowSurface.blit(front_bot.image,(front_bot.x, front_bot.y))

  # Draw Ammt Poured
  text = basicFont.render("CURRENT", True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (40,20))
  text = basicFont.render(flowMeter.getFormattedThisPour(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (40,30+LINEHEIGHT))
  text = basicFont.render(flowMeter2.getFormattedThisPour(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (40, 30+(2*(LINEHEIGHT+5))))

  # Draw Ammt Poured Total
  text = basicFont.render("TOTAL", True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (windowInfo.current_w - textRect.width - 40, 20))
  text = basicFont.render(flowMeter.getFormattedTotalPour(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (windowInfo.current_w - textRect.width - 40, 30 + LINEHEIGHT))
  text = basicFont.render(flowMeter2.getFormattedTotalPour(), True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (windowInfo.current_w - textRect.width - 40, 30 + (2 * (LINEHEIGHT+5))))

  # Display everything
  pygame.display.flip()

# This gets run whenever an interrupt triggers it due to pin 22 being grounded.
def doAClick(channel):
  currentTime = int(time.time() * FlowMeter.MS_IN_A_SECOND)
  if fm.enabled == True:
    fm.update(currentTime)

def doAClick2(channel):
  currentTime = int(time.time() * FlowMeter.MS_IN_A_SECOND)
  if fm2.enabled == True:
    fm2.update(currentTime)

def tweetPour(theTweet):
  try:
    t.statuses.update(status=theTweet)
  except:
    logging.warning('Error tweeting: ' + theTweet + "\n")

GPIO.add_event_detect(22, GPIO.RISING, callback=doAClick, bouncetime=20)
GPIO.add_event_detect(23, GPIO.RISING, callback=doAClick2, bouncetime=20)

# main loop
while True:
  # Handle keyboard events
  for event in pygame.event.get():
    if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
      GPIO.cleanup()
      pygame.quit()
      sys.exit()
  
  currentTime = int(time.time() * FlowMeter.MS_IN_A_SECOND)
  
  if (fm.thisPour > 0.23 and currentTime - fm.lastClick > 10000): # 10 seconds of inactivity causes a tweet
    tweet = "Someone just poured " + fm.getFormattedThisPour() + " of root beer from the Adafruit keg bot!" 
    fm.thisPour = 0.0
    tweetPour(tweet)
 
  if (fm2.thisPour > 0.23 and currentTime - fm2.lastClick > 10000): # 10 seconds of inactivity causes a tweet
    tweet = "Someone just poured " + fm2.getFormattedThisPour() + " of beer from the Adafruit keg bot!"
    fm2.thisPour = 0.0
    tweetPour(tweet)

  # Update the screen
  renderThings(fm, fm2, tweet, windowSurface, basicFont)
