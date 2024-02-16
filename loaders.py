#!/bin/env python

import os
import re
import csv
import configparser
import itertools as its
import operator as op
import random

import browse_rto as rto


def load_ecf(instance):
    config = configparser.ConfigParser()
    config.read('./plot.conf')
    rto_mount = config['paths']['rto']
    ecf = rto.browse_events(rto_mount)
    ecf = filter(lambda x: instance in x, ecf)
    ecf = next(ecf, None)
    handle = open(ecf, 'r')
    reader = csv.DictReader(handle)
    data = tuple(reader)
    handle.close()
    return data


def already_complete():
    config = configparser.ConfigParser()
    config.read('./plot.conf')
    output_path = config['paths']['output']
    if os.path.exists(output_path):
        output_handle = open(output_path, 'r')
        reader = csv.DictReader(output_handle)
        done = map(op.itemgetter('pkey'), reader)
        done = tuple(done)
        output_handle.close()
    else:
        done = ()
    return done


#def make_primary_key(jump_dict):
#    pkey = '_'.join([jump_dict['file'], jump_dict['idx']])
#    return pkey
#
#
#def add_primary_key(jump_dict):
#    jump_dict['pkey'] = make_primary_key(jump_dict)
#    return jump_dict


def read_csv(file):
    config = configparser.ConfigParser()
    config.read('./plot.conf')
    subsample = config.getint('params', 'subsample')
    handle = open(file, 'r')
    reader = csv.DictReader(handle)
    data = tuple(reader)
    data = its.islice(data, 0, None, subsample)
    data = tuple(data)
    handle.close()
    return data


def load_jumps(config):
    jump_file = config['paths']['jump_bins']
    jump_handle = open(jump_file, 'r')
    jump_data = csv.DictReader(jump_handle)
#    jump_data = map(add_instance, reader)
#    jump_data = map(add_primary_key, jump_data)
    jump_data = sorted(jump_data, key=op.itemgetter('file', 'jump_idx'))
    jump_data = tuple(jump_data)
    jump_handle.close()
    return jump_data


def load_data(files):
    data = map(read_csv, files)
    data = tuple(data)
    return data


def get_work(config, jump_data):
    def in_window(jump):
        foo = jump['in_ev_window']
        return op.eq(foo, 't')

    jump_data = filter(in_window, jump_data)
    complete = already_complete()
    jump_data = filter(lambda x: x['pkey'] not in complete, jump_data)
    jump_data = filter(lambda x: '_3M_' in x['csv_path'], jump_data)
    jump_data = tuple(jump_data)
    return jump_data


def interrater_validation(config):

    def filt(pair):
        A, B = pair
        return op.eq(A['instance'], B)

    # Interrater round one
    selection = ('BF032_12M',
                 'LF292_12M',
                 'LH294_1M',
                 'LG293_3M',
                 'CG059_6M',
                 'LC289_9M',
                 'CF058_12',
                 'BO041_3M',
                 'AI009_2W',
                 'LE291_2W')

    # Interrater round two
    selection = ('CE057_4M',
                 'CS071_6M',
                 'CW075_6M',
                 'AZ026_6M',
                 'DD082_P38W',
                 'DS097_3M',
                 '115-111_3M',
                 'BL038_3M-2',
                 'BU047_6M',
                 'BH034_3M')


    # Interrater round three
    selection = ('AA001_9M',
                 'BT046_2W',
                 'DE083_3M',
                 'LB288_3M',
                 'UB522_1M',
                 'UG522_3M',
                 'AR018_9M',
                 'BV048_2W',
                 'CO067_1M',
                 'EP120_6M',)

    # Interrater round three meeting

    selection = ('UB522_1M',
                 'CO067_1M',)


    jump_data = load_jumps(config)

    iterable = its.product(jump_data, selection)
    jump_data = filter(filt, iterable)
    jump_data = map(op.itemgetter(0), jump_data)
    jump_data = tuple(jump_data)
    return jump_data



def add_instance(jump_dict):
    instance = jump_dict['file']
    instance = instance.split('_')
    instance = instance[0:2]
    instance = '_'.join(instance)
    jump_dict['instance'] = instance
    return jump_dict


def find_files(instance):
    config = configparser.ConfigParser()
    config.read('./plot.conf')
    rto_mount = config['paths']['rto']
    files = rto.browse_sensors(rto_mount)
    pat = re.compile(instance)
    files = filter(pat.search, files)
    files = sorted(files)
    return files


def select_one(jump_data):
    instances = map(op.itemgetter('instance'), jump_data)
    instances = tuple(set(instances))
    instance = random.choice(instances)
    jump_data = filter(lambda x: x['instance'] == instance, jump_data)
    jump_data = sorted(jump_data, key=op.itemgetter('file', 'jump_idx'))
    jump_data = tuple(jump_data)
    return jump_data



def main():
    config = configparser.ConfigParser()
    config.read('./plot.conf')

#    jump_data = get_work(config)
#    for d in jump_data:
#        print(d)
#    breakpoint()
    jump_data = load_jumps(config)
    jump_data = interrater_validation(config)
    jump_data = get_work(config, jump_data)
    jump_data = select_one(jump_data)
#    for d in jump_data:
#        print(d)
    breakpoint()
    return None

if __name__ == '__main__':
    main()
