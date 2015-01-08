# What is NLUlite?


NLUlite is a developer-friendly database that can read texts and
answer questions in English about them. For example, consider the
following text (taken from http://simple.wikipedia.org/wiki/Snakes)

```
  A snake is a member of about 19 reptile families that has no limbs,
  voice, ears, or eyelids. They also have a long, slender body. About
  2,900 snake species are known to exist, and most of them live in the
  tropics. Very few snake species are able to live beyond the Tropic of
  Cancer or Tropic of Capricorn, and only one species, common viper,
  lives beyond the Arctic Circle. Their skin is covered with
  scales. They can see well, and they can taste the air with their
  tongues by flicking them in and out. Though they do not have a voice,
  they hiss instead. Like all reptiles, snakes need the heat of the sun
  to control their body temperature.
```

You can retrieve the information in the text by asking questions that
match the sentence within the provided data 

```
  what are the snakes able to do?
  where do most of the snakes live?
  what animal has no limbs?
  what is a member of what?
```

You can also combine two or more questions

```
  what has no voice and sees well?
```

Additionally, you can specify in the text simple inference rules,
like 

```
  If an animal has no limbs it cannot walk.
```

and then ask

```
  what does not walk?
```

This repository contains the client files, to be used in conjunction
with the server. 

The server can be downloaded from 
https://nlulite.com
