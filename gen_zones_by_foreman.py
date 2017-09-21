#!/usr/bin/env python
# coding=utf-8
# Generate bind zones from foreman facts by domain
# ./gen_zones_by_foreman.py --url https://<ip> -u ${foreman_user} -p ${foreman_password} --domain ${domain} --postfix .int 2>/dev/null
import json
import requests
import argparse

def get_foreman_hosts(url, user, password, ca, domain_filter='*', per_page=20000):
    url = '{0}/api/v2/hosts'.format(url)
    #search='*.convectix.com'
    data = {
        'search': domain_filter,
        'per_page': per_page
    }
    r = requests.get(url, params=data, auth=(user, password), verify=ca)
    r.raise_for_status()
    return r.json()

def get_foreman_facts(url, user, password, facts, ca, host_filter='*', per_page=20000):
    url = '{0}/api/v2/fact_values'.format(url)

    search = 'host ~ {0} and ({1})'.format(
        host_filter,
        ' or '.join('name={0}'.format(fact) for fact in facts),
    )
    data = {
        'search': search,
        'per_page': per_page
    }
    r = requests.get(url, params=data, auth=(user, password), verify=ca)
    r.raise_for_status()
    return r.json()

def get_args():
    parser = argparse.ArgumentParser(description='get foreman facts')
    parser.add_argument('--url', type=str, required=True, help='foreman base url')
    parser.add_argument('-u', '--user', required=True, type=str, help='user for foreman')
    parser.add_argument('-p', '--password', required=True, type=str, help='password for foreman')
    parser.add_argument('-f', '--facts', required=True, type=str, nargs='+')
    parser.add_argument('--ca', type=str, default=False, help='path to ca for foreman certificate verification')
    parser.add_argument('-o', '--output', type=str, help='result will be atomic writen to provided path in yaml format')
    parser.add_argument('--domain', type=str, default='*', help='domain mask for search nodes')
    parser.add_argument('--max-hosts', type=int, default=2000, help='number of hosts to retrieve from foreman')
    parser.add_argument('--postfix', type=str, default=False, help='postfix for generated name in zones, e.g: --postfix=.int')
    return parser.parse_args()


def main(args):
    host_list = get_foreman_hosts(args.url, args.user, args.password, args.ca, args.domain)
    assert len(host_list) > 1, "Foreman returned more then 1 host: {0}".format(host_list)

    if (args.postfix):
      postfix=args.postfix
    else:
      postfix=''

    host_num=len(host_list['results'])

    for i, host in enumerate(host_list['results']):
      try:
        certname = host_list['results'][i]['certname']
      except:
        certname = ''
      if (certname):
        host_info = get_foreman_facts(args.url, args.user, args.password, args.facts, args.ca, certname)
        assert len(host_info) > 1, "Foreman returned more then 1 host, looks dangerous: {0}".format(host_info)
        try:
          ipaddress = host_info['results'][certname]['ipaddress']
        except:
          ipaddress = ''
        if (ipaddress):
          shortname = certname.split('.')[0]
          print ( shortname + postfix + "\t\t" + "A" + "\t" + ipaddress )


if __name__ == '__main__':
    main(get_args())
