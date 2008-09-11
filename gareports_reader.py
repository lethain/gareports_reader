"""
This library is used for parsing data from  Google Analytics reports saved in XML format.

    >>> from gareports_reader import GoogleAnalyticsReportParser
    >>> fin = open('lethain.xml','r')
    >>> data = GoogleAnalyticsReportParser(fin.read())
    >>> fin.close()
    >>> dir(data)
    ['__class__', '__delattr__', '__dict__', '__doc__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__str__', '__weakref__', 'contents', 'dates', 'domain', 'end', 'et', 'known_report_types', 'pageviews', 'parse_dashboard', 'start', 'type']
    >>> data.domain
    'www.lethain.com'
    >>> data.start
    datetime.datetime(2008, 8, 11, 0, 0)
    >>> data.end
    datetime.datetime(2008, 9, 10, 0, 0)
"""

__AUTHOR__ =  u"Will Larson, <lethain@gmail.com>"
__COPYRIGHT__ = u"Copyright (c) 2008 Will Larson <lethain@gmail.com> and Button Down Design, LLC."
__LICENSE__ = u"Released under the MIT License."

import re, time, datetime, StringIO
try:
    import elementtree.ElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree


SPARKLINE_NAME_REGEX = re.compile("(?P<type>\w+)Sparkline")


class UnknownReportTypeException(Exception):
    pass


class GoogleAnalyticsReportParser(object):
    'Parses Google Analytic reports. Takes an argument of a file or filepath.'
    known_report_types = ("DashboardReport",)
    def __init__(self, filepath):
        self.pageviews = ()
        self.et = ElementTree.parse(StringIO.StringIO(filepath))
        self.type = self.et.find('Report').attrib['name']
        details = self.et.find('Report').find('Title')
        self.domain = details.find('ProfileName').text
        date_range = details.find('PrimaryDateRange').text.split(" - ")
        self.start = datetime.datetime(*time.strptime(date_range[0], "%B %d, %Y")[0:5])
        self.end = datetime.datetime(*time.strptime(date_range[1], "%B %d, %Y")[0:5])

        if self.type =="Dashboard":
            return self.parse_dashboard()
        else:
            raise UnknownReportTypeException("Cannot handle report of type '%s'." % self.type)
 
    def parse_dashboard(self):
        'Parse data from dashboard report.'
        # Duplicates not being parsed: `Bounce`,'Pageview', 'AvgPage'

        types = ('Visits','Pageviews','TimeOnSite','BounceRate','NewVisits',
                 'Visitors','AvgPageviews','TimeOnSite','NewVisitors',
                 'Direct','Referral','Search','Unique')

        def form_sparklines(sparkline):
            if sparkline.attrib.has_key('id'):
                type = SPARKLINE_NAME_REGEX.search(sparkline.attrib['id']).group('type')
                return type, sparkline.findall('PrimaryValue')
            return None

        def form(x):
            return dates.next(), dict((type,sparklines[type][x].text) for type in types)

        diff = abs((self.end - self.start).days)
        dates = (self.start + datetime.timedelta(days=x) for x in xrange(0,diff,1))
        sparklines = tuple(form_sparklines(x) for x in self.et.find('Report').getiterator('Sparkline'))
        sparklines = tuple(x for x in sparklines if x != None)
        sparklines = dict((x[0],x[1]) for x in sparklines)
        self.dates = tuple(form(x) for x in xrange(0,diff,1))
