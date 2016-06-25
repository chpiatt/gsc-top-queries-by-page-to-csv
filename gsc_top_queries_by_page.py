#!/usr/bin/python
# -*- coding: utf-8 -*-
#
import argparse, sys, os, json, datetime, csv
from googleapiclient import sample_tools

# Default to unicode
reload(sys)
sys.setdefaultencoding('utf8')

# Declare command-line flags.
argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument('start_date', type=str,
                       help=('Optional: start date of the requested date range in '
                             'YYYY-MM-DD format.'), nargs='?')
argparser.add_argument('end_date', type=str,
                       help=('Optional: end date of the requested date range in '
                             'YYYY-MM-DD format.'), nargs='?')

def main(argv):
  service, flags = sample_tools.init(
      argv, 'webmasters', 'v3', __doc__, __file__, parents=[argparser],
      scope='https://www.googleapis.com/auth/webmasters.readonly')

  # Optional: Define specific properties (comma-separated list) for reports. Otherwise, all verified properties will be fetched.
  properties = []

  # Define desired output folder
  folder = 'outputs'

  # Define list of search types. Options: 'web', 'image', and 'video'
  search_types = [
        'web'
  ]

  # If no start date flag specified, set report start date equal to 4 days ago.
  # Google Search Console data is only available after-the-fact, so make sure to offset your start date by several days to ensure data quality.
  if flags.start_date:
      start_date = flags.start_date
  else:
      start_date = (datetime.date.today() - datetime.timedelta(4)).strftime('%Y-%m-%d')

  # If no end date flag specified, set report end date equal to 4 days ago.
  if flags.end_date:
      end_date = flags.end_date
  else:
      end_date = (datetime.date.today() - datetime.timedelta(4)).strftime('%Y-%m-%d')

  # If no properties specified in default args, then get data for all verified properties
  if len(properties) == 0:
    site_list = service.sites().list().execute()

    # Filter for verified websites
    verified_sites_urls = [s['siteUrl'] for s in site_list['siteEntry']
                       if s['permissionLevel'] != 'siteUnverifiedUser'
                          and s['siteUrl'][:4] == 'http']
    properties = verified_sites_urls

  # Create output folder if it doesn't exist already
  if not os.path.exists(folder):
      os.makedirs(folder)

  for web_property in properties:
    for search_type in search_types:

        # Get top queries for the date range, sorted by click count, descending.
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['date', 'page', 'query', 'device'],
            'searchType': search_type,
            'rowLimit': 5000
        }
        print 'Fetching: ' + web_property
        response = execute_request(service, web_property, request)

        if 'rows' not in response:
          print 'Empty response.'
          continue

        # save as csv
        filename = clean_name(web_property) + "-gsc-top-queries-by-page" + ".csv"
        filepath = folder + '/' + filename
        with open(filepath, 'wb') as fp:
            a = csv.writer(fp)
            header = ['date', 'page', 'query', 'device_type', 'clicks', 'impressions', 'ctr', 'position']
            a.writerow(header)
            rows = response['rows']
            for row in rows:
                formattedRow = [row['keys'][0], row['keys'][1], row['keys'][2], row['keys'][3], row['clicks'], row['impressions'], row['ctr'], row['position']]
                a.writerow(formattedRow)

        print 'Successfully created file: ' + filename

def clean_name(str):
  str = str.replace(':', '-')
  str = str.replace('/', '')
  str = str.replace('.', '-')
  return str

def execute_request(service, property_uri, request):
  """
  Executes a searchAnalytics.query request.

  Args:
    service: The webmasters service to use when executing the query.
    property_uri: The site or app URI to request data for.
    request: The request to be executed.

  Returns:
    An array of response rows.
  """
  return service.searchanalytics().query(
      siteUrl=property_uri, body=request).execute()

if __name__ == '__main__':
  main(sys.argv)
