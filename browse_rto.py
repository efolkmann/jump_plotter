#!/bin/env python

import os
import re
import itertools as its
import configparser


def sensor_links(rto_mount):
    """
    Browse sensor validation arm
    """

    p_sub = r"[A-Z]{2}[0-9]{3}"
    p_sub = re.compile(p_sub)

    p_tp = r".*[0-9]+ (Month|Week)(s?)( Part [1-9]+)?"
    p_tp = re.compile(p_tp)

    p_sensor = r"[A-Z]{2}[0-9]{3}_P?[0-9]+[WM](-[0-9]+)?_(tps_)?[MS][1-9]?(-[1-9]+)?_(tps_)?(conv_)?accl_gyro_raw.csv"
    p_sensor = re.compile(p_sensor)

    study_data = "Corbett/Data/StudyData/sensor_original"
    study_data = os.path.join(rto_mount, study_data)
    sub_dirs = os.listdir(study_data)
    for sub_dir in filter(p_sub.match, sub_dirs):
        dir_path = os.path.join(study_data, sub_dir)
        for tp in filter(p_tp.match, os.listdir(dir_path)):
            sensor_files = filter(p_sensor.match,
                                  os.listdir(os.path.join(dir_path, tp)))
            for file in sensor_files:
                sensor = os.path.join(study_data, sub_dir, tp, file)
                yield sensor


def sensor_links_intervention(rto_mount):
    """
    Browse sensor intervention arm
    """
    p_sub = re.compile(r"[1-9]{3}-[0-9]+")
    p_tp = re.compile(r".*[0-9]+ [MW].*")
    p_sensor = re.compile(r".*[0-9]+[MW]_(S[0-9]|M)_accl_gyro_raw.csv")

    study_data = os.path.join(rto_mount,
                              "Project Corbett - Intervention/Data_Assessments/Study_Data")
    sub_dirs = os.listdir(study_data)
    for sub_dir in filter(p_sub.match, sub_dirs):
        dir_path = os.path.join(study_data, sub_dir)
        for tp in filter(p_tp.match, os.listdir(dir_path)):
            if 'part' in tp.lower():
                continue
            sensor_files = filter(p_sensor.match,
                                  os.listdir(os.path.join(dir_path, tp)))
            for file in sensor_files:
                sensor = os.path.join(study_data, sub_dir, tp, file)
                yield sensor

def browse_sensors(rto_mount):
    """
    Browse sensor validation arm
    """
    iterable = its.chain(sensor_links(rto_mount),
                         sensor_links_intervention(rto_mount))
    for link in iterable:
        yield link




def event_links_intervention(rto_mount):
    """
    Create shortcuts to event files
    """

    config = configparser.ConfigParser()
    config.read("./pc.conf")

    p_sub = re.compile(r"[1-9]{3}-[0-9]+")
    p_tp = re.compile(r".*[0-9]+ [MW].*")
    p_event = re.compile(r"[0-9]{3}-[0-9]*_[0-9]+[MW]_ECF.csv")
    study_data = "Project Corbett - Intervention/Data_Assessments/Study_Data"
    study_data = os.path.join(rto_mount, study_data)
    sub_dirs = os.listdir(study_data)
    for sub_dir in filter(p_sub.match, sub_dirs):
        subdir_path = os.path.join(study_data, sub_dir)
        for tp in filter(p_tp.match, os.listdir(subdir_path)):
            tp_dir = os.path.join(study_data, sub_dir, tp)
            tp_files = os.listdir(tp_dir)
            event_file = filter(p_event.match, tp_files)
            event_file = next(event_file, None)
            if not event_file:
                continue
            else:
                event = os.path.join(tp_dir, event_file)
                yield event


