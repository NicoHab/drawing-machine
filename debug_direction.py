#!/usr/bin/env python3
"""Debug direction calculation"""

from cloud.data_aggregator.motor_command_generator import MotorCommandGenerator

generator = MotorCommandGenerator()

test_cases = [0.0, 25.0, 50.0, 75.0, 100.0]

for util in test_cases:
    rpm, direction = generator._calculate_utilization_based_motor(util)
    print(f"{util:5.1f}% -> {rpm:4.1f} RPM {direction} (value: {direction.value})")