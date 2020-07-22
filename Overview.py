#! /usr/bin/env python3

'''Car Requirements:
1. Must be as fast as the winning car on a track
2. Must go as long between refueling as winning car on a track 
3. Simulation must output:
  a. Energy capacity of battery
  b. Motor power
  c. laps per battery swap
  d. characteristics used for simulation

'''

''' Assumptions
- Drag and inertia are the major forces acting on car, other forces are negligible
- ideal and constant motor characteristics (output power doesn't vary with charge % of battery, etc)
- ideal and constant battery characteristics (efficieny doesn't depend on output current)

'''

'''Simulation Architecture
Main simulation file has no hard coded properties
- Properties file for:
  - Track/winning car
  - Electric car
  - physics
- Main simulation file accepts properties and outputs required outputs on command line

'''

''' Simulation process
1. Define track of interest
2. Define winning car characteristics (lap time and refuel interval)
3. Define velocity profile for lap time
4. Define electric car properties (weight, energy capacity, inertia)
5. Calculate lap output of electric car
6. Iterate 4 and 5

'''

