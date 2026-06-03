====OPIS PROJEKTU====

Lan Chat to aplikacja komunikatora działająca w sieci lokalnej, umożliwiająca wymianę wiadomości w czasie rzeczywistym pomiędzy użytkownikami.

System składa się z klienta oraz serwera TCP, które komunikują się przy użyciu własnego protokołu tekstowego.

Aplikacja umożliwia:

- komunikację prywatną (PM)
- czaty grupowe (ROOM)
- listę aktywnych użytkowników
- listę dostępnych pokoi
- historię wiadomości (SQLite)
- dynamiczną aktualizację GUI

====FUNKCJONALNOŚCI====

- logowanie użytkownika z walidacją nicku
- obsługa wielu klientów jednocześnie (wątki po stronie serwera)
- prywatne wiadomości (PM)
- pokoje rozmów (ROOM)
- dołączanie i opuszczanie pokoi (/join, /leave)
- automatyczna aktualizacja list:
  - aktywnych użytkowników
  - dostępnych pokoi
- zapisywanie wiadomości do bazy danych SQLite
- pobieranie historii rozmów (PM i ROOM)
- GUI w Tkinter z podziałem na:
  - listę użytkowników
  - listę pokoi
  - okno czatu
- komunikacja w czasie rzeczywistym przez socket TCP

====PROTOKÓŁ KOMUNIKACJI====

Wiadomości prywatne (PM)
 - PM|odbiorca|treść
   
Wiadomości w pokoju (ROOM)
 - ROOM|pokój|treść
   
Format wiadomości serwera
 - PM|nadawca|odbiorca|treść|timestamp
 - ROOM|pokój|nadawca|treść|timestamp
   
Aktualizacje systemowe
 - USERS|user1,user2,user3
 - ROOMS|room1:user1,user2;room2:user3

====WYKORZYSTANE NARZĘDZIA====

- socket – komunikacja TCP
- threading – obsługa wielu klientów
- queue – komunikacja GUI ↔ wątek sieciowy
- Tkinter – interfejs graficzny
- SQLite – przechowywanie historii wiadomości
- re – walidacja nicków i nazw pokoi
- datetime – obsługa timestampów

====STRUKTURA PLIKÓW====

server.py
- serwer TCP
- obsługa klientów
- routing wiadomości (PM / ROOM)
- zarządzanie pokojami
- broadcast list użytkowników i pokoi
- rate limiting
- zapis do bazy danych

client.py
- połączenie z serwerem
- odbiór wiadomości w osobnym wątku
- parsowanie protokołu
- przekazywanie danych do GUI przez Queue

gui.py
- interfejs użytkownika (Tkinter)
- lista użytkowników i pokoi
- obsługa czatu PM i ROOM
- dynamiczne odświeżanie GUI
- obsługa zdarzeń (kliknięcia, wysyłanie wiadomości)

database.py
- SQLite database
- zapis historii wiadomości
- pobieranie historii PM i ROOM

main.py
- inicjalizacja aplikacji GUI
- uruchomienie klienta i połączenia z serwerem

====URUCHOMIENIE PROJEKTU====
1. Uruchomienie serwera
2. Uruchomienie main dla każdego klienta 
