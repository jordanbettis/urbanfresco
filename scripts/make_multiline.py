from nh.core.app import initialize

initialize()

from nh.images.models import Collection
from nh.core.db import Session

COLLECTIONS = (
    ("Goose Island", "Goose\nIsland",),
    ("Heart of Chicago", "Heart of\nChicago",),
    ("Andersonville", "Anderson-\nville",),
    ("Canaryville", "Canary-\nville",),
    ("Marshall Square", "Marshall\nSquare",),
    ("Ravenswood","Ravens-\nwood"),
    ("Washington Park","Washington\nPark"),
    ("Ukranian Village","Ukranian\nVillage"),
    ("Bowmanville","Bowman-\nville"),
    ("Edison Park","Edison\nPark"),
    ("Grand Boulevard","Grand\nBoulevard"),
    ("Grand Crossing","Grand\nCrossing"),
    ("Near South Side", "Near\nSouth\nSide"),
    ("Gold Coast", "Gold\nCoast"),
    ("Cottage Grove", "Cottage\nGrove"),
    ("Oakland", "Oak-\nland"),
    ("Chinatown", "China-\ntown"),
    ("River North", "River\nNorth"),
    ("Pullman", "Pull-\nman"),
    ("Mount Greenwood", "Mount\nGreenwood"),
    ("North Center", "North\nCenter"),
    ("Lincoln Square", "Lincoln\nSquare"),
    ("Fuller Park", "Fuller\nPark"),
    ("Roscoe Village", "Roscoe\nVillage"),
    ("Midway", "Mid-\nway"),
    ("Archer Heights", "Archer\nHeights"),
    ("East Side", "East\nSide"),
    ("Rogers Park", "Rogers\nPark"),
    ("Back of the Yards", "Back of\nthe Yards"),
    ("Marquette Park", "Marquette\nPark"),
    ("Hegewisch", "Hegewisch"),
    ("Hermosa", "Herm-\nosa"),
    ("West Pullman", "West\nPullman"),
    ("Kenwood", "Ken-\nwood"),
    ("McKinley Park", "McKinley\nPark"),
    ("West Elsdon", "West\nElsdon"),
    ("Calumet Heights", "Calumet\nHeights"),
    ("Bronzeville", "Bronze-\nville"),
    ("The Loop", "The\nLoop"),
    ("Montclare", "Mont-\nclare"),
    ("Jefferson Park", "Jefferson\nPark"),
    ("Bucktown", "Buck-\ntown"),
    ("Avalon Park", "Avalon\nPark"),
    ("South Deering", "South\nDeering"),
    ("Brighton Park", "Brighton\nPark"),
    ("Edgewater", "Edge-\nwater"),
    ("Chicago Lawn", "Chicago\nLawn"),
    ("North Park", "North\nPark"),
    ("Wicker Park", "Wicker\nPark"),
    ("Hyde Park", "Hyde\nPark"),
    ("Park Manor", "Park\nManor"),
    ("Lincoln Park", "Lincoln\nPark"),
    ("South Chicago", "South\nChicago"),
    ("Belmont Cragin", "Belmont\nCragin"),
    ("Portage Park", "Portage\nPark"),
    )

def main():
    session = Session()
    for c in COLLECTIONS:
        obj = session.query(Collection).filter(Collection.name==c[0]).first()
        obj.name_multiline=c[1]
        obj.max_line_length = max([len(x) for x in obj.name_multiline.split('\n')])
    session.commit()

if __name__ == "__main__":
    main()
