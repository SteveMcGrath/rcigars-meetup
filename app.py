from bottle import Bottle, request, response, redirect, static_file, error
from jinja2 import Environment, FileSystemLoader
from urllib import urlencode
from time import mktime
from datetime import datetime
from ConfigParser import ConfigParser
import os
import feedparser

# This is the base URL that will be used for all Reddit searches.  Location
# specific criteria will be replaced with the {DATA} tag when needed.
base_url = 'http://www.reddit.com/search.xml?'
query = {
    'q': 'subreddit:cigars {DATA} AND (title:herf OR title:meetup)',
    'restrict_sr': 'off',
    'sort': 'new',
    't': 'all',
}

# Location-specific search criteria are entered here.
locations = {
    'chicago': '(title:chicago OR title:"casa de montecristo" OR title:tesa)',
}

path = os.path.dirname(os.path.abspath(__file__))
env = Environment(
    lstrip_blocks=True,
    trim_blocks=True,
    loader=FileSystemLoader(os.path.join(path, 'templates'))
)
app = Bottle()


def get_entries(location):
    '''
    Returns the subset fo the data that pertains to the location specified. 
    Further it will only return recent items that have been created within
    the last 30 days.
    '''
    # Look mo, its a empty list!
    data = []

    # instantiate query and replace the {DATA} tag with the localized query.
    q = query
    q['q'] = q['q'].replace('{DATA}', locations[location])
    # generate the rss_url
    rss_url = base_url + urlencode(q)
    for entry in feedparser.parse(rss_url).entries:
        # convert the timestamp into a datetime object then check to make sure
        # that the timestamp is no more than 30 days old before adding into the
        # feed.
        publishdate = datetime.fromtimestamp(mktime(entry.published_parsed))
        if (datetime.now() - publishdate).days <= 30:
            data.append(entry)
    return data


@app.get('/static/<location:path>')
def static_files(location):
    return static_file(location, root=os.path.join(path, 'static'))


@app.get('/favicon.ico')
def favicon():
    return static_file('favicon.ico', root=os.path.join(path, 'static'))


@app.get('/')
def main_page():
    return env.get_template('index.html').render(
        locations=locations
    )


@app.get('/<location>')
def location_meetups(location):
    return env.get_template('location.html').render(
        feed=get_entries(location.lower()),
        locations=locations
    )


if __name__ == '__main__':
    config = ConfigParser()
    config.read(os.path.join(path, 'app.conf'))
    app.run(
        port=config.get('Settings', 'port'),
        host=config.get('Settings', 'host'),
        server=config.get('Settings', 'app_server'),
        reloader=config.getboolean('Settings', 'debug')
    )