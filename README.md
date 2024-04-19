Générateur de grille hexagonale
Ce programme vous permet de générer une grille hexagonale personnalisée en utilisant différentes dimensions et paramètres.

Fonctionnalités
Paramètres personnalisables : Vous pouvez spécifier la taille des hexagones, leur hauteur, l'espacement entre eux, la largeur et la hauteur de la surface.
Génération de grille en STL : Une fois les paramètres définis, vous pouvez générer une grille hexagonale au format STL.
Renommage des fichiers STL : Après la génération, vous pouvez renommer le fichier STL avec les paramètres utilisés dans le nom du fichier.
Prérequis
Python 3.x
PyQt5
numpy
numpy-stl
Installation
Clonez ce dépôt sur votre machine locale :
bash
Copy code
git clone https://github.com/julien-lafargue/honeycomb-stl-pattern.git
Installez les dépendances requises en exécutant la commande suivante :
bash
Copy code
pip install -r requirements.txt
Utilisation
Exécutez le programme en utilisant la commande suivante :
bash
Copy code
python main.py
Spécifiez les paramètres de la grille hexagonale dans l'interface utilisateur.
Cliquez sur le bouton "Save STL" pour générer la grille.
Une fois la génération terminée, un bouton "Rename File" apparaîtra. Cliquez dessus pour renommer le fichier STL avec les paramètres utilisés.



Licence
Ce projet est sous licence MIT. Consultez le fichier LICENSE pour plus d'informations.

