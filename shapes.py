import numpy as np
import math
from stl import mesh as stlmesh
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

def create_hexagon(size, height):
    angle_deg = 60
    angles = np.radians(np.arange(0, 360, angle_deg))
    points = np.stack((np.cos(angles), np.sin(angles)), axis=-1) * size
    vertices = np.vstack((points, points + [0, 0, height]))
    faces = [[i, (i + 1) % 6, i + 6] for i in range(6)] + \
            [[(i + 1) % 6, (i + 1) % 6 + 6, i + 6] for i in range(6)]
    return vertices, np.array(faces)

def create_circle(radius, height, num_points):
    theta = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    points = np.stack((np.cos(theta), np.sin(theta)), axis=-1) * radius
    vertices = np.vstack((points, points + [0, 0, height]))
    faces = [[i, (i + 1) % num_points, num_points + (i + 1) % num_points, num_points + i] for i in range(num_points)]
    return vertices, np.array(faces)

def mesh_worker(params):
    shape, x_offset, y_offset = params
    try:
        return shape.generate_mesh(), x_offset, y_offset
    except Exception as e:
        return None, x_offset, y_offset

class Hexagon:
    def __init__(self, parameters):
        self.parameters = parameters

    def generate_mesh(self):
        horiz = math.sqrt(3) * self.parameters['size'] + self.parameters['spacing']
        vert = 1.5 * self.parameters['size'] + self.parameters['spacing']
        num_x = self.parameters['width'] // horiz
        num_y = self.parameters['height_dimension'] // vert

        with ProcessPoolExecutor(max_workers=max(1, cpu_count() // 2)) as executor:
            mesh_data = []
            batch_size = 10  # Nombre de tâches à créer et exécuter à la fois
            for y in range(0, num_y, batch_size):
                for x in range(0, num_x, batch_size):
                    tasks = []
                    for j in range(batch_size):
                        for i in range(batch_size):
                            if y + j < num_y and x + i < num_x:
                                tasks.append((self, (x + i) * horiz + ((y + j) % 2) * (horiz / 2), (y + j) * vert))
                    mesh_data.extend(executor.map(mesh_worker, tasks))

        return stlmesh.Mesh(np.concatenate([data[0] for data in mesh_data if data[0] is not None]),
                            remove_empty_areas=False)


class Circle:
    def __init__(self, parameters):
        self.parameters = parameters

    def generate_mesh(self):
        num_points = 30
        vertices, faces = create_circle(self.parameters['radius'], self.parameters['height'], num_points)
        mesh_data = np.zeros(len(faces), dtype=stlmesh.Mesh.dtype)
        for i, face in enumerate(faces):
            mesh_data['vectors'][i] = vertices[face]
        return stlmesh.Mesh(mesh_data, remove_empty_areas=False)

class Square:
    def __init__(self, parameters):
        self.parameters = parameters

    def generate_mesh(self):
        side_length = self.parameters['side_length']
        height = self.parameters['height']
        spacing = self.parameters['spacing']
        width = self.parameters['width']
        height_dimension = self.parameters['height_dimension']

        num_x = int(width // (side_length + spacing))
        num_y = int(height_dimension // (side_length + spacing))

        vertices = []
        faces = []

        for y in range(num_y):
            for x in range(num_x):
                # Calculate vertex coordinates
                x_offset = x * (side_length + spacing)
                y_offset = y * (side_length + spacing)
                z_offset = 0  # Assuming the square is on the XY plane
                vertices.extend([
                    [x_offset, y_offset, z_offset],
                    [x_offset + side_length, y_offset, z_offset],
                    [x_offset + side_length, y_offset + side_length, z_offset],
                    [x_offset, y_offset + side_length, z_offset]
                ])

                # Calculate face indices
                base_index = (y * num_x + x) * 4
                faces.extend([
                    [base_index, base_index + 1, base_index + 2],
                    [base_index, base_index + 2, base_index + 3]
                ])

        # Convert vertices and faces to numpy arrays
        vertices = np.array(vertices)
        faces = np.array(faces)

        # Create the mesh
        mesh_data = np.zeros(len(faces), dtype=stlmesh.Mesh.dtype)
        for i, face in enumerate(faces):
            mesh_data['vectors'][i] = vertices[face]

        return stlmesh.Mesh(mesh_data, remove_empty_areas=False)
class KochSnowflake:
    def __init__(self, parameters):
        self.parameters = parameters

    def generate_mesh(self):
        side_length = self.parameters['side_length']
        iterations = self.parameters['iterations']

        # Coordonnées des sommets du triangle équilatéral initial
        vertices = np.array([
            [0, np.sqrt(3) * side_length / 3, 0],   # Sommet inférieur
            [-side_length / 2, 0, 0],                # Sommet inférieur gauche
            [side_length / 2, 0, 0]                  # Sommet inférieur droit
        ])

        # Génère le flocon de Koch itérativement
        for _ in range(iterations):
            new_vertices = []
            for i in range(len(vertices)):
                # Points de départ et d'arrivée du segment actuel
                start_point = vertices[i]
                end_point = vertices[(i + 1) % len(vertices)]

                # Calcule les deux tiers du segment
                p1 = start_point + (end_point - start_point) / 3
                p2 = start_point + 2 * (end_point - start_point) / 3

                # Calcule les coordonnées des sommets des triangles équilatéraux sortants
                outward_point1 = p1 + np.dot(p2 - p1, np.array([[0, -1], [1, 0]])) / np.sqrt(3)
                outward_point2 = p2 + np.dot(p1 - p2, np.array([[0, 1], [-1, 0]])) / np.sqrt(3)

                # Construit les nouveaux segments du flocon
                new_vertices.extend([start_point, p1, outward_point1])
                new_vertices.extend([outward_point1, p2, outward_point2])
                new_vertices.extend([outward_point2, end_point, start_point])

            vertices = np.array(new_vertices)

        # Construction des faces du flocon
        faces = []
        for i in range(0, len(vertices) - 2, 3):
            faces.append([i, i + 1, i + 2])

        # Création du maillage STL
        mesh_data = np.zeros(len(faces), dtype=stlmesh.Mesh.dtype)
        for i, face in enumerate(faces):
            mesh_data['vectors'][i] = vertices[face]

        return stlmesh.Mesh(mesh_data, remove_empty_areas=False)
