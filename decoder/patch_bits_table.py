import csv
from collections import defaultdict

from decoder.lib.diff import compare


def read_params_file(file):
    effects = defaultdict(lambda: defaultdict(list))

    with open(file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        current_effect = 0
        current_param = 0

        for row in csv_reader:
            if len(row) == 2:
                current_effect, current_param = int(row[0]), int(row[1])
                continue

            message = [int(e) for e in row]
            effects[current_effect][current_param].append(message)

    return effects


def read_effect_status_file(file):
    effects = defaultdict(list)

    with open(file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        current_effect = 0

        for row in csv_reader:
            if len(row) == 1:
                current_effect = int(row[0])
                continue

            message = [int(e) for e in row]
            effects[current_effect].append(message)

    return effects


def filter_data(param_data):
    # Filter all responses with len(data) > 40 and ignore tail (checksum)
    data = [d[:113] for d in param_data if len(d) > 40]
    return data[0], data[1:]


def position(diff):
    offset = diff.position + 1
    bit_position = bin(diff.mask).count("0") - 1

    return offset, bit_position


# pip install numpy
import numpy as np

effects = read_params_file('decoder/data_params.csv')

pedalboard_data = np.zeros((119, 8), dtype=object)


for effect_index, effect in effects.items():
    for param_index, param_data in effect.items():
        data_base, data = filter_data(param_data)

        for bit, data_i in enumerate(data):
            diffs = compare(data_base, data_i)

            if len(diffs) != 1:
                raise Exception(f'More than one changes are detected for effect {effect_index} param {param_index}. Why? {diffs}')

            offset, bit_position = position(diffs[0])
            information = f'{effect_index}p{param_index}b{bit}'

            if pedalboard_data[offset, bit_position] != 0:
                raise Exception(f'Try populate {information} in {[offset, bit_position]}, '
                                f'but the position already in use: {pedalboard_data[offset, bit_position]}. '
                                f'Please try rescan configurations with bigger sleep time.')

            pedalboard_data[offset, bit_position] = information


effects = read_effect_status_file('decoder/data_effects_status.csv')
for effect_index, effect in effects.items():
    data_base, data = filter_data(effect)

    diffs = compare(data_base, data[0])

    if len(diffs) != 1:
        raise Exception(f'More than one changes are detected for effect {effect_index}. Why? {diffs}')

    offset, bit_position = position(diffs[0])
    information = f'{effect_index}EfOn'

    if pedalboard_data[offset, bit_position] != 0:
        raise Exception(f'Try populate {information} in {[offset, bit_position]}, '
                        f'but the position already in use: {pedalboard_data[offset, bit_position]}. '
                        f'Please try rescan configurations with bigger sleep time.')

    pedalboard_data[offset, bit_position] = information


# Left to right
pedalboard_data_ltor = np.flip(pedalboard_data, axis=1)
print(pedalboard_data_ltor)
np.savetxt('decoder/table.csv', pedalboard_data_ltor, '%s', delimiter=',')