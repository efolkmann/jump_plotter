#!/bin/env python

import os
import configparser
import matplotlib.pyplot as plt
import itertools as its
import operator as op
from array import array
import json

import read_data as rdt

event_names = {'1': 'supine',
               '2': 'prone',
               '3': 'sitting',
               '4': 'vsus',
               '5': 'pull2sit',
               '6': 'standing',
               '7': 'calibration',
               '8': 'end',
               '100': 'gravity'}

event_colors = {'1': 'C0',
                '2': 'C1',
                '3': 'C2',
                '4': 'C3',
                '5': 'C4',
                '6': 'C5',
                '7': 'C6',
                '8': 'C7',
                '100': 'C8',
                '101': 'C9',
                '102': 'C10'}


def lookup_fw_version(file, fw_versions):
    file = os.path.basename(file)
    fw_version = filter(lambda x: x['sens'] == file, fw_versions)
    fw_version = next(fw_version, {})
    if 'fw_ver' in fw_version:
        version = fw_version['fw_ver']
    else:
        version = None
    return version

def test_489_condition(file, fw_versions):
    fw_version = lookup_fw_version(file, fw_versions)
    is_ammonitor = op.eq(fw_version, 'N/A')
    is_S = op.contains(file, '_S')
    return op.and_(is_ammonitor, is_S)




def plot_files(data, files,  ecf, session, axis):
    config = configparser.ConfigParser()
    config.read('./plot.conf')
    fw_handle = config['paths']['fw_vers']
    fw_handle = open(fw_handle, 'r')
    fw_versions = json.load(fw_handle)
    fw_handle.close()
    subsample = config.getint('params', 'subsample')
    page_size = config.getint('params', 'page_size')
    page_size = op.floordiv(page_size, subsample)

    axis_n = ord(axis) - ord('X')
    keys = data[0][0].keys()
    instance = session[0]['instance']

    accl_keys = filter(lambda x: 'accl' in x.lower(), keys)
    accl_keys = tuple(accl_keys)
    gyro_keys = filter(lambda x: 'velo' in x.lower(), keys)
    gyro_keys = tuple(gyro_keys)
    time_key = filter(lambda x: 'time' in x.lower(), keys)
    time_key = next(time_key)

    fig, axs = plt.subplots(3, 1, sharex=True, sharey=True, figsize=(16, 9))
    fig.suptitle(instance)
    fig.supxlabel('Time (s)')
    for ii, (file, datum,) in enumerate(zip(files, data)):


        time = rdt.select_time(datum, time_key)
        accl = rdt.select_instrument(datum, accl_keys)
        gyro = rdt.select_instrument(datum, gyro_keys)

        add_489 = test_489_condition(file, fw_versions)
        if add_489:
            time = map(op.add, time, its.repeat(489/1000))
            time = array('d', time)

        jyl = rdt.calc_jyl(accl, gyro)
        jyl_max = max(jyl[1:])
        jyl = map(op.truediv, jyl, its.repeat(jyl_max))
        jyl = map(op.add, jyl, its.repeat(ii))
        jyl = array('d', jyl)

        accl = accl[axis_n]
        accl = map(op.truediv, accl, its.repeat(10))
        accl = map(op.add, accl, its.repeat(ii))
        accl = array('d', accl)

        gyro = gyro[axis_n]
        gyro = map(op.truediv, gyro, its.repeat(1200))
        gyro = map(op.add, gyro, its.repeat(ii))
        gyro = array('d', gyro)

        axs[0].plot(time, accl)
        axs[0].set_ylabel(f'Accl {axis} (dimensionless)')
        axs[0].set_ylim(-1, len(data))
        axs[0].set_yticklabels([])
        if add_489:
            axs[0].annotate('489', xy=(0, ii), color='black')

        axs[1].plot(time, gyro)
        axs[1].set_ylabel(f'Gyro {axis} (dimensionless)')
        axs[1].set_ylim(-1, len(data))
        axs[1].set_yticklabels([])

        for jump_no, jump_record in enumerate(session):
            if check_for_jumps(file, jump_record):
                idx = int(jump_record['idx'])
                idx = op.floordiv(idx, subsample)
                # _bin = int(jump_record['bin'])
                slc = slice(idx, idx+page_size)

                color = list(event_colors.keys())[ii]
                color = event_colors[color]

                axs[0].plot(time[slc], accl[slc], color='black', lw=0.75)
                axs[0].annotate(f'{jump_no}',
                                xy=(time[idx], accl[idx]*1.05),
                                color='black',
                                )
                axs[1].plot(time[slc], gyro[slc], color='black', lw=0.75)
                axs[2].plot(time, jyl, color=color)
        axs[2].set_yticklabels([])
        axs[2].set_ylim(-1, len(data))
        axs[2].set_ylabel('JYL (dimensionless)')

    for event_pair in get_events(ecf):
        event = event_pair[0]['Event']
        if event in event_names.keys():
            event_name = event_names[event]
            event_color = event_colors[event]
        else:
            event_color = 'black'
        t0 = event_pair[0]['Sensor Time(ms)']
        t0 = float(t0)/1000
        t = event_pair[1]['Sensor Time(ms)']
        t = float(t)/1000
        for ax in axs:
            ax.fill_betweenx((-1, len(data)),
                             t0, t,
                             color=event_color, alpha=0.25)
    plt.show()
    return fig


def iterate_axes():
    axes = ('X', 'Y', 'Z')
    for axis in its.cycle(axes):
        yield axis


def check_for_jumps(file, jump_record):
    return op.contains(file, jump_record['file'])

def get_events(ecf):
    for pair in filter(is_event, its.pairwise(ecf)):
        yield pair


def is_event(pair):
    A = op.ne(pair[0]['Event'], '8')
    B = op.eq(pair[1]['Event'], '8')
    return op.and_(A, B)