def event_links(rto_mount):
    """
    Create shortcuts to event files
    """
    config = configparser.ConfigParser()
    config.read("./pc.conf")

    p_sub = r"[A-Z]{2}[0-9]{3}"
    p_sub = re.compile(p_sub)

    p_tp = r".*[0-9]+ (Month|Week)(s?)( Part [1-9]+)?"
    p_tp = re.compile(p_tp)

    p_event = r"[A-Z]{2}[0-9]{3}_[MS][1-9]?(-[1-9]+)?_accl_gyro_raw.csv"
    p_event = re.compile(r".*ECF.csv")

    study_data = "Corbett/Data/StudyData/sensor_original"
    study_data = os.path.join(rto_mount, study_data)
    sub_dirs = os.listdir(study_data)
    for sub_dir in filter(p_sub.match, sub_dirs):
        subdir_path = os.path.join(study_data, sub_dir)
        for tp in filter(p_tp.match, os.listdir(subdir_path)):
            tp_dir = os.path.join(study_data, sub_dir, tp)
            tp_files = os.listdir(tp_dir)
            event_file = filter(p_event.match, tp_files)
            event_file = next(event_file, None)
            if not event_file:
                continue
            else:
                event = os.path.join(tp_dir, event_file)
                yield event


def browse_events(rto_mount):
    """
    Create shortcuts to event files
    """
    iterable = its.chain(event_links(rto_mount),
                         event_links_intervention(rto_mount))
    for link in iterable:
        yield link



def is_shrd_dir(path):
    A = 'shrd' in path.lower()
    B = os.path.isdir(path)
    return A and B

def shrd_validation(rto_mount):

    p_sub = r"[A-Z]{2}[0-9]{3}"
    p_sub = re.compile(p_sub)

    p_tp = r".*[0-9]+ (Month|Week)(s?)( Part [1-9]+)?"
    p_tp = re.compile(p_tp)

    p_shrd = r".*\.shrd"
    p_shrd = re.compile(p_shrd)

    study_data = "Corbett/Data/StudyData/sensor_original"
    study_data = os.path.join(rto_mount, study_data)
    sub_dirs = os.listdir(study_data)
    for sub_dir in filter(p_sub.match, sub_dirs):
        dir_path = os.path.join(study_data, sub_dir)
        for tp in filter(p_tp.match, os.listdir(dir_path)):
            tp_path = os.path.join(dir_path, tp)
            shrd_dirs = map(os.path.join, its.repeat(tp_path), os.listdir(tp_path))
            shrd_dirs = filter(is_shrd_dir, shrd_dirs)
            shrd_dir = next(shrd_dirs, None)
            if shrd_dir:
                shrd_files = filter(p_shrd.match,
                                      os.listdir(os.path.join(dir_path, shrd_dir)))
            else:
                shrd_files = filter(p_shrd.match,
                                      os.listdir(os.path.join(dir_path, tp)))
            for file in shrd_files:
                shrd = os.path.join(study_data, sub_dir, tp, shrd_dir, file)
                yield shrd

def shrd_intervention(rto_mount):
    """
    Browse sensor intervention arm
    """
    p_sub = re.compile(r"[1-9]{3}-[0-9]+")
    p_tp = re.compile(r".*[0-9]+ [MW].*")
    p_shrd = r".*\.shrd"
    p_shrd = re.compile(p_shrd)

    study_data = os.path.join(rto_mount,
                              "Project Corbett - Intervention/Data_Assessments/Study_Data")
    sub_dirs = os.listdir(study_data)
    for sub_dir in filter(p_sub.match, sub_dirs):
        dir_path = os.path.join(study_data, sub_dir)
        for tp in filter(p_tp.match, os.listdir(dir_path)):
            if 'part' in tp.lower():
                continue
            tp_path = os.path.join(dir_path, tp)
            shrd_dirs = map(os.path.join, its.repeat(tp_path), os.listdir(tp_path))
            shrd_dirs = filter(is_shrd_dir, shrd_dirs)
            shrd_dir = next(shrd_dirs, None)
            if shrd_dir:
                shrd_files = filter(p_shrd.match,
                                      os.listdir(os.path.join(dir_path, shrd_dir)))
            else:
                shrd_files = filter(p_shrd.match,
                                      os.listdir(os.path.join(dir_path, tp)))
            shrd_files = filter(p_shrd.match,
                                  os.listdir(os.path.join(dir_path, tp)))
            for file in shrd_files:
                shrd = os.path.join(study_data, sub_dir, tp, file)
                yield shrd

def browse_shrds(rto_mount):
    """
    Browse sensor validation arm
    """
    iterable = its.chain(shrd_validation(rto_mount),
                         shrd_intervention(rto_mount))
    for link in iterable:
        yield link

