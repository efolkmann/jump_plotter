#!/bin/env python

import itertools as its
import operator as op
from array import array


def select_instrument(data, cols):

    """Selects specific columns from a dataset and returns them as
    a tuple.

    Args:
        data (list): The dataset to select columns from.  slc (slice):

        The slice object specifying which columns to select.  cols (list):
        A list of column indices to select.

    Returns:
        tuple: A tuple containing the selected columns from the dataset.

    Raises:
        TypeError: If the data is not a list or the slice is not a valid
        slice object.
        IndexError: If any of the column indices are out of range.

    Example:
        >>> data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> select_instrument(data, slice(0, 2), [0, 2]) ([1, 3], [7, 9])
    """
    cols = map(op.itemgetter(*cols), data)
    cols = map(map, its.repeat(float), cols)
    cols = zip(*cols)
    cols = map(array, its.repeat('d'), cols)
    cols = tuple(cols)
    return cols


def select_time(data, time):
    """ Selects a specific time from a given dataset.

    Parameters:
        data (list): The dataset to be searched.  slc (slice): The slice
        of the dataset to be selected.  time (str): The specific time
        to be selected.

    Returns:
        time (array): An array containing the selected time from the
        dataset.

    Raises:
        TypeError: If the data is not a list or the slice is not a valid
        slice object.
        ValueError: If the time is not a valid time in
        the dataset.
    """
    # Check if data is a tuple
    if not isinstance(data, tuple):
        raise TypeError("Data must be a tuple.")

    # Select the specific time from the dataset
    time = map(op.itemgetter(time), data)
    time = map(float, time)
    time = map(op.truediv, time, its.repeat(1000))
    time = array('d', time)
    return time


def diff(arr):
    # Check input type
    if not isinstance(arr, array):
        raise TypeError("Input must be an array.")

    # Check input length
    if len(arr) == 0:
        raise ValueError("Input array cannot be empty.")

    # Calculate absolute values of input array
    arr = map(abs, arr)

    # Convert input array to array of type 'd'
    arr = array('d', arr)

    # Initialize output array with NaN values
    out = array('d', [float('nan')] * len(arr))

    # Calculate difference between consecutive elements
    a = arr[1:]
    a = map(op.sub, a, its.repeat(min(arr)))
    a = map(op.truediv, a, its.repeat(max(arr)))

    b = arr[:-1]
    b = map(op.sub, b, its.repeat(min(arr)))
    b = map(op.truediv, b, its.repeat(max(arr)))

    reg = map(op.sub, a, b)
    reg = map(abs, reg)
    reg = array('d', reg)

    # Assign calculated values to output array
    out[1:] = reg

    return out


def calc_jyl(accl, gyro):
    """Calculates the jerk, yaw, and lateral acceleration of a given
    accelerometer and gyroscope data.

    Args:
        accl (list): A list of accelerometer data.  gyro (list): A list
        of gyroscope data.
    Returns:
        jyl (array): An array containing the calculated jerk, yaw,
        and lateral acceleration values.

    Raises:
        None.
    """
    jyl_a = map(diff, accl)
    jyl_a = map(sum, zip(*jyl_a))
    jyl_a = array('d', jyl_a)
    jyl_g = map(diff, gyro)
    jyl_g = map(sum, zip(*jyl_g))
    jyl_g = array('d', jyl_g)
    jyl = map(op.add, jyl_a, jyl_g)
    jyl = array('d', jyl)
    return jyl
