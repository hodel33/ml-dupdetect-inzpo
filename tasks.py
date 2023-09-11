# Django imports
from core.scraper import Main


def scraper_get_potential_duplicates():

    main = Main()

    ## POTENTIAL DUPLICATES
    main.get_potential_episode_duplicates(mode="new")