import heapq
from math import sqrt
from concurrent.futures import ThreadPoolExecutor

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def distance_to(self, other):
        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

class VRP:
    def __init__(self, points, num_vehicles, vehicle_capacity):
        self.points = points
        self.num_vehicles = num_vehicles
        self.vehicle_capacity = vehicle_capacity
        self.depot = points[0]
        self.distance_dict = self._compute_distances()
        self.routes = [[] for _ in range(num_vehicles)]

    def _compute_distances(self):
        """Precompute distances between all pairs of points in a dictionary."""
        distances = {}
        for i, point1 in enumerate(self.points):
            for j, point2 in enumerate(self.points):
                if j >= i:
                    distance = point1.distance_to(point2)
                    distances[(point1, point2)] = distance
                    distances[(point2, point1)] = distance  # Add reverse pair
        return distances

    def get_distance(self, point1, point2):
        """Retrieve distance between two points from the dictionary."""
        if (point1, point2) in self.distance_dict:
            return self.distance_dict[(point1, point2)]
        elif (point2, point1) in self.distance_dict:
            return self.distance_dict[(point2, point1)]
        else:
            raise KeyError(f"Distance not found for points {point1} and {point2}")

    def greedy_vrp(self):
        """Optimized VRP using only the closest point, no lookahead."""
        visited = [False] * len(self.points)  # Track visited status with a list
        vehicle_loads = [0] * self.num_vehicles

        # Mark the depot as visited initially
        visited[self.points.index(self.depot)] = True

        for vehicle in range(self.num_vehicles):
            current_location = self.depot
            self.routes[vehicle].append(current_location)

            # Continue adding points to the vehicle's route until full capacity
            while vehicle_loads[vehicle] < self.vehicle_capacity:
                nearest_point = None
                nearest_distance = float('inf')

                # Step 1: Get the closest point
                unvisited_indices = [i for i, v in enumerate(visited) if not v]

                # Create a heap of unvisited points sorted by distance to `current_location`
                closest_points_heap = [
                    (self.get_distance(current_location, self.points[i]), i) for i in unvisited_indices
                ]
                heapq.heapify(closest_points_heap)

                # Get the closest point from the heap
                if closest_points_heap:
                    nearest_distance, idx1 = heapq.heappop(closest_points_heap)
                    nearest_point = self.points[idx1]

                if nearest_point is None:  # If no valid point was found, break out of the loop
                    break

                # Add the selected point to the route
                self.routes[vehicle].append(nearest_point)
                visited[self.points.index(nearest_point)] = True  # Mark as visited
                vehicle_loads[vehicle] += 1
                current_location = nearest_point

            # Ensure the vehicle is filled to capacity, even if there are fewer than `vehicle_capacity` points left
            remaining_points = [self.points[i] for i in range(len(self.points)) if not visited[i]]
            for point in remaining_points:
                if vehicle_loads[vehicle] < self.vehicle_capacity:
                    self.routes[vehicle].append(point)
                    visited[self.points.index(point)] = True
                    vehicle_loads[vehicle] += 1

            # Return to depot
            self.routes[vehicle].append(self.depot)

    def _apply_2opt(self, vehicle):
        """Apply 2-opt optimization to improve the route."""
        route = self.routes[vehicle]
        for i in range(1, len(route) - 2):  # Ensure at least two points are left for swap
            for j in range(i + 1, len(route) - 1):
                # Swap if it improves the route
                self._two_opt_swap(route, i, j)

    def _two_opt_swap(self, route, i, j):
        """Perform a 2-opt swap: reverse the section of the route between i and j."""
        new_route = route[:i] + route[i:j + 1][::-1] + route[j + 1:]
        if self.calculate_route_distance(new_route) < self.calculate_route_distance(route):
            route[:] = new_route

    def optimize_routes(self):
        """Apply 2-opt optimization in parallel for each vehicle."""
        with ThreadPoolExecutor() as executor:
            executor.map(self._apply_2opt, range(self.num_vehicles))

    def calculate_route_distance(self, route):
        distance = 0
        for i in range(len(route) - 1):
            distance += self.distance_dict[(route[i], route[i + 1])]
        return distance

    def total_distance(self):
        total_distance = 0
        for i, route in enumerate(self.routes):
            route_distance = self.calculate_route_distance(route)
            total_distance += route_distance
        return total_distance

    def print_routes(self):
        total_distance = 0
        for i, route in enumerate(self.routes):
            route_distance = self.calculate_route_distance(route)
            total_distance += route_distance
            print(f"Vehicle {i + 1} Route: {route}")
            print(f"Vehicle {i + 1} Route Distance: {route_distance:.2f}")
        print(f"\nTotal Distance: {total_distance:.2f}")
