import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer
import numpy as np
from stl import mesh
import math
import os
import shutil

class HexagonalGridGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Générateur de grille hexagonale")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        form_layout = QFormLayout()

        self.init_parameters(form_layout)
        main_layout.addLayout(form_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)
        self.progress_bar.setHidden(True)

        self.rename_button = QPushButton("Rename File")
        self.rename_button.setFont(QFont("Segoe UI", 12))
        self.rename_button.setHidden(True)
        self.rename_button.clicked.connect(self.rename_stl_file)
        main_layout.addWidget(self.rename_button)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_progress_bar)

    def init_parameters(self, layout):
        font = QFont("Segoe UI", 12)

        label_size = QLabel("Taille des hexagones (mm):")
        label_size.setFont(font)

        self.size_entry = QLineEdit("1.0")
        self.size_entry.setFont(font)

        label_height = QLabel("Hauteur des hexagones (mm):")
        label_height.setFont(font)

        self.height_entry = QLineEdit("1.0")
        self.height_entry.setFont(font)

        label_spacing = QLabel("Espacement entre les hexagones (mm):")
        label_spacing.setFont(font)

        self.spacing_entry = QLineEdit("0.25")
        self.spacing_entry.setFont(font)

        label_width = QLabel("Largeur de la surface (mm):")
        label_width.setFont(font)

        self.surface_width_entry = QLineEdit("10.0")
        self.surface_width_entry.setFont(font)

        label_surface_height = QLabel("Hauteur de la surface (mm):")
        label_surface_height.setFont(font)

        self.surface_height_entry = QLineEdit("10.0")
        self.surface_height_entry.setFont(font)

        self.generate_button = QPushButton("Save STL")
        self.generate_button.setFont(font)
        self.generate_button.clicked.connect(self.generate_honeycomb_grid)

        layout.addRow(label_size, self.size_entry)
        layout.addRow(label_height, self.height_entry)
        layout.addRow(label_spacing, self.spacing_entry)
        layout.addRow(label_width, self.surface_width_entry)
        layout.addRow(label_surface_height, self.surface_height_entry)
        layout.addRow(self.generate_button)

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

        hexagon = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            hexagon.vectors[i] = vertices[f]

        return hexagon

    def generate_honeycomb_grid(self):

        self.progress_bar.setHidden(False)


        self.generate_button.setEnabled(False)

        size = float(self.size_entry.text())
        height = float(self.height_entry.text())
        spacing = float(self.spacing_entry.text())
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

        combined_hexagons = mesh.Mesh(np.concatenate([h.data for h in all_hexagons]))
        self.stl_file_name = os.path.abspath('hexagonal_honeycomb_grid_with_spacing.stl')
        combined_hexagons.save(self.stl_file_name)


        self.timer.start(500)

    def hide_progress_bar(self):
        self.progress_bar.setHidden(True)
        self.generate_button.setEnabled(True)
        self.rename_button.setHidden(False)
        self.rename_button.setStyleSheet("background-color: #353535; color: #ffffff; border: none; padding: 8px 16px; border-radius: 5px;")
        self.rename_button.setCursor(Qt.PointingHandCursor)

    def rename_stl_file(self):
        surface_width = self.surface_width_entry.text()
        surface_height = self.surface_height_entry.text()
        size = self.size_entry.text()
        height = self.height_entry.text()
        spacing = self.spacing_entry.text()
        new_stl_file_name = os.path.join(os.path.dirname(self.stl_file_name),
                                         f"honeycomb_grid_surface_{surface_width}x{surface_height}_size_{size}_height_{height}_spacing_{spacing}_hex_size_{size}.stl")
        shutil.move(self.stl_file_name, new_stl_file_name)
        self.rename_button.setHidden(True)


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

    window = HexagonalGridGenerator()
    window.show()
    sys.exit(app.exec_())
