# -*- coding: utf-8 -*-

import sqlite3
import random

# Inicjalizacja bazy danych
conn = sqlite3.connect('gry.db')
c = conn.cursor()

# Tworzenie tabel w bazie danych
c.execute('''CREATE TABLE IF NOT EXISTS gry
             (id INTEGER PRIMARY KEY,
              nazwa TEXT UNIQUE)''')

c.execute('''CREATE TABLE IF NOT EXISTS gracze
             (id INTEGER PRIMARY KEY,
              nazwa TEXT UNIQUE)''')

c.execute('''CREATE TABLE IF NOT EXISTS rozgrywki
             (id INTEGER PRIMARY KEY,
              gra_id INTEGER,
              numer INTEGER,
              FOREIGN KEY(gra_id) REFERENCES gry(id))''')

c.execute('''CREATE TABLE IF NOT EXISTS wyniki
             (id INTEGER PRIMARY KEY,
              rozgrywka_id INTEGER,
              gracz_id INTEGER,
              punkty INTEGER,
              wygrana BOOLEAN,
              FOREIGN KEY(rozgrywka_id) REFERENCES rozgrywki(id),
              FOREIGN KEY(gracz_id) REFERENCES gracze(id))''')

conn.commit()

def dodaj_gre(nazwa_gry):
    try:
        c.execute("INSERT INTO gry (nazwa) VALUES (?)", (nazwa_gry,))
        conn.commit()
        print(f"Dodano grę: {nazwa_gry}")
    except sqlite3.IntegrityError:
        print("Gra o tej nazwie już istnieje.")

def dodaj_gracza(nazwa_gracza):
    try:
        c.execute("INSERT INTO gracze (nazwa) VALUES (?)", (nazwa_gracza,))
        conn.commit()
        print(f"Dodano gracza: {nazwa_gracza}")
    except sqlite3.IntegrityError:
        print("Gracz o tej nazwie już istnieje.")

def pobierz_id_gracza(nazwa_gracza):
    c.execute("SELECT id FROM gracze WHERE nazwa=?", (nazwa_gracza,))
    result = c.fetchone()
    if result:
        return result[0]
    else:
        print(f"Gracz o nazwie '{nazwa_gracza}' nie istnieje.")
        return None

def pobierz_liste_gier():
    c.execute("SELECT nazwa FROM gry")
    gry = c.fetchall()
    return [gra[0] for gra in gry]

def pobierz_liste_graczy():
    c.execute("SELECT nazwa FROM gracze")
    gracze = c.fetchall()
    return [gracz[0] for gracz in gracze]

def pobierz_statystyki_gry(nazwa_gry):
    try:
        c.execute("SELECT g.nazwa, COUNT(DISTINCT r.numer) as liczba_gier, AVG(w.punkty) as srednia_punktow "
                  "FROM gry g LEFT JOIN rozgrywki r ON g.id=r.gra_id "
                  "LEFT JOIN wyniki w ON r.id=w.rozgrywka_id "
                  "WHERE g.nazwa=? AND g.id=r.gra_id " 
                  "GROUP BY g.id", (nazwa_gry,))
        statystyki = c.fetchone()
        return statystyki
    except sqlite3.Error as e:
        print("Błąd:", e)
        return None


def pobierz_statystyki_gracza(nazwa_gry):
    try:
        c.execute("SELECT gracz_id, COUNT(*) as liczba_gier, COUNT(CASE WHEN wygrana=1 THEN 1 END) as liczba_wygranych, AVG(punkty) as srednia_punktow "
                  "FROM wyniki w LEFT JOIN rozgrywki r ON w.rozgrywka_id=r.id "
                  "LEFT JOIN gry g ON r.gra_id=g.id "
                  "WHERE g.nazwa=? "
                  "GROUP BY gracz_id", (nazwa_gry,))
        statystyki_gracza = c.fetchall()
        return statystyki_gracza
    except sqlite3.Error as e:
        print("Błąd:", e)
        return None

