from qelebrimbor.helpers.octahedron import OctahedronHelper

if __name__ == "__main__":
    hemi_octahedron = OctahedronHelper.get_hemi_positions(2, upper = True)
    print(hemi_octahedron)