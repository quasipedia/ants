#! /bin/bash
git archive --format zip -o bot.zip HEAD
chromium-browser http://aichallenge.org/submit.php