def pobierz_historie_gier(nazwa_gry):
    try:
        c.execute("SELECT r.id, r.numer, gracz_id, punkty, wygrana "
                  "FROM wyniki w LEFT JOIN rozgrywki r ON w.rozgrywka_id=r.id "
                  "LEFT JOIN gry g ON r.gra_id=g.id "
                  "WHERE g.nazwa=? "
                  "ORDER BY r.id", (nazwa_gry,))
        wynik = c.fetchall()

        numer_porzadkowy = 1
        numeracja = {}

        historia_gier = []

        for element in wynik:
            klucz = element[0]
            if klucz not in numeracja:
                numeracja[klucz] = numer_porzadkowy
                numer_porzadkowy += 1
            nowy_element = (numeracja[klucz],) + element[1:]
            historia_gier.append(nowy_element)

        return historia_gier
    except sqlite3.Error as e:
        print("Błąd:", e)
        return None

def dodaj_rozgrywke_z_wynikami(nazwa_gry, gracze):
    try:
        # Sprawdzenie, czy gra o podanej nazwie istnieje
        c.execute("SELECT id FROM gry WHERE nazwa=?", (nazwa_gry,))
        gra_id = c.fetchone()

        if gra_id is not None:
            gra_id = gra_id[0]

            # Fetch the maximum numer for the given game
            c.execute("SELECT MAX(numer) FROM rozgrywki WHERE gra_id=?", (gra_id,))
            max_numer = c.fetchone()[0]

            # Set numer to one greater than the maximum or 1 if there is no existing rozgrywki
            numer_rozgrywki = max_numer + 1 if max_numer is not None else 1

            # Insert a new rozgrywka with the calculated numer
            c.execute("INSERT INTO rozgrywki (gra_id, numer) VALUES (?, ?)", (gra_id, numer_rozgrywki))
            rozgrywka_id = c.lastrowid

            for gracz, punkty, wygrana in gracze:
                gracz_id = pobierz_id_gracza(gracz)
                if gracz_id is not None:
                    c.execute("INSERT INTO wyniki (rozgrywka_id, gracz_id, punkty, wygrana) VALUES (?, ?, ?, ?)", (rozgrywka_id, gracz_id, punkty, wygrana))

            conn.commit()
            print(f"Dodano rozgrywkę dla gry: {nazwa_gry} z wynikami: {gracze}")
        else:
            print(f"Brak gry: {nazwa_gry} lub rozgrywek dla niej")
    except sqlite3.Error as e:
        print("Błąd:", e)

def losuj_gre():
    c.execute("SELECT g.nazwa, COUNT(DISTINCT r.id) as suma_rozgrywek FROM gry g LEFT JOIN rozgrywki r ON g.id=r.gra_id GROUP BY g.id ORDER BY suma_rozgrywek ASC")
    wyniki = c.fetchall()
    min_rozgrywek = wyniki[0][1]
    gry_do_wyboru = [nazwa for nazwa, suma in wyniki if suma == min_rozgrywek]
    return random.choice(gry_do_wyboru)

def usun_gre(nazwa_gry):
    try:
        c.execute("DELETE FROM gry WHERE nazwa=?", (nazwa_gry,))
        conn.commit()
        print(f"Usunięto grę: {nazwa_gry}")
    except sqlite3.Error as e:
        print("Błąd:", e)

def usun_gracza(nazwa_gracza):
    try:
        c.execute("DELETE FROM gracze WHERE nazwa=?", (nazwa_gracza,))
        conn.commit()
        print(f"Usunięto gracza: {nazwa_gracza}")
    except sqlite3.Error as e:
        print("Błąd:", e)

def usun_rozgrywke(nazwa_gry):
    try:
        c.execute("SELECT id FROM gry WHERE nazwa=?", (nazwa_gry,))
        gra_id = c.fetchone()

        if gra_id is not None:
            gra_id = gra_id[0]

            c.execute("SELECT MAX(numer) FROM rozgrywki WHERE gra_id=?", (gra_id,))
            max_numer = c.fetchone()[0]

            c.execute("SELECT id FROM rozgrywki WHERE numer=? AND gra_id=?", (max_numer, gra_id))
            id_rozgrywki = c.fetchone()[0]

            c.execute("DELETE FROM rozgrywki WHERE numer=? AND gra_id=?", (max_numer, gra_id))
            conn.commit()
            
            c.execute("DELETE FROM wyniki WHERE rozgrywka_id=?", (id_rozgrywki,))
            conn.commit()

            print(f"Usunięto rozgrywkę o numerze {max_numer} dla gry: {nazwa_gry}")
        else:
            print(f"Nie znaleziono gry o nazwie: {nazwa_gry}")
    except sqlite3.Error as e:
        print("Błąd:", e)

