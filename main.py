#!/usr/bin/python3
from modules.CreateScenario import Scenario
from modules.CoveragePathPlanner import CoveragePathPlanner

def main():
    scenario = Scenario()
    planner = CoveragePathPlanner(scenario.map1)
    x, y = planner.plan()
    scenario.draw_map(scenario.map1, x, y)

if __name__ =="__main__":
    try:
        main()
    except Exception as e:
        print(e)