# Duck
A simple Slack bot for me to use that has a few utilities

## Try it out
You can test it out (if you're in the HC slack) [here](https://hackclub.slack.com/archives/C09ETD04JH1)

## Features
It doesn't have many, but these are the ones so far
1. A sticky note command
   - Run it with /sticky-note and you can either remove, edit or create a message (you need to specify the text for edit and create)
   - This only works in this channel for now until I can find a way to get the channel managers of a certain channel
2. A dice roller
   - There are 2, `/d6` and `/dx`. `/d6` just does a normal six sided roll, but you can specify the number of sides with `/dx`
   - You can either run `/d6` by itself or you can also specify whether to post in the channel, just type true after `/d6`, like `/d6 true`
   - For /dx, you first have to specify the number of sides and then you can specify whether or not to post it in the channel or send an "only visible to you" message.
     - For example: /dx 10 true simulates a roll with 10 sides and posts it in the channel
3. A ping command
   - This provides 2 types of ping, a tcp ping toward Slack's servers, and one that calculates how long a Slack API request takes, which is less accurate but more applicable, since this is a Slackbot
   - Additionally, this command provides a unique machine_id, so I can identify which server I'm running this on which can prevent issues like running on old code (that hasn't been git pulled by the server yet) and allowing me to actually find logs on the specific device where errors have occured.
   - Run this with `/pingo` in the Hack Club Slack
4. Yubico OTP checks
   - You can specify a Slack channel in your .env for this bot to constantly check for Yubico OTPs, which you get from pressing the captive button on Yubikeys. Although these OTPs are rarely used anymore, Yubico provides an API to test the validity of these OTPs, which is what this module uses and you can try out in [this channel](https://hackclub.enterprise.slack.com/archives/C07N1JRBMF1) on the Hack Club Slack
5. Private channel joiner
   - Since HC's workspace has had workflows disabled, there isn't really a better way to request to join someone's private channel, unless you DM the owner. This module attempts to fix this issue with a command that allows people make a join request.
   - It also includes features like blacklisting, and cooldowns to prevent people from spam requesting
   - You can run this with `/join-obobs-duck`
6. Kuma Statuspage integration
   - Kuma Statuspage is a statuspage service, like Atlassian Startpage, which you may have seen in places like [claude](https://status.claude.ai) and [cloudflare](https://cloudflarestatus.com).
   - Since this is a Slackbot, there isn't really a way for the statuspage server to make a request to check the uptime time of it, so we instead use a push system, where we make a requests to a url every 55 seconds to tell it that the bot is online
   - You can see a demo of this [here](https://status.olived.xyz/status/obob) under `obob's duck`

## Deploying locally
   - Clone this repo
   - Gather up all of the required API keys that this bot needs
      - Get a Yubico OTP key from [here](https://upgrade.yubico.com/getapikey/) (you need a yubikey to do this)
      - Create a new Slack app [here](https://api.slack.com/apps)
   - Then duplicate the provided .env.example and add fill it out (Kuma usage is optional, if you don't want to set it up, then just set STATUS_ENABLED to false
   - Now you can choose whether to run on bare metal or Docker
      - If you would not like to use Docker, then can simply run main.py in src/
      - If you want to use Docker, then a docker-compose is provided, whick you can simply run docker compose build and then docker compose up -d
