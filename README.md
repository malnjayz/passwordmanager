# Maln's Passwordmanager
---
## Overview
1. Features
2. Setup
3. Usage
---
## Features
* Using docker compose for easy setup
* Python-WebApp delivers easy
    * accessibility and
    * configurability
* Multi-User functionality
* Two-Time Encryption for stored passwords
    * including user-specific salt
    * also including installation-specific pepper
---
## Setup
1. Clone Repository:
    
    git clone git://github.com/malnjayz/passwordmanager.git
2. Populate .env with secure passwords.
3. Build the image and bring compose up:
    
    docker compose build

    docker compose up -d

    On initial startup MySQL will initialize the specified password, this may take a few seconds!

    You can check the state using 'docker compose logs -f', exit using Ctrl+C
4. Initialize Database
    
    docker compose exec app python3 /app/initdb.sh
5. The container will listen on port 5000, you can change that in the docker-compose.yml
6. (opt.) I put my container behind an nginx-Proxy, you can reach a demo at passwordmanager.maln.dev
---
## Usage (images coming soon)
* You can both create a user and login by typing in credentials and then clicking the specific button.
    * Once you registered you will need to type in your credentials again to log in.
* Once logged in you can create a new folder using the text space at the top of the screen.
    * On creation your folders opens automatically.
    * If you want to switch to another folder just click the according button.
* Using the blank text spaces you can now begin to populate your folders.
* Every entry line brings the possibillity to:
    * Open the linked website (Button 'O')
    * Copy the linked username (Button 'U')
    * Copy the linked password (Button 'P')
    * Update the entry (Button 'Update')
    * Delete the entry (Button 'X').
* In order to delete a folder you have to type 'confirm' and clicke the 'Delete Folder'-Button.
