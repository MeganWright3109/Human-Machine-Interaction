# !/usr/bin/env python3
'''COM2009-3009 EV3DEV TEST PROGRAM'''

# Connect left motor to Output C and right motor to Output B
# Connect an ultrasonic sensor to Input 3
import math
import matplotlib.pyplot as plt
from matplotlib import style
import time
import numpy as np
import random
import os


# Global Variables

m_n = 0
m_oldM = 0
m_newM = 0
m_oldS = 0
m_newS = 0
integral_left = 0
integral_right = 0
last_error_left = 0
last_error_right = 0
derivative_left = 0
derivative_right = 0
start_time = time.time()
end_time = time.time()


class RunningStats:
    # The following are to calculate the running stats
    m_n = 0
    m_oldM = 0
    m_newM = 0
    m_oldS = 0
    m_newS = 0

    # @staticmethod
    def push(self, x):
        global m_n, m_oldM, m_newM, m_oldS, m_newS
        m_n = m_n + 1

        if (m_n == 1):
            # Double check it
            # TODO
            m_newM = x
            m_oldM = x
            m_oldS = 0.0
        else:
            m_newM = m_oldM + (x - m_oldM)/m_n
            m_newS = m_oldS + (x - m_oldM)*(x - m_newM)
            # set up for next iteration
            m_oldM = m_newM
            m_oldS = m_newS

    # Calculates the running variance
    @staticmethod
    def variance():
        global m_n, m_oldM, m_newM, m_oldS, m_newS
        # Changed to greater or equals to make sure that the value will
        # be different than 0
        # When the variable is greater, returns the equation
        if (m_n >= 1):
            return (m_newS)/(m_n-1)
        else:
            return 0.0

    # Calculates the running standard deviation

    def standard_deviation(self):
        global m_n, m_oldM, m_newM, m_oldS, m_newS
        return math.sqrt(RunningStats.variance())

    # Calculates the running mean
    def mean(self):
        global m_n, m_oldM, m_newM, m_oldS, m_newS
        # Changed to greater or equals to make sure that the value will be
        # different than 0
        if (m_n >= 1):
            return m_newM
        else:
            return 0.0


def create_file(light_sensor_left, light_sensor_right, offset):
    global start_time, end_time

    # Create the time variable
    end_time = time.time()
    # Calculate the necessary time to get the values from the light sensor
    time_taken = end_time - start_time

    l = open("robot_left.txt", "a+")
    r = open("robot_right.txt", "a+")
    d = open("offset.txt", "a+")
    string_value_left = str("%.2f" % time_taken)+"," + str(light_sensor_left)+"\n"
    l.write(string_value_left)
    string_value_right = str("%.2f" % time_taken)+"," + str(light_sensor_right)+"\n"
    r.write(string_value_right)
    d.write(str(offset)+"\n")
    r.close
    l.close
    d.close


def create_graphic():
    x, y_right = np.loadtxt('robot_right.txt', delimiter=',', unpack=True)
    x, y_left = np.loadtxt('robot_left.txt', delimiter=',', unpack=True)
    d = np.loadtxt('offset.txt', unpack=True)

    # Creats a graph on it
    style.use('fivethirtyeight')
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)
    plt.xlabel("Time(s)")
    plt.ylabel("Light Sensor Value")
    ax1.plot(x, y_right, linestyle='', marker="o")
    ax1.plot(x, y_left, linestyle='', marker="x")
    ax1.plot(x, d)
    plt.show()


def select_controller(mode):
    # Using Ku to get a better integral
    Ku = 6
    Tu = 0.3
    if mode == "P":
        print("Running in P mode")
        # Mulitply Kp by 100 to use decimal points
        Kp = 0.6*100
        # Proportional for the Integral
        Ki = 0
        # Proportional for the derivative
        Kd = 0
        return Kp, Ki, Kd
    elif mode == "PI":
        print("Running in PI mode")
        # Mulitply Kp by 100 to use decimal points
        Kp = 0.45*100*Ku
        # Proportional for the Integral
        Ki = (0.54*Ku)/Tu
        # Proportional for the derivative
        Kd = 0
        return Kp, Ki, Kd
    else:
        print("Running in PID mode")
        # Mulitply Kp by 100 to use decimal points
        Kp = 0.6*100*Ku
        # Proportional for the Integral
        Ki = (1.2*Ku)/Tu
        # Proportional for the derivative
        Kd = (3*Ku*Tu)
        return Kp, Ki, Kd

    # Calculates the PID, sets Ki, Kd = 0 if you would like to use only P and so on


