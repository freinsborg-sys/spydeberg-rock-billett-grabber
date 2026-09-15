import asyncio
from datetime import datetime

from playwright.async_api import async_playwright


# ---------------------------------------------------------
# INNSTILLINGER
# ---------------------------------------------------------

URL = "https://srfestival.ticketco.events/no/nb/e/spydeberg_rock_2027"

# Første automatiske sjekk
CHECK_TIME = datetime(2026, 9, 15, 15, 14, 59)

# Åpne nettleseren 90 sekunder før
OPEN_EARLY_SECONDS = 90

# Ventetid mellom oppdateringer
REFRESH_SECONDS = 0

# Maks antall automatiske oppdateringer
MAX_ATTEMPTS = 15

# Ønsket antall.
# NB: Scriptet velger ikke antallet automatisk ennå.
QUANTITY = 5

# Tekster som sannsynligvis identifiserer riktig billett.
# Unngår generelle treff som "15" og "2027".
TICKET_NAMES = [
    "Early bird festivalpass",
    "Festivalpass",
    "Festival Pass",
    "Early bird",
    "15 kr",
    "Helgepass",
    "Helge pass",
    "Hælje pass",
    "Hæljepass",
]


# ---------------------------------------------------------
# HJELPEFUNKSJONER
# ---------------------------------------------------------

def countdown(seconds):
    seconds = max(0, seconds)

    minutes = int(seconds // 60)
    secs = seconds % 60

    return f"{minutes:02d}:{secs:04.1f}"


async def find_festivalpass(page):
    """
    Leter etter tekst som sannsynligvis tilhører riktig billett.
    Returnerer True når den finner et treff.
    """

    for name in TICKET_NAMES:

        try:
            locator = page.get_by_text(
                name,
                exact=False
            )

            count = await locator.count()

            if count > 0:

                print(f"\n✓ Fant mulig billettype: {name}")

                element = locator.first

                # Scroll til billetten
                try:
                    await element.scroll_into_view_if_needed()
                except Exception:
                    pass

                # Marker billetten tydelig i nettleseren
                try:
                    await element.evaluate("""
                        el => {
                            el.style.outline = '4px solid lime';
                            el.style.backgroundColor = 'yellow';
                        }
                    """)
                except Exception:
                    pass

                return True

        except Exception:
            continue

    return False


# ---------------------------------------------------------
# HOVEDPROGRAM
# ---------------------------------------------------------

async def main():

    print()
    print("=" * 60)
    print("       SPYDEBERG ROCK 2027 – BILLETTASSISTENT")
    print("=" * 60)
    print()

    print(f"Ønsket antall: {QUANTITY}")
    print(
        "Første sjekk:",
        CHECK_TIME.strftime("%H:%M:%S")
    )
    print()

    # -----------------------------------------------------
    # VENT TIL NETTLESEREN SKAL ÅPNES
    # -----------------------------------------------------

    open_time = (
        CHECK_TIME.timestamp()
        - OPEN_EARLY_SECONDS
    )

    if datetime.now().timestamp() < open_time:

        while True:

            remaining = (
                open_time
                - datetime.now().timestamp()
            )

            if remaining <= 0:
                break

            print(
                f"\rÅpner nettleseren om "
                f"{countdown(remaining)}",
                end="",
                flush=True
            )

            await asyncio.sleep(0.1)

    print("\n\nÅpner TicketCo...")


    # -----------------------------------------------------
    # START PLAYWRIGHT
    # -----------------------------------------------------

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )

        context = await browser.new_context(
            viewport=None
        )

        page = await context.new_page()


        # -------------------------------------------------
        # ÅPNE TICKETCO
        # -------------------------------------------------

        try:

            await page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=30000
            )

            print("✓ TicketCo åpnet.")

        except Exception as e:

            print("⚠ Problem ved åpning av siden:")
            print(e)

            print(
                "Nettleseren holdes åpen slik at "
                "du kan bruke siden manuelt."
            )


        # -------------------------------------------------
        # VENT TIL FØRSTE SJEKK
        # -------------------------------------------------

        while True:

            remaining = (
                CHECK_TIME.timestamp()
                - datetime.now().timestamp()
            )

            if remaining <= 0:
                break

            print(
                f"\rFØRSTE SJEKK OM "
                f"{countdown(remaining)}",
                end="",
                flush=True
            )

            await asyncio.sleep(0.1)


        print()
        print()
        print("=" * 60)
        print("        STARTER SJEKK AV BILLETTER")
        print("=" * 60)


        # -------------------------------------------------
        # OPPDATER + LET ETTER BILLETT
        # -------------------------------------------------

        found = False

        for attempt in range(1, MAX_ATTEMPTS + 1):

            print()
            print(
                f"Sjekk {attempt}/{MAX_ATTEMPTS} "
                f"({datetime.now().strftime('%H:%M:%S')})"
            )

            # Oppdater siden
            try:

                print("Oppdaterer TicketCo...")

                await page.reload(
                    wait_until="domcontentloaded",
                    timeout=30000
                )

            except Exception:

                print(
                    "⚠ Oppdateringen tok for lang tid. "
                    "Fortsetter..."
                )

            # Kort tid til rendering
            await page.wait_for_timeout(500)

            # Let etter billett
            found = await find_festivalpass(page)

            if found:

                print()
                print("=" * 60)
                print("       ✓ MULIG FESTIVALPASS FUNNET!")
                print("=" * 60)
                print()
                print(
                    f"Ønsket antall er {QUANTITY}."
                )
                print()
                print(
                    "Automatiske oppdateringer er STOPPET."
                )
                print(
                    "Sjekk den markerte billetten og "
                    "fortsett manuelt."
                )

                break


            # Ikke funnet
            if attempt < MAX_ATTEMPTS:

                print(
                    f"Ingen treff. Ny sjekk om "
                    f"{REFRESH_SECONDS} sekunder..."
                )

                await page.wait_for_timeout(
                    REFRESH_SECONDS * 1000
                )


        # -------------------------------------------------
        # INGEN TREFF
        # -------------------------------------------------

        if not found:

            print()
            print("=" * 60)
            print("       INGEN BILLETT FUNNET AUTOMATISK")
            print("=" * 60)
            print()
            print(
                "Automatisk overvåking er ferdig."
            )
            print(
                "TicketCo-vinduet forblir åpent."
            )
            print(
                "Fortsett manuelt i nettleseren."
            )


        # -------------------------------------------------
        # HOLD NETTLESEREN ÅPEN
        # -------------------------------------------------

        print()
        print("=" * 60)
        print("PROGRAMMET HOLDER NETTLESEREN ÅPEN")
        print()
        print("Scriptet gjennomfører IKKE betaling/kjøp.")
        print("Trykk Ctrl+C i terminalen når du er ferdig.")
        print("=" * 60)
        print()

        while True:
            await asyncio.sleep(60)


# ---------------------------------------------------------
# START
# ---------------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nProgrammet ble avsluttet.")
        