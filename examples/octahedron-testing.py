from qelebrimbor.helpers.coordinates import CoordinatesHelper

if __name__ == "__main__":
    hemi_octahedron = CoordinatesHelper.get_hemi_octahedron(2, upper = True)
    print(hemi_octahedron)