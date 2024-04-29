import sys
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QComboBox
from PyQt5.QtGui import QFont, QColor, QPalette
from pyqtgraph.Qt import QtCore
import numpy as np
from stl import mesh as stlmesh
import os
import shutil
import pyqtgraph.opengl as gl
from shapes import Hexagon, Circle, Square, KochSnowflake

class ShapeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Générateur de formes")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        self.shape_selector = QComboBox()
        self.shape_selector.addItems(["Hexagone", "Rond", "Carré", "Flocon de Koch"])
        self.shape_selector.currentIndexChanged.connect(self.update_parameters_form)
        main_layout.addWidget(self.shape_selector)
        self.form_layout = QFormLayout()
        main_layout.addLayout(self.form_layout)
        self.init_parameters()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setHidden(True)
        main_layout.addWidget(self.progress_bar)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_progress_bar)
        self.visualizer_widget = gl.GLViewWidget()
        self.visualizer_widget.opts['distance'] = 100  # Réglez la distance de vue si nécessaire
        self.visualizer_widget.setBackgroundColor(53, 53, 53, 53)
        main_layout.addWidget(self.visualizer_widget)
        self.rename_button = QPushButton("Save File")
        self.rename_button.setFont(QFont("Segoe UI", 12))
        self.rename_button.setHidden(True)
        self.rename_button.clicked.connect(self.rename_stl_file)
        main_layout.addWidget(self.rename_button)

    def init_parameters(self):
        self.update_parameters_form()

    def update_parameters_form(self):
        shape = self.shape_selector.currentText()
        self.form_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        self.form_layout.setVerticalSpacing(10)
        self.form_layout.setHorizontalSpacing(10)
        while self.form_layout.count():
            child = self.form_layout.takeAt(0).widget()
            if child is not None:
                child.deleteLater()
        if shape == "Hexagone":
            self.hex_size_entry = self.add_parameter("Taille des hexagones (mm):", "1.0")
            self.hex_height_entry = self.add_parameter("Hauteur des hexagones (mm):", "1.0")
            self.hex_spacing_entry = self.add_parameter("Espacement entre les hexagones (mm):", "0.25")
        elif shape == "Rond":
            self.round_radius_entry = self.add_parameter("Rayon du cercle (mm):", "1.0")
            self.round_spacing_entry = self.add_parameter("Espacement entre les ronds (mm):", "1.0")
        elif shape == "Flocon de Koch":
            # Ajoutez les paramètres spécifiques au flocon de Koch
            self.koch_side_length_entry = self.add_parameter("Longueur du côté du triangle (mm):", "1.0")
            self.koch_iterations_entry = self.add_parameter("Nombre d'itérations:", "3")
        elif shape == "Carré":
            self.square_side_length_entry = self.add_parameter("Longueur du côté du carré (mm):", "1.0")
            self.square_height_entry = self.add_parameter("Hauteur du carré (mm):", "1.0")
            self.square_spacing_entry = self.add_parameter("Espacement entre les carrés (mm):", "0.25")
        self.surface_width_entry = self.add_parameter("Largeur de la surface (mm):", "10.0")
        self.surface_height_entry = self.add_parameter("Hauteur de la surface (mm):", "10.0")
        self.generate_button = QPushButton("Preview STL")
        self.generate_button.setFont(QFont("Segoe UI", 12))
        self.generate_button.clicked.connect(self.generate_shape)
        self.form_layout.addRow(self.generate_button)

    def add_parameter(self, label_text, default_value):
        font = QFont("Segoe UI", 12)
        label = QLabel(label_text)
        label.setFont(font)
        entry = QLineEdit(default_value)
        entry.setFont(font)
        self.form_layout.addRow(label, entry)
        return entry

    def generate_shape(self):
        self.clear_visualizer()
        shape = self.shape_selector.currentText()
        if shape == "Hexagone":
            self.generate_honeycomb_grid("hexagon.stl")
        elif shape == "Rond":
            self.generate_round_shape("rond.stl")
        elif shape == "Carré":
            self.generate_square("carre.stl")
        elif shape == "Flocon de Koch":
            self.generate_koch_snowflake("koch_snowflake.stl")

    def clear_visualizer(self):
        self.visualizer_widget.clear()

    def generate_honeycomb_grid(self, filename):
        self.progress_bar.setHidden(False)
        self.generate_button.setEnabled(False)

        size = float(self.hex_size_entry.text())
        height = float(self.hex_height_entry.text())
        spacing = float(self.hex_spacing_entry.text())
        surface_width_mm = float(self.surface_width_entry.text())
        surface_height_mm = float(self.surface_height_entry.text())
        surface_width = int(surface_width_mm / (math.sqrt(3) * size + spacing))
        surface_height = int(surface_height_mm / (1.5 * size + spacing))

        horiz = math.sqrt(3) * size + spacing
        vert = 1.5 * size + spacing

        all_hexagons = []
        total_hexagons = surface_height * surface_width
        progress_step = 100 / total_hexagons
        current_progress = 0

        for i in range(surface_height):
            for j in range(surface_width):
                if j * horiz >= surface_width_mm or i * vert >= surface_height_mm:
                    break
                x = j * horiz + (i % 2) * (horiz / 2)
                y = i * vert
                hexagon = self.create_hexagon(size, height)

                rotation_angle = 0
                if i % 2 == 0:
                    rotation_angle = 30 if j % 2 == 0 else -30
                else:
                    rotation_angle = 30 if j % 2 != 0 else -30

                hexagon.rotate([0, 0, 1], math.radians(rotation_angle))
                hexagon.translate([x, y, 0])
                all_hexagons.append(hexagon)

                current_progress += progress_step
                self.progress_bar.setValue(int(current_progress))

        combined_hexagons = stlmesh.Mesh(np.concatenate([h.data for h in all_hexagons]))
        stl_file_name = os.path.abspath(filename)
        combined_hexagons.save(stl_file_name)

        self.timer.start(500)
        self.visualize_stl(stl_file_name)
    def generate_round_shape(self, filename):
        self.progress_bar.setHidden(False)
        self.generate_button.setEnabled(False)
        radius = float(self.round_radius_entry.text())
        spacing = float(self.round_spacing_entry.text())
        surface_width_mm = float(self.surface_width_entry.text())
        surface_height_mm = float(self.surface_height_entry.text())
        num_circles = int(surface_width_mm / (2 * radius + spacing))
        num_vertical_circles = int(surface_height_mm / (2 * radius + spacing))
        all_circles = []
        total_circles = num_circles * num_vertical_circles
        progress_step = 100 / total_circles
        current_progress = 0
        for i in range(num_vertical_circles):
            center_y = radius + i * (2 * radius + spacing)
            for j in range(num_circles):
                center_x = radius + j * (2 * radius + spacing)
                circle = self.create_circle(radius, 30, center_x, center_y)
                all_circles.append(circle)
                current_progress += progress_step
                self.progress_bar.setValue(int(current_progress))
        combined_circles = stlmesh.Mesh(np.concatenate([c.data for c in all_circles]))
        stl_file_name = os.path.abspath(filename)
        combined_circles.save(stl_file_name)
        self.timer.start(500)
        self.visualize_stl(stl_file_name)

    def generate_koch_snowflake(self, filename):
        # Récupérez les paramètres du formulaire
        side_length = float(self.koch_side_length_entry.text())
        iterations = int(self.koch_iterations_entry.text())
        surface_width_mm = float(self.surface_width_entry.text())
        surface_height_mm = float(self.surface_height_entry.text())

        # Divisez la surface en régions plus petites
        region_width = side_length * 3  # Largeur d'une région
        region_height = side_length * np.sqrt(3)  # Hauteur d'une région
        num_regions_x = int(surface_width_mm / region_width)
        num_regions_y = int(surface_height_mm / region_height)

        # Générez un flocon de Koch sur chaque région
        all_meshes = []
        for y in range(num_regions_y):
            for x in range(num_regions_x):
                # Calculez les coordonnées de départ de la région
                region_x = x * region_width
                region_y = y * region_height

                # Génère le flocon de Koch pour cette région
                koch_snowflake = KochSnowflake({'side_length': side_length, 'iterations': iterations})
                mesh = koch_snowflake.generate_mesh()

                # Déplace le maillage pour qu'il corresponde à la région actuelle
                mesh.x += region_x
                mesh.y += region_y

                # Ajoute le maillage à la liste des maillages
                all_meshes.append(mesh)

        # Combinez tous les maillages en un seul maillage
        combined_mesh = stlmesh.Mesh(np.concatenate([m.data for m in all_meshes]))

        # Enregistrez le maillage dans un fichier STL
        stl_file_name = os.path.abspath(filename)
        combined_mesh.save(stl_file_name)

        # Affichez le maillage dans le visualiseur
        self.timer.start(500)
        self.visualize_stl(stl_file_name)

    def generate_square(self, filename):
        side_length = float(self.square_side_length_entry.text())
        height = float(self.square_height_entry.text())
        spacing = float(self.square_spacing_entry.text())
        surface_width_mm = float(self.surface_width_entry.text())
        surface_height_mm = float(self.surface_height_entry.text())

        parameters = {
            'side_length': side_length,
            'height': height,
            'spacing': spacing,
            'width': surface_width_mm,
            'height_dimension': surface_height_mm
        }
        square = Square(parameters)
        mesh = square.generate_mesh()
        stl_file_name = os.path.abspath(filename)
        mesh.save(stl_file_name)

        self.timer.start(500)
        self.visualize_stl(stl_file_name)

    def create_hexagon(self, edge_length, height):
        angle_deg = 60
        points_2d = [(math.cos(math.radians(angle * angle_deg)), math.sin(math.radians(angle * angle_deg)))
                     for angle in range(6)]

        vertices = np.zeros((12, 3))
        for i in range(6):
            vertices[i, :2] = [p * edge_length for p in points_2d[i]]
            vertices[i + 6] = [vertices[i, 0], vertices[i, 1], height]

        faces = []
        for i in range(6):
            faces.append([i, (i + 1) % 6, i + 6])
            faces.append([(i + 1) % 6, (i + 1) % 6 + 6, i + 6])
        for i in range(1, 5):
            faces.append([0, i, i + 1])
            faces.append([6, i + 6, i + 1 + 6])

        hexagon = stlmesh.Mesh(np.zeros(len(faces), dtype=stlmesh.Mesh.dtype))
        for i, f in enumerate(faces):
            hexagon.vectors[i] = vertices[f]

        return hexagon

    def create_circle(self, radius, num_points, center_x, center_y):
        theta = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        x = center_x + radius * np.cos(theta)
        y = center_y + radius * np.sin(theta)
        vertices_base = np.zeros((num_points + 1, 3))
        vertices_base[0, :] = [center_x, center_y, 0]
        vertices_base[1:, 0] = x
        vertices_base[1:, 1] = y
        vertices_top = np.zeros_like(vertices_base)
        vertices_top[:, :2] = vertices_base[:, :2]
        vertices_top[:, 2] = 1.0
        vertices = np.vstack([vertices_base, vertices_top])
        faces_base = [[0, i, (i % num_points) + 1] for i in range(1, num_points + 1)]
        faces_top = [[num_points + 1, num_points + i + 1, num_points + (i % num_points) + 2] for i in range(1, num_points + 1)]
        faces_side = []
        for i in range(1, num_points + 1):
            next_index = (i % num_points) + 1
            faces_side.append([i, next_index, num_points + next_index])
            faces_side.append([num_points + next_index, num_points + i, i])
        all_faces = faces_base + faces_top + faces_side
        circle_mesh = stlmesh.Mesh(np.zeros(len(all_faces), dtype=stlmesh.Mesh.dtype))
        for i, f in enumerate(all_faces):
            circle_mesh.vectors[i] = vertices[f]
        return circle_mesh

    def hide_progress_bar(self):
        self.progress_bar.setHidden(True)
        self.generate_button.setEnabled(True)
        self.rename_button.setHidden(False)

    def rename_stl_file(self):
        surface_width = self.form_layout.itemAt(6).widget().text()
        surface_height = self.form_layout.itemAt(8).widget().text()
        size = self.form_layout.itemAt(0).widget().text()
        height = self.form_layout.itemAt(2).widget().text()
        spacing = self.form_layout.itemAt(4).widget().text()
        stl_file_name = self.shape_selector.currentText().lower() + ".stl"
        new_stl_file_name = os.path.join(os.path.dirname(stl_file_name), f"honeycomb_grid_surface_{surface_width}x{surface_height}_size_{size}_height_{height}_spacing_{spacing}_hex_size_{size}.stl")
        shutil.move(stl_file_name, new_stl_file_name)
        self.rename_button.setHidden(True)

    def visualize_stl(self, stl_file):
        mesh = stlmesh.Mesh.from_file(stl_file)
        vertices = mesh.vectors.reshape(-1, 3)
        faces = np.arange(len(vertices)).reshape(-1, 3)
        self.visualizer_widget.addItem(gl.GLMeshItem(vertexes=vertices, faces=faces, smooth=True, color=(0, 0, 1, 1)))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    window = ShapeGenerator()
    window.show()
    sys.exit(app.exec_())
