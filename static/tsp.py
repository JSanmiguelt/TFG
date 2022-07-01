#!/usr/bin/env python3
# Copyright 2010-2021 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# [START program]
"""Simple Travelling Salesperson Problem (TSP) between cities."""

# [START import]
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
# [END import]

class TSP:
    def __init__(self):
        self.data = None
        self.manager = None
        self.routing = None
        self.objectiveValue = None
    
    # [START data_model]
    def create_data_model(self, distance_matrix):
        """Stores the data for the problem."""
        data = {}
        data['distance_matrix'] = distance_matrix
        data['num_vehicles'] = 1
        data['depot'] = 0
        return data
        # [END data_model]


    # [START solution_printer]
    def print_solution(self, solution):
        """Prints solution on console."""
        print('Objective: {} meters'.format(solution.ObjectiveValue()))
        index = self.routing.Start(0)
        plan_output = 'Route:\n'
        route_distance = 0
        while not self.routing.IsEnd(index):
            plan_output += ' {} ->'.format(self.manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(self.routing.NextVar(index))
            route_distance += self.routing.GetArcCostForVehicle(previous_index, index, 0)
        plan_output += ' {}\n'.format(self.manager.IndexToNode(index))
        print(plan_output)
        plan_output += 'Route distance: {}meters\n'.format(route_distance)
        # [END solution_printer]

    # [START transit_callback]
    def distance_callback(self, from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = self.manager.IndexToNode(from_index)
        to_node = self.manager.IndexToNode(to_index)
        return self.data['distance_matrix'][from_node][to_node]


    def get_routes(self, solution):
        """Get vehicle routes from a solution and store them in an array."""
        # Get vehicle routes and store them in a two dimensional array whose
        # i,j entry is the jth location visited by vehicle i along its route.
        routes = []
        for route_nbr in range(self.routing.vehicles()):
            index = self.routing.Start(route_nbr)
            route = [self.manager.IndexToNode(index)]
            while not self.routing.IsEnd(index):
                index = solution.Value(self.routing.NextVar(index))
                route.append(self.manager.IndexToNode(index))
            routes.append(route)
        return routes


    def TSP_solver(self):
        transit_callback_index = self.routing.RegisterTransitCallback(self.distance_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        solution = self.routing.SolveWithParameters(search_parameters)

        if solution:
            self.objectiveValue = solution.ObjectiveValue()
            self.print_solution(solution)
            return self.get_routes(solution)