def wyswietl_statystyki(nazwa_gry):
    try:
        statystyki_gry = pobierz_statystyki_gry(nazwa_gry)
        if statystyki_gry is not None:
            nazwa_gry, liczba_gier, srednia_punktow_w_grze = statystyki_gry
            print(f"\n===== Statystyki gry {nazwa_gry} =====")
            print(f"Liczba gier: {liczba_gier}")
            print(f"Średnia liczba punktów w grze: {srednia_punktow_w_grze:.2f}\n")

            statystyki_gracza = pobierz_statystyki_gracza(nazwa_gry)
            if statystyki_gracza:
                print("===== Statystyki wszystkich graczy =====")
                for gracz_id, liczba_gier, liczba_wygranych, srednia_punktow in statystyki_gracza:
                    c.execute("SELECT nazwa FROM gracze WHERE id=?", (gracz_id,))
                    gracz_nazwa = c.fetchone()[0]
                    print(f"Gracz: {gracz_nazwa}")
                    print(f"Liczba gier: {liczba_gier}")
                    print(f"Liczba wygranych: {liczba_wygranych}")
                    print(f"Średnia liczba punktów w grze: {srednia_punktow:.2f}\n")

                historia_gier = pobierz_historie_gier(nazwa_gry)
                if historia_gier:
                    print("===== Historia gier =====")
                    for numer_rozgrywki, numer, gracz_id, punkty, wygrana in historia_gier:
                        c.execute("SELECT nazwa FROM gracze WHERE id=?", (gracz_id,))
                        gracz_nazwa = c.fetchone()[0]
                        print(f"Nr rozgrywki: {numer_rozgrywki}, Gracz: {gracz_nazwa}, Punkty: {punkty}, Wygrana: {'Tak' if wygrana else 'Nie'}")
                    print("=" * 30 + "\n")
                else:
                    print("Brak historii gier.\n")
            else:
                print("Brak statystyk graczy.\n")
        else:
            print(f"Nie znaleziono żadnej rozgrywki dla: {nazwa_gry}")
    except sqlite3.Error as e:
        print("Błąd:", e)

def wyswietl_liste_gier_z_liczba_rozgrywek():
    try:
        c.execute("SELECT g.nazwa, COUNT(DISTINCT r.id) as liczba_rozgrywek "
                  "FROM gry g LEFT JOIN rozgrywki r ON g.id=r.gra_id "
                  "GROUP BY g.id")
        gry = c.fetchall()

        if gry:
            print("\n===== Lista wszystkich gier wraz z liczbą rozgrywek =====")
            for gra, liczba_rozgrywek in gry:
                print(f"{gra}: {liczba_rozgrywek}")
            print("=" * 50 + "\n")
        else:
            print("Brak dostępnych gier.\n")
    except sqlite3.Error as e:
        print("Błąd:", e)

def wyswietl_liste_graczy():
    gracze = pobierz_liste_graczy()
    if gracze:
        print("\n===== Lista wszystkich graczy =====")
        for gracz in gracze:
            statystyki_gracza = pobierz_statystyki_gracza_dla_gracza(gracz)
            liczba_gier = statystyki_gracza[1] if statystyki_gracza else 0
            liczba_wygranych = statystyki_gracza[2] if statystyki_gracza else 0
            print(f"{gracz} - gier: {liczba_gier}, wygranych: {liczba_wygranych}")
        print("=" * 50 + "\n")
    else:
        print("Brak dostępnych graczy.\n")

def pobierz_statystyki_gracza_dla_gracza(nazwa_gracza):
    try:
        c.execute("SELECT gracz_id, COUNT(*) as liczba_gier, COUNT(CASE WHEN wygrana=1 THEN 1 END) as liczba_wygranych "
                  "FROM wyniki w LEFT JOIN rozgrywki r ON w.rozgrywka_id=r.id "
                  "LEFT JOIN gracze g ON w.gracz_id=g.id "
                  "WHERE g.nazwa=? "
                  "GROUP BY gracz_id", (nazwa_gracza,))
        statystyki_gracza = c.fetchone()
        return statystyki_gracza
    except sqlite3.Error as e:
        print("Błąd:", e)
        return None



# widok konsoli
while True:
    print("\n========= Menu =========")

    print("\n======= Dodawanie =======")
    print("1. Dodaj grę")
    print("2. Dodaj gracza")
    print("3. Dodaj rozgrywkę z wynikami")

    print("\n====== Losowanie ======")
    print("4. Losuj grę")

    print("\n===== Usuwanie =====")
    print("5. Usuń grę")
    print("6. Usuń ostatnią rozgrywkę dla gry")
    print("7. Usuń gracza")

    print("\n====== Statystyki ======")
    print("8. Wyświetl statystyki dla wybranej gry")
    print("9. Wyświetl liczbę rozgrywek dla gier")
    print("10. Wyświetl statystyki graczy")
    
    print("\n===== Wyjście =====")
    print("0. Zamknij")

    wybor = input("Wybierz opcję: ")

    if wybor == '1':
        nazwa_gry = input("Podaj nazwę gry: ")
        dodaj_gre(nazwa_gry)

    elif wybor == '2':
        nazwa_gracza = input("Podaj nazwę gracza: ")
        dodaj_gracza(nazwa_gracza)

    elif wybor == '3':
        gry = pobierz_liste_gier()
        if gry:
            print("Dostępne gry:", gry)
            nazwa_gry = input("Wybierz grę z powyższej listy: ")
            liczba_graczy = int(input("Podaj liczbę graczy: "))

            gracze = []
            for _ in range(liczba_graczy):
                dostepni_gracze = pobierz_liste_graczy()
                if dostepni_gracze:
                    print("Dostępni gracze:", dostepni_gracze)
                    gracz = input("Wybierz gracza z powyższej listy: ")
                    punkty = int(input("Podaj liczbę punktów: "))
                    wygrana = input("Czy wygrana (Tak/Nie): ").lower() == 'tak'
                    gracze.append((gracz, punkty, wygrana))
                else:
                    print("Brak dostępnych graczy. Dodaj graczy przed rozpoczęciem rozgrywki.")
                    break

            dodaj_rozgrywke_z_wynikami(nazwa_gry, gracze)

    elif wybor == '4':
        print("Wybierz rodzaj losowania gry:")
        print("1. Wylosuj spośród gier o najmniejszej liczbie rozgrywek")
        print("2. Wylosuj ze wszystkich gier")
        
        rodzaj_losowania = input("Wybierz opcję (1 lub 2): ")

        if rodzaj_losowania == '1':
            wylosowana_gra = losuj_gre()
        elif rodzaj_losowania == '2':
            gry_do_wyboru = pobierz_liste_gier()
            if gry_do_wyboru:
                wylosowana_gra = random.choice(gry_do_wyboru)
            else:
                wylosowana_gra = None
                print("Brak dostępnych gier do losowania.")
        else:
            print("Niepoprawny wybór. Wybierz 1 lub 2.")
            wylosowana_gra = None

        if wylosowana_gra:
            print(f"Wylosowana gra do zagrania: {wylosowana_gra}")
        elif wybor == '2':
            print("Brak dostępnych gier do losowania.")


    elif wybor == '5':
        gry = pobierz_liste_gier()
        if gry:
            print("Dostępne gry:", gry)
            nazwa_gry = input("Podaj nazwę gry do usunięcia: ")
            usun_gre(nazwa_gry)
        else:
            print("Brak dostępnych gier do usunięcia.")

    elif wybor == '6':
        gry = pobierz_liste_gier()
        if gry:
            print("Dostępne gry:", gry)
            nazwa_gry = input("Podaj nazwę gry: ")
            usun_rozgrywke(nazwa_gry)
        else:
            print("Brak dostępnych gier do usunięcia.")

    elif wybor == '7':
        gracze = pobierz_liste_graczy()
        if gracze:
            print("gracz:", gracze)
            nazwa_gracza = input("Podaj nazwę gracza do usunięcia: ")
            usun_gracza(nazwa_gracza)
        else:
            print("Brak dostępnych graczy do usunięcia.")
    

    elif wybor == '8':
        gry = pobierz_liste_gier()
        if gry:
            print("Dostępne gry:", gry)
            nazwa_gry = input("Podaj nazwę gry: ")
            wyswietl_statystyki(nazwa_gry)
        else:
            print("Brak dostępnych gier do wyświetlenia statystyk.")

    elif wybor == '9':
        wyswietl_liste_gier_z_liczba_rozgrywek()

    elif wybor == '10':
        wyswietl_liste_graczy()

    elif wybor == '0':
        break

    else:
        print("Niepoprawny wybór. Spróbuj ponownie.")

conn.close()
