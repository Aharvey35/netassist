# modules/space_facts.py
import random
from colorama import Fore

def run():
    print(Fore.MAGENTA + "\n Space Explorer Activated!")
    mode = random.choice(["deep_dive", "fact_pack"])

    if mode == "deep_dive":
        deep_dive_objects = [
            {
                "name": "Mercury",
                "nickname": "Swift Planet",
                "facts": [
                    "Smallest planet in our solar system",
                    "No atmosphere to retain heat",
                    "Daytime temperatures reach 430°C",
                    "Nights drop to -180°C",
                    "Orbital period: 88 Earth days",
                    "Has a molten core",
                    "Heavily cratered surface",
                    "No moons"
                ]
            },
            {
                "name": "Venus",
                "nickname": "Earth's Twin",
                "facts": [
                    "Hottest planet due to thick CO2 atmosphere",
                    "Surface pressure 92 times Earth's",
                    "Rotates in the opposite direction",
                    "Day is longer than its year",
                    "Volcanically active",
                    "No moons"
                ]
            },
            {
                "name": "Earth",
                "nickname": "The Blue Planet",
                "facts": [
                    "Only known planet with life",
                    "70% surface covered in water",
                    "One moon",
                    "Atmosphere supports life",
                    "Protective magnetic field"
                ]
            },
            {
                "name": "Mars",
                "nickname": "The Red Planet",
                "facts": [
                    "Average temperature: -60°C",
                    "Two moons: Phobos and Deimos",
                    "Largest volcano: Olympus Mons",
                    "Tallest canyon: Valles Marineris",
                    "Day length: 24.6 hours",
                    "Thin CO2 atmosphere",
                    "Signs of ancient water"
                ]
            },
            {
                "name": "Jupiter",
                "nickname": "The Gas Giant",
                "facts": [
                    "Largest planet in the solar system",
                    "Great Red Spot is a giant storm",
                    "At least 79 moons",
                    "Has faint rings",
                    "Magnetic field 14 times stronger than Earth's"
                ]
            },
            {
                "name": "Saturn",
                "nickname": "The Ringed Planet",
                "facts": [
                    "Famous for its prominent ring system",
                    "Over 80 known moons",
                    "Low density—it would float in water",
                    "Fast rotation creates an oblate shape",
                    "Atmosphere mainly hydrogen and helium"
                ]
            },
            {
                "name": "Uranus",
                "nickname": "The Sideways Planet",
                "facts": [
                    "Rotates on its side",
                    "Bluish color due to methane",
                    "Has faint rings",
                    "Coldest planet in the solar system",
                    "At least 27 moons"
                ]
            },
            {
                "name": "Neptune",
                "nickname": "The Windy Planet",
                "facts": [
                    "Fastest winds in the solar system",
                    "Deep blue due to methane",
                    "Discovered in 1846",
                    "Triton is the largest moon, retrograde orbit",
                    "Has dark storms similar to Jupiter"
                ]
            },
            {
                "name": "Europa",
                "nickname": "Jupiter's Icy Moon",
                "facts": [
                    "Surface of ice with possible subsurface ocean",
                    "May host microbial life",
                    "Target of future space missions",
                    "Cracked icy surface",
                    "Tidal heating keeps it warm"
                ]
            },
            {
                "name": "Titan",
                "nickname": "Saturn's Methane Moon",
                "facts": [
                    "Thick nitrogen-rich atmosphere",
                    "Lakes and rivers of liquid methane",
                    "Surface temperature: -179°C",
                    "Only moon with a dense atmosphere",
                    "Studied by the Cassini-Huygens mission"
                ]
            },
            {
                "name": "The Moon",
                "nickname": "Earth's Natural Satellite",
                "facts": [
                    "Diameter: 3,474 km",
                    "Gravitational pull causes Earth's tides",
                    "Formed ~4.5 billion years ago",
                    "Visited by humans in Apollo missions",
                    "Surface has maria, craters, and highlands"
                ]
            }
        ]
        body = random.choice(deep_dive_objects)
        print(Fore.CYAN + f"\n Deep Dive: {body['name']} - {body['nickname']}")
        for fact in body['facts']:
            print("- " + fact)
    else:
        trivia_facts = [
            "Neutron stars can spin at 600 rotations per second!",
            "A day on Venus is longer than its year.",
            "There’s a planet made of diamonds – 55 Cancri e.",
            "Jupiter’s Great Red Spot is a storm bigger than Earth.",
            "The Sun contains 99.86% of the solar system’s mass.",
            "One spoonful of neutron star weighs a billion tons.",
            "Uranus rotates on its side, unlike other planets.",
            "A year on Mercury is just 88 Earth days.",
            "Saturn’s moon Enceladus has ice volcanoes.",
            "Light from the Sun takes 8 minutes to reach Earth.",
            "The Milky Way is on a collision course with Andromeda.",
            "Black holes can slow down time.",
            "Mars has the largest dust storms in the solar system.",
            "Venus is the hottest planet, not Mercury.",
            "You would weigh less on the Moon than on Earth.",
            "Pulsars emit beams of radiation detectable from Earth.",
            "The Kuiper Belt is home to many dwarf planets.",
            "There are more stars in the universe than grains of sand on Earth.",
            "Pluto has a heart-shaped glacier called Tombaugh Regio.",
            "The International Space Station travels 28,000 km/h.",
            "The closest star system is Alpha Centauri, 4.37 light years away.",
            "Oumuamua was the first known interstellar object in our solar system.",
            "The Moon is slowly drifting away from Earth at 3.8 cm/year."
        ]
        print(Fore.CYAN + "\n Random Space Trivia")
        for fact in random.sample(trivia_facts, 5):
            print("- " + fact)
