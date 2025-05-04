"""App to randomly generate nicknames to avoid dupes"""
import random
from builtins import str


def generate_nickname() -> str:
    """Generate a URL-safe nickname using adjectives and animal names."""
    adjectives = ["clever", "jolly", "brave", "sly", "gentle"]
    animals = ["panda", "fox", "raccoon", "koala", "lion"]
    number = random.randint(0, 999)
    return f"{random.choice(adjectives)}_{random.choice(animals)}_{number}"
