# Duck
This is just a simple Slack bot for me to use that has a few utilities

## Try it out
You can test it out (if you're in the HC slack) [here](https://hackclub.slack.com/archives/C09ETD04JH1)

## Features
It doesn't have many, but these are the ones so far
1. A sticky note command
   - Run it with /sticky-note and you can either remove, edit or create a message (you need to specify the text for edit and create)
   - This only works in this channel for now until I can find a way to get the channel managers of a certain channel
2. A dice roller
   - There are 2, /d6 and /dx. /d6 just does a normal six sided roll, but you can specify the number of sides with /dx
   - You can either run /d6 by itself or you can also specify whether to post in the channel (just type true after /d6, like /d6 true
   - For /dx, you first have to specify the number of sides and then you can specify whether or not to post it in the channel or send an "only visible to you" message. 
     - For example: /dx 10 true simulates a roll with 10 sides and posts it in the channel
