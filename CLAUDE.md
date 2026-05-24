# Overview

Lyrc is a terminal based application designed to assist in the creation of song lyrics to be used with Suno or other similar music generation tools.

# Features at a Glance

- Rich terminal interface that uses CSS to define styles
- Has intellisense-like helpers for stage directions. As soon as you open a bracket, it knows you are providing stage directions
- Configurable rhyming structures, with the simplest (two rhyming lines) being the default
- Each line has a sylable count in the margin
- Collpsable sections defined by stage directions (chorus, bridge, etc.)
- Sections can be moved around and copy/pasted within the song as blocks
- A simple hotkey copies all text for pasting somewhere else
- All songs have a title, and all songs are stored as markdown within a 'songs' folder
- AI integration using Claude CLI
- Thesaurus-like suggestions for synonyms that pop up like intellisense when a hotkey is pressed at the end of a word.