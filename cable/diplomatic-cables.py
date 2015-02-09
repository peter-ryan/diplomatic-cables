from HTMLParser import HTMLParser
import re
import requests


class CountryData(object):
    def __init__(self):
        super(CountryData, self).__init__()
        self.name = None
        self.state = None

    def need_orders(self):
        return self.state not in [None, "Completed", "Ready"]

    def __repr__(self):
        return self.__dict__.__repr__()


class GameParser(HTMLParser):
    def __init__(self, game_id):
        HTMLParser.__init__(self)
        self.game_id = game_id
        self.time_remaining = None
        self.countries = {}
        self.current_country_data = None
        self.in_left_side = None
        self.country_name_next = False
        self.game_phase_next = False
        self.game_date_next = False
        game_url = "http://webdiplomacy.net/board.php?gameID={}".format(game_id)
        self.feed(requests.get(game_url).text)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)

        tag_class = attributes.get("class")
        if tag_class == "memberLeftSide":
            self.current_country_data = CountryData()

        if tag_class == "timeremaining":
            self.time_remaining = int(attributes['unixtime'])

        if tag_class == "gamePhase":
            self.game_phase_next = True
            return

        if tag_class == "gameDate":
            self.game_date_next = True
            return

        if not self.current_country_data:
            return

        if tag_class:
            match = re.match("country([1-7])\s+memberStatus(\w+)", tag_class)
            if match:
                player_id, status = match.groups()
                self.current_country_data.player_id = player_id
                self.current_country_data.status = status
                self.country_name_next = True

        if tag == "img":
            country_state = attributes.get("alt")
            self.current_country_data.state = country_state

    def handle_data(self, data):
        if self.country_name_next:
            self.current_country_data.name = data
            self.country_name_next = False

        if self.game_phase_next:
            self.phase = data
            self.game_phase_next = False

        if self.game_date_next:
            self.game_date = data
            self.game_date_next = False

    def handle_endtag(self, tag):
        if tag == "td" and self.current_country_data:
            self.countries[self.current_country_data.name] = self.current_country_data
            self.current_country_data = None

    def game_status(self):
        return GameStatus(self.game_id, self.phase, self.game_date, self.time_remaining, self.countries)


class GameStatus(object):
    def __init__(self, game_id, phase, game_date, time_remaining, countries):
        super(GameStatus, self).__init__()
        self.game_id = game_id
        self.time_remaining = time_remaining
        self.countries = countries
        self.phase = phase
        self.game_date = game_date

    def __repr__(self):
        return self.__dict__.__repr__()

    def need_orders(self):
        return filter(lambda s: s.need_orders(), self.countries.values())


def main():
    game_id = "151938"
    game_status = GameParser(game_id).game_status()
    print game_status.need_orders()


if __name__ == "__main__":
    main()