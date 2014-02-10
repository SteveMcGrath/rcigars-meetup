from bottle import Bottle, request, response, redirect, static_file, error
from jinja2 import Environment, FileSystemLoader
from urllib import urlencode
from time import mktime
from datetime import datetime
from ConfigParser import ConfigParser
import os
import feedparser

# First we set a few parameters.  Mostly boilerplate stuff that we will use
# throughout the app.
path = os.path.dirname(os.path.abspath(__file__))
env = Environment(
    lstrip_blocks=True,
    trim_blocks=True,
    loader=FileSystemLoader(os.path.join(path, 'templates'))
)
app = Bottle()

# Lets go ahead and read in the configuration file...
config = ConfigParser()
config.read(os.path.join(path, 'app.conf'))
base_url = config.get('RSS Feed', 'base_url')

# Then we need to populate the RSS query information from the RSS Feed section
# of the config file.
query = {}
for option in config.options('RSS Feed'):
    if option is not 'base_url':
        query[option] = config.get('RSS Feed', option)

# Next we populate the location-specific information...
locations = {}
for section in config.sections():
    if 'LOCATION: ' in section:
        locations[section.split(': ')[1].lower()] = config.get(section, 'search')


def get_entries(location):
    '''
    Returns the subset of the data that pertains to the location specified. 
    Further it will only return recent items that have been created within
    the last 30 days.
    '''
    # Look mo, its a empty list!
    data = []

    # instantiate query and replace the {DATA} tag with the localized query.
    q = query.copy()
    q['q'] = q['q'].replace('{DATA}', config.get('LOCATION: %s' % location,
                                                 'search'))
    # generate the rss_url
    rss_url = base_url + urlencode(q)
    print rss_url
    for entry in feedparser.parse(rss_url).entries:
        print entry.title
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
        locations=[i.split(': ')[1] for i in config.sections() if 'LOCATION: ' in i]
    )


@app.get('/<location>')
def location_meetups(location):
    return env.get_template('location.html').render(
        feed=get_entries(location),
        locations=locations
    )


if __name__ == '__main__':
    print locations
    app.run(
        port=config.get('Settings', 'port'),
        host=config.get('Settings', 'host'),
        server=config.get('Settings', 'app_server'),
        reloader=config.getboolean('Settings', 'debug')
    )