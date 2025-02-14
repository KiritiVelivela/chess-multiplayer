# ♟️ Real-Time Multiplayer Chess Game  

A real-time multiplayer chess platform built using **Django Channels, Redis, and WebSockets**, enabling users to challenge opponents, accept challenges, and play chess in real-time.

## 🚀 Features  

- **Real-Time Gameplay**: Instant move updates via WebSocket-based communication.  
- **Challenge System**: Send, accept, or reject game challenges dynamically.  
- **State Management**: Uses **Redis** for real-time updates and **PostgreSQL** for persistence.  
- **Turn-Based Validation**: Ensures only the correct player can make move.  
- **User Presence Tracking**: Tracks online users and available opponents via Django Channels & Redis.  
- **Secure Authentication**: Integrates Django’s User Model for authentication & session management.  
- **Game History & Journals**: Stores game history, move count, and player notes for analysis.  
- **Resignation Handling**: Allows players to resign, automatically declaring the opponent as the winner.

## 🛠️ Tech Stack  

- **Backend**: Django, Django Channels, Redis, PostgreSQL  
- **WebSockets**: Real-time communication with Django Channels  
- **Frontend**: Django Templates, HTML, CSS, JavaScript  
- **Authentication**: Django’s built-in authentication system 

## 📦 Installation  

### 1 Clone the Repository  
```bash
git clone https://github.com/KiritiVelivela/chess-multiplayer.git
cd chess-multiplayer
```

### 2 Setup a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3 Install Dependencies
```bash
pip install -r requirements.txt
```

### 4 Start the Development Server
```bash
python manage.py runserver
```