def calculate_pid(left_sensor, right_sensor, mode):
    global integral_left, integral_right, last_error_left, last_error_right, derivative_left, derivative_right
    Kp, Ki, Kd = select_controller(mode)
    # In words our conversion is "for every 1
    # unit change in the error we will increase the
    # power of one motor by 10"

    # The value that would be right
    left_sensor = left_sensor/10
    right_sensor = right_sensor/10

    offset = (left_sensor + right_sensor)/2

    # The target power, when the error is 0 the motors will run in this power
    # The target point for when the value is == to the offset value can be
    # higher
    # Therefore, it would be good to have an if statement checking it
    # If the line is pretty straight you can use a large Tp to get the
    # robot running at high speed and a small Kp so the
    # turns (corrections) are gentle.
    Tp = 50

    # Starting the loop>>>>>>

    # This has to read from the robot's left sensor
    error_left = left_sensor - offset
    # This has to read from the robot's left sensor
    error_right = right_sensor - offset
    # It will increase or decrease the error conform the "size" of the integral
    # variable, giving the controller a method to reduce errors over time
    # Another way to don't make the integral to get too big is to do times
    # 2/3, making the integral forget about long term errors
    integral_left = ((2/3)*integral_left) + error_left
    integral_right = ((2/3)*integral_right) + error_right
    # The derivative that tries to see the future error
    derivative_left = error_left - last_error_left
    derivative_right = error_right - last_error_right
    # This is the P, therefore, how much we want to change the velocity
    # of the motor
    # Divide velocity by 100 to decrease from the Kp from before
    velocity_p_left = ((error_left*Kp)+(integral_left*Ki)+(derivative_left*Kd))/100
    velocity_p_right = ((error_right*Kp)+(integral_right*Ki)+(derivative_right*Kd))/100
    print(velocity_p_left)
    print(velocity_p_right)
    # Those are the powers that will be suplied to the motors
    power_right = velocity_p_right + Tp
    power_left = velocity_p_left + Tp

    # Save the last error to be the next error
    last_error_left = error_left
    last_error_right = error_right
    # Check the maximum and minimum power that can be sent to the robot
    # Also check if the motor can receive a negative power
    # Also double check by how far both motors go from a 100
    # If it goes too far, better changing some Tune like Kp or Tp
    if power_left > 100:
        power_left = 100
    elif power_left < -100:
        power_left = -100

    if power_right > 100:
        power_right = 100
    elif power_right < -100:
        power_right = -100

    # Sets the integral to zero when the error is zero
    # That is to make sure that the integral does not get too big
    # if error == 0:
    #     integral = 0
    # debug_print(error)

    # Return the powers of the robots
    # if error >= 0.5 or error <= 0.5:
    return power_left, power_right
    # else:
    # return 0, 0
    # debug_print(error)


def test_no_robot():
    value = 0
    while value <= 100:
        random_number_left = (random.randrange(400, 1000, 1)/10)
        random_number_right = (random.randrange(400, 1000, 1)/10)
        power = calculate_pid(45, 33, "P")
        create_file(power[0], power[1], 50)
        print("Power Left", power[0])
        print("Power Right", power[1])
        value = value + 1
    # create_graphic()
    # power = calculate_pid(10, 10, "PID")
    # print("Power Left", power[0])
    # print("Power Right", power[1])
    # os.remove("offset.txt")


def main():
    test_no_robot()
    # rs=RunningStats()
    #
    # print(rs.mean())
    # print(rs.variance())
    # print(rs.standard_deviation())


main()
