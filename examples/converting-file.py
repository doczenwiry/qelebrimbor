from qelebrimbor.volumetric_zx_graph import VolumetricZxGraph

if __name__ == "__main__":
    vzx = VolumetricZxGraph.from_file("../assets/vzx/ghz8-alternative.vzx")

    vzx.print_summary()

    vzx.into_file("../assets/vzx/ghz8-alternative-bis.vzx")